from flask import Flask, jsonify, make_response, url_for, request
from flask_restful import Api, Resource, fields
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, jwt_required, fresh_jwt_required, jwt_refresh_token_required, create_access_token, create_refresh_token, get_jwt_identity
from webargs.flaskparser import use_args, parser
from webargs import fields
import datetime
import smtplib
from email.mime.text import MIMEText
from errors import *
from litescale import *
import json
import os
import re
from string import Template

AUTHORIZED = 'authorized'
OWNER = 'owner'

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 't1NP63m4wnBg6nyHYKfmc2TpCOGI4nss'
api = Api(app, errors=errors)
jwt = JWTManager(app)


# ---------------------------------------LOGIN RESOURCE----------------------------------------------- #

class LoginAPI(Resource):
    def __init__(self):
        super(LoginAPI, self).__init__()

    user_args = {
        "email": fields.Str(required=True),
        "password": fields.Str(required=True)
    }

    @use_args(user_args, location="json")
    def post(self, args):
        email = args['email']
        password = args['password']

        rst, user = search_user(email)

        if not rst:
            raise UnauthorizedError

        if not check_password_hash(user[0][1], password): 
            raise UnauthorizedError

        expires = datetime.timedelta(minutes=60)
        token = {'AccessToken': create_access_token(identity=email, expires_delta=expires, fresh=True),
                 'RefreshToken': create_refresh_token(identity=email)}
        return jsonify(token)

# ---------------------------------------------------------------------------------------------------- #


# ---------------------------------------REFRESH TOKEN RESOURCE--------------------------------------- #

class RefreshTokenAPI(Resource):
    def __init__(self):
        super(RefreshTokenAPI, self).__init__()
        
    @jwt_refresh_token_required
    def post(self):
        email = get_jwt_identity()
        expires = datetime.timedelta(minutes=60)
        token = {'AccessToken': create_access_token(identity=email, expires_delta=expires, fresh=False)}
        return jsonify(token)
    
# ---------------------------------------------------------------------------------------------------- #


# ----------------------------------------USERS RESOURCE---------------------------------------------- #

class UsersAPI(Resource):
    def __init__(self):
        super(UsersAPI, self).__init__()

    user_args = {
        "email": fields.Str(required=True),
        "password": fields.Str(required=True)
    }

    # Insert a new user
    @use_args(user_args, location="json")
    def post(self, args):
        email = args['email']
        password = args['password']
        
        regex = "^.+@(\[?)[a-zA-Z0-9-.]+.([a-zA-Z]{2,3}|[0-9]{1,3})(]?)$"
        pat = re.compile(regex)
        if not re.search(pat,email): 
            raise InvalidEmailError

        regex = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d@$!#%*?&]{6,20}$"
        pat = re.compile(regex)
        if not re.search(pat,password): 
            raise InvalidPasswordError
    
        password = generate_password_hash(password)

        result, msg = insert_user(email, password)
        if not result:
            raise EmailAlreadyExistsError

        with open('templates/welcome.html', 'r') as f:
            body = f.read()
         
        body = Template(body).safe_substitute(user=email)
        
        mail = {
        'from' : 'ciaociao.d@virgilio.it',
        'object' : 'LITESCALE - CONFIRM REGISTRATION',
        'message' : body 
        }
        
        # Connect to server
        server = smtplib.SMTP_SSL('out.virgilio.it', 465)
        # Login
        server.login(mail['from'], "6$ki7M!n8y3a2zc")
        # Send mail
        msg = MIMEText(mail['message'], 'html', 'utf-8')
        msg['Subject'] = mail['object']
        msg['From'] = mail['from']
        msg['To'] = email 
        server.sendmail(mail['from'], email, msg.as_string())
        
        return {"result" : "True"}

    # Delete user
    @fresh_jwt_required
    def delete(self):
        email = get_jwt_identity()

        rst, msg = delete_user(email)

        if not rst:
            raise ResourceNotFoundError

        return {"result": "True"}

# ---------------------------------------------------------------------------------------------------- #


# -----------------------------------PROJECT LIST RESOURCE-------------------------------------------- #

class ProjectListAPI(Resource):
    def __init__(self):
        super(ProjectListAPI, self).__init__()

    # Return project list

    @jwt_required
    @use_args({"type": fields.Str(required=True)}, location="query") # authorized or owner
    def get(self, args):
        email = get_jwt_identity()
        typeList = args['type']

        if (typeList != AUTHORIZED and typeList != OWNER):
            raise InvalidTypeListError

        if typeList == AUTHORIZED:
            project_list = all_project_list(email)
        else:
            project_list = own_project_list(email)

        if project_list == []:
            return {"Error": "There are no projects"}

        project_list = json.dumps([{"projectId": project[0],
                                    "projectName": project[1],
                                    "projectOwner": project[2],
                                    "phenomenon": project[3],
                                    "tuplesize": project[4],
                                    "replicate": project[5],
                                    "Location": url_for('project', id=project[0], _external=True)}
                                   for project in project_list])

        project_list_json = json.loads(project_list)

        return project_list_json


