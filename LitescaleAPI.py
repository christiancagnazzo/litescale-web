from flask import Flask, jsonify, abort, make_response, url_for
from flask_restful import Api, Resource, fields
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from webargs.flaskparser import use_args
from webargs import fields
from litescale import *
import json

AUTHORIZED = 'authorized'
OWNER = 'owner'

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 't1NP63m4wnBg6nyHYKfmc2TpCOGI4nss'
api = Api(app)
jwt = JWTManager(app)

# STATUS CODE:
# 404 not found
# 401 not authorized
# 422 unprocessable Entity
# 400 bad request
# 409 conflict

# Return validation errors as JSON
@app.errorhandler(422) 
@app.errorhandler(400) 
def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    if headers:
        return jsonify({"errors": messages}), err.code, headers
    else:
        return jsonify({"errors": messages}), err.code
    
    

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
        
        rst, user = search_user(email);
        
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
            abort(404, description="User not found");
            
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
        typeList = args['typeList']
        
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
                                    "Location": url_for('project',id=project[0],_external = True)} 
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
    @use_args({"id": fields.Int(required=True)}, location="query")
    def get(self, args):
        email = get_jwt_identity()
        project_id = args['id']
        
        rst, project_dict = get_project(project_id)
        
        if not rst:
            abort(404, description="Project not found")
            
        rst, msg = check_authorization(project_id, email)
        
        if not rst:
            abort(401)
        
        return project_dict
    
    # Delete project
    @jwt_required
    @use_args({"id": fields.Int(required=True)}, location="query")
    def delete(self, args):
        email = get_jwt_identity()
        project_id = args['id']
        
        rst, msg = delete_project(project_id) 
        
        if not rst:
            abort(404, description="Project not found")
            
        rst, msg = check_owner(project_id, email)
        
        if not rst:
            abort(401)
        
        return {"result": "True"}
    
    
    user_args = {
        "project_name": fields.Str(required=True),
        "phenomenon": fields.Str(required=True),
        "tuple_size": fields.Int(required=True),
        "replication": fields.Int(required=True)    
    } 
    
    #Create a new project
    @jwt_required
    @use_args(user_args, location="json")
    def post(self, args):
        email = get_jwt_identity()
        project_name = args['project_name']
        tuple_size = args['tuple_size']
        phenomenon = args['phenomenon']
        replication = args['replication'] 
         
        project_id, msg = new_project(
                    email,
                    project_name,
                    phenomenon,
                    tuple_size,
                    replication,
                    'example.tsv'  # !!!! add instance file !!!!
                )
        
        if (not project_id):  # project not created 
            abort(400)
               
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
            abort(401)
            
        tup_id, tup = next_tuple(project_id, email)
        
        if tup is None:
            return {"Error": "No tuple to annotate"}
        
        return jsonify(tup)
        
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
            abort(401)
        
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
            abort(401)
        
        rst, file = generate_gold(project_id)

        if not rst:
            abort(404, description="Project not found")
         
        response = make_response(file)   
        response.headers['content-type'] = 'application/octet-stream'
        return response


api.add_resource(LoginAPI, '/litescale/api/login', endpoint='login')
api.add_resource(UsersAPI, '/litescale/api/users', endpoint='users')
api.add_resource(ProjectListAPI, '/litescale/api/projectList', endpoint='projects')
api.add_resource(ProjectsAPI, '/litescale/api/projects', endpoint='project')
api.add_resource(TuplesAPI, '/litescale/api/tuples', endpoint='tuples')
api.add_resource(AnnotationsAPI, '/litescale/api/annotations', endpoint='annotation')
api.add_resource(GoldAPI, '/litescale/api/gold', endpoint='gold')


if __name__ == '__main__':
    app.run(debug=True)
