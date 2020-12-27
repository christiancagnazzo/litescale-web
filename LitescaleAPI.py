from flask import Flask, jsonify, abort, make_response, url_for, request
from flask_restful import Api, Resource, fields
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from webargs.flaskparser import use_args
from webargs import fields
from litescale import *
import json
import os
import re

AUTHORIZED = 'authorized'
OWNER = 'owner'

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 't1NP63m4wnBg6nyHYKfmc2TpCOGI4nss'
api = Api(app)
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
            abort(404, description="User not found")

        if not check_password_hash(user[0][1], password):  # check password
            abort(401, description="Incorrect email or password")

        token = {'AccessToken': create_access_token(identity=email)}
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
        
        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        if not re.search(regex,email): 
            abort(400, description="Insert a valid email")

        password = generate_password_hash(password)

        result, msg = insert_user(email, password)
        if not result:
            # existing user
            abort(409, description="User already exists")

        token = {'AccessToken': create_access_token(identity=email)}
        return jsonify(token)

    # Delete user
    @jwt_required
    def delete(self):
        email = get_jwt_identity()

        rst, msg = delete_user(email)

        if not rst:
            abort(404, description="User not found")

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
            abort(400, description="Indicate type of list: owner or authorized")

        if typeList == AUTHORIZED:
            project_list = all_project_list(email)
        else:
            project_list = own_project_list(email)

        if project_list == []:
            return {"Error": "There are no projects"}

        project_list = json.dumps([{"projectId": project[0],
                                    "projectName": project[1],
                                    "projectOwner": project[2],
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
            abort(404, description="Project not found")

        rst, msg = check_authorization(project_id, email)

        if not rst:
            abort(401, description=msg)

        return project_dict

    # Delete project
    @jwt_required
    @use_args({"project_id": fields.Int(required=True)}, location="query")
    def delete(self, args):
        email = get_jwt_identity()
        project_id = args['project_id']

        rst, msg = check_owner(project_id, email)

        if not rst:
            abort(401, description=msg)

        rst, msg = delete_project(project_id)

        if not rst:
            abort(404, description="Project not found")

        return {"result": "True"}

    
    # Create a new project
    @jwt_required
    @use_args({"file": fields.Field(required=True)}, location="files")
    def post(self, files):  
        email = get_jwt_identity()
        
        if not request.files or not request.form:
            abort(400, description="Missing instance file or project info")
            
        if not request.files['file']:
            abort(400, description="Missing instance file")
            
        if not request.form['json']:
            abort(400, description="Missing project info")
            
        info = json.loads((request.form['json']))
        
        if not info['project_name'] or not info['tuple_size'] or not info['phenomenon'] or not info['replication']:
                abort(400, description="Missing project info")
        
        instance_file =  request.files['file']
        file_name, extension = os.path.splitext(instance_file.filename)
    
        if extension != ".tsv":
            abort(400, description="Upload a tsv file")
        
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
            abort(400, description=msg)

        return {"result": "True"}

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
            abort(401, description=msg)

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
    @jwt_required
    @use_args(user_args, location="json")
    def post(self, args):
        email = get_jwt_identity()
        project_id = args['project_id']
        tup_id = args['tup_id']
        answer_best = args['answer_best']
        answer_worst = args['answer_worst']

        rst, msg = check_authorization(project_id, email)

        if not rst:
            abort(401, description=msg)

        x, y = annotate(project_id, email, tup_id, answer_best, answer_worst)
        return jsonify({"Annotations": x, "Tuples": y})

# ---------------------------------------------------------------------------------------------------- #


# --------------------------------------------GOLD RESOURCE------------------------------------------- #

class GoldAPI(Resource):
    def __init__(self):
        super(GoldAPI, self).__init__()

    # Add annotation into db
    @jwt_required
    @use_args({"project_id": fields.Int(required=True)}, location="query")
    def get(self, args):
        email = get_jwt_identity()
        project_id = args['project_id']

        rst, msg = check_authorization(project_id, email)

        if not rst:
            abort(401, description=msg)

        rst, file = generate_gold(project_id)

        if not rst:
            abort(404, description=file)

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
            abort(401, description=msg)

        done, total = progress(project_id, email)

        if done is None and total is None:
            abort(404, description="Project not found")

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
    @jwt_required
    @use_args(user_args, location="json")
    def post(self, args):
        email = get_jwt_identity()
        project_id = args['project_id']
        user_to = args['user_to']
        
        rst, msg = check_owner(project_id, email)

        if not rst:
            abort(401, description=msg)
            
        rst, msg = get_authorization(project_id, user_to)
        
        if not rst:
            abort(400, description=msg)
            
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
api.add_resource(AuthorizationAPI, '/litescale/api/auhtorizations', endpoint='authorization')


# STATUS CODE:
# 404 not found
# 401 not authorized
# 422 unprocessable Entity
# 400 bad request
# 409 conflict

# Return validation errors as JSON (when missing input)
@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    abort(400, description="Missing input")


if __name__ == '__main__':
    app.run(debug=True)