# ---------------------------------------------------------------------------------------------------- #


# -----------------------------------PROJECTS RESOURCE------------------------------------------------ #

class ProjectsAPI(Resource):
    def __init__(self):
        super(ProjectsAPI, self).__init__()

    # Return project info
    @jwt_required
    @use_args({"project_id": fields.Int(required=True)}, location="query")
    def get(self, args):
        email = get_jwt_identity()
        project_id = args['project_id']

        rst, project_dict = get_project(project_id)

        if not rst:
            raise ResourceNotFoundError

        rst, msg = check_authorization(project_id, email)

        if not rst:
            raise UnauthorizedProjectError

        return project_dict

    # Delete project
    @fresh_jwt_required
    @use_args({"project_id": fields.Int(required=True)}, location="query")
    def delete(self, args):
        email = get_jwt_identity()
        project_id = args['project_id']

        rst, msg = check_owner(project_id, email)

        if not rst:
            raise UnauthorizedProjectError

        rst, msg = delete_project(project_id)

        if not rst:
            raise ResourceNotFoundError

        return {"result": "True"}

    
    # Create a new project
    @fresh_jwt_required
    def post(self):  
        email = get_jwt_identity()
    
        if not request.files or not request.form:
           raise MissingProjectInfoError
            
        if not request.files['file']:
            raise MissingProjectInfoError
            
        if not request.form['json']:
            raise MissingProjectInfoError
            
        info = json.loads((request.form['json']))
        
        if not 'project_name' in info or not 'tuple_size' in info or not 'phenomenon' in info or not 'replication' in info:
            raise MissingProjectInfoError
        
        instance_file =  request.files['file']
        #file_name, extension = os.path.splitext(instance_file.filename)
    
        #if extension != ".tsv":
        #    raise InvalidFileUploadError
        
        instance_file.save('instance_file.tsv')
        project_name = info['project_name']
        tuple_size = info['tuple_size']
        phenomenon = info['phenomenon']
        replication = info['replication']

        project_id, msg = new_project(
            email,
            project_name,
            phenomenon,
            tuple_size,
            replication,
            'instance_file.tsv'
        )
        
        try:
            os.remove('instance_file.tsv')
        except:
            pass

        if (not project_id):  # project not created
            raise InvalidFileUploadError

        return {"result": "True", "id": project_id}

# ---------------------------------------------------------------------------------------------------- #


# -------------------------------------TUPLE RESOURCE------------------------------------------------- #

class TuplesAPI(Resource):
    def __init__(self):
        super(TuplesAPI, self).__init__()

    # Get next tuple to annotate
    @jwt_required
    @use_args({"project_id": fields.Int(required=True)}, location="query")
    def get(self, args):
        email = get_jwt_identity()
        project_id = args['project_id']

        rst, msg = check_authorization(project_id, email)

        if not rst:
            raise UnauthorizedProjectError

        tup_id, tup = next_tuple(project_id, email)

        if tup is None:
            return {"Error": "No tuple to annotate"}

        return jsonify({'tup_id': tup_id, 'tup': tup})

# ---------------------------------------------------------------------------------------------------- #


# -------------------------------------ANNOTATIONS RESOURCE------------------------------------------- #

class AnnotationsAPI(Resource):
    def __init__(self):
        super(AnnotationsAPI, self).__init__()

    user_args = {
        "project_id": fields.Int(required=True),
        "tup_id": fields.Int(required=True),
        "answer_best": fields.Int(required=True),
        "answer_worst": fields.Int(required=True)
    }

    # Add annotation into db
    @fresh_jwt_required
    @use_args(user_args, location="json")
    def post(self, args):
        email = get_jwt_identity()
        project_id = args['project_id']
        tup_id = args['tup_id']
        answer_best = args['answer_best']
        answer_worst = args['answer_worst']

        rst, msg = check_authorization(project_id, email)

        if not rst:
            raise UnauthorizedProjectError

        x, y = annotate(project_id, email, tup_id, answer_best, answer_worst)
        return jsonify({"Annotations": x, "Tuples": y})

# ---------------------------------------------------------------------------------------------------- #


# --------------------------------------------GOLD RESOURCE------------------------------------------- #

class GoldAPI(Resource):
    def __init__(self):
        super(GoldAPI, self).__init__()

    
    @fresh_jwt_required
    @use_args({"project_id": fields.Int(required=True)}, location="query")
    def get(self, args):
        email = get_jwt_identity()
        project_id = args['project_id']

        rst, msg = check_authorization(project_id, email)

        if not rst:
            raise UnauthorizedProjectError

        rst, file = generate_gold(project_id)

        if not rst:
            raise EmptyAnnotationsError

        response = make_response(file)
        response.headers['content-type'] = 'application/octet-stream'
        return response

# ---------------------------------------------------------------------------------------------------- #


# -------------------------------------PROGRESS RESOURCE---------------------------------------------- #

class ProgressAPI(Resource):
    def __init__(self):
        super(ProgressAPI, self).__init__()

    # Return progress annotation
    @jwt_required
    @use_args({"project_id": fields.Int(required=True)}, location="query")
    def get(self, args):
        email = get_jwt_identity()
        project_id = args['project_id']

        rst, msg = check_authorization(project_id, email)

        if not rst:
            raise UnauthorizedProjectError
        
        done, total = progress(project_id, email)

        if done is None and total is None:
            raise ResourceNotFoundError

        return jsonify({'done': done, 'total': total})

# ---------------------------------------------------------------------------------------------------- #



# -------------------------------------AUTHORIZATION RESOURCE----------------------------------------- #

class AuthorizationAPI(Resource):
    def __init__(self):
        super(AuthorizationAPI, self).__init__()

    user_args = {
        "project_id": fields.Int(required=True),
        "user_to": fields.String(required=True),
    }
    
    # Add authorization
    @fresh_jwt_required
    @use_args(user_args, location="json")
    def post(self, args):
        email = get_jwt_identity()
        project_id = args['project_id']
        user_to = args['user_to']
        
        rst, msg = check_owner(project_id, email)

        if not rst:
            raise UnauthorizedProjectError
            
        rst, msg = get_authorization(project_id, user_to)
        
        if not rst:
            return {'result': 'False'}
        
        with open('templates/auth.html', 'r') as f:
            body = f.read()
         
        body = Template(body).safe_substitute(user=email,user_to=user_to)
        
        mail = {
        'from' : 'ciaociao.d@virgilio.it',
        'object' : 'LITESCALE - NEW PROJECT!',
        'message' : body 
        }
        
        # Connect to server
        server = smtplib.SMTP_SSL('out.virgilio.it', 465)
        # Login
        server.login(mail['from'], "6$ki7M!n8y3a2zc")
        # Send mail
        msg = MIMEText(mail['message'], 'html', 'utf-8')
        msg['Subject'] = mail['object']
        msg['From'] = mail['from']
        msg['To'] = user_to 
        server.sendmail(mail['from'], user_to, msg.as_string())
            
        return {'result': 'True'}
    
    # Remove authorization
    @fresh_jwt_required
    @use_args(user_args, location="json")
    def delete(self, args):
        email = get_jwt_identity()
        project_id = args['project_id']
        user_to = args['user_to']
        
        rst, msg = check_owner(project_id, email)

        if not rst:
            raise UnauthorizedProjectError
            
        if email == user_to:
            return {'result': 'False'}
        
        rst, msg = remove_authorization(project_id, user_to)
        
        if not rst:
            return {'result': 'False'}
         
        return {'result': 'True'}
            
# ---------------------------------------------------------------------------------------------------- #

api.add_resource(LoginAPI, '/litescale/api/login', endpoint='login')
api.add_resource(UsersAPI, '/litescale/api/users', endpoint='users')
api.add_resource(ProjectListAPI, '/litescale/api/projectList',endpoint='projects')
api.add_resource(ProjectsAPI, '/litescale/api/projects', endpoint='project')
api.add_resource(TuplesAPI, '/litescale/api/tuples', endpoint='tuples')
api.add_resource(AnnotationsAPI, '/litescale/api/annotations', endpoint='annotation')
api.add_resource(GoldAPI, '/litescale/api/gold', endpoint='gold')
api.add_resource(ProgressAPI, '/litescale/api/progress', endpoint='progress')
api.add_resource(AuthorizationAPI, '/litescale/api/authorizations', endpoint='authorization')
api.add_resource(RefreshTokenAPI, '/litescale/api/token', endpoint='refresh')


# Function to handle auhtorization errors

@jwt.expired_token_loader
def expired_token_callback(expired_token):
    response = {"message": "Token has expired", "sub_status": 40} # token expired
    abort(401, description=response)
   
@jwt.needs_fresh_token_loader
def needs_fresh_token_callback():
    response = {"message": "Needs a fresh token", "sub_status": 41} #  fresh token expired
    abort(401, description=response)
   
@jwt.invalid_token_loader
def invalid_token_callback():
    response = {"message": "Invalid token", "sub_status": 42} # invalid token
    abort(401, description=response)
      
    
   
if __name__ == '__main__':
    app.run(debug=True)
