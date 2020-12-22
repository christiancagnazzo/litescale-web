from flask import Flask, jsonify, abort, make_response, url_for
from flask_restful import Api, Resource, fields, marshal
from werkzeug.security import generate_password_hash, check_password_hash
from webargs import fields
import json
from webargs.flaskparser import use_args, use_kwargs, parser
from litescale import *

# QUESTION:
# - abort or return error?
# TO DO:
# security authentication
# authorization resource

app = Flask(__name__)
api = Api(app)


AUTHORIZED = 'authorized'
OWNER = 'owner'

# Return validation errors as JSON
# 404 not found
# 401 not authorized
@app.errorhandler(422) # Unprocessable Entity
@app.errorhandler(400) # Bad request
def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    if headers:
        return jsonify({"errors": messages}), err.code, headers
    else:
        return jsonify({"errors": messages}), err.code
    
    
# ----------------------------------------USERS RESOURCE---------------------------------------------- #

class UsersAPI(Resource):
    def __init__(self):
        super(UsersAPI, self).__init__()
        
       
    # Return user info (email and password)   ??? 
    @use_args({"email": fields.Str(required=True)}, location="query")
    def get(self, args): 
        rst, user = search_user(args['email']);
        
        if (rst):
            return {'email': user[0][0], 'passwordHash': user[0][1]}
        else:
            return {'Error': 'User not found'}
    
         
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
            return {'Error': 'Existing user'}
        
        return jsonify({ 'email': email }, 201, {'Location': url_for('users', email=email,_external = True)})
    
    # Delete user  
    @use_args({"email": fields.Str(required=True)}, location="query")
    def delete(self, args): 
        email = args['email']
        
        rst, msg = delete_user(email)
    
        if not rst:
            abort(404);
            
        return jsonify({"result": "True"}, 200)

# ---------------------------------------------------------------------------------------------------- #


# -----------------------------------PROJECT LIST RESOURCE-------------------------------------------- #

class ProjectListAPI(Resource):
    def __init__(self):
        super(ProjectListAPI, self).__init__() 
   
    user_args = {
        "email": fields.Str(required=True),
        "accessType": fields.Str(required=True) # authorized or owner
    }     
       
    # Return project list 
    @use_args(user_args, location="json") 
    def get(self, args): 
        email = args['email']
        accessType = args['accessType']
        
        if (accessType != AUTHORIZED and accessType != OWNER):
            abort(400)
            
        rst, msg = search_user(args['email']);
        
        if not rst:
            abort(404)
    
        if accessType == AUTHORIZED:
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
    @use_args({"id": fields.Int(required=True)}, location="query")
    def get(self, args):
        project_id = args['id']
        
        rst, project_dict = get_project(project_id)
        
        if not rst:
            abort(404)
        
        return project_dict
    
    # Delete project
    @use_args({"id": fields.Int(required=True)}, location="query")
    def delete(self, args):
        project_id = args['id']
        
        rst, msg = delete_project(project_id) 
        
        if not rst:
            return {'Error': msg} # or abort ?
        
        return jsonify({"result": "True"}, 200)
    
    
    user_args = {
        "email": fields.Str(required=True),
        "project_name": fields.Str(required=True),
        "phenomenon": fields.Str(required=True),
        "tuple_size": fields.Int(required=True),
        "replication": fields.Int(required=True)    
    } 
    
    #Create a new project
    @use_args(user_args, location="json")
    def post(self, args):
        email = args['email']
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
               
        return jsonify({"result": "True"}, 201)
    
# ---------------------------------------------------------------------------------------------------- #


# -------------------------------------TUPLE RESOURCE------------------------------------------------- #

class TuplesAPI(Resource):
    def __init__(self):
        super(TuplesAPI, self).__init__() 
        
    user_args = {
        "email": fields.Str(required=True),
        "project_id": fields.Int(required=True)
    }
    
    # Get next tuple to annotate
    @use_args(user_args, location="json")
    def get(self, args):
        email = args['email']
        project_id = args['project_id']
        
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
        "email": fields.Str(required=True),
        "project_id": fields.Int(required=True),
        "tup_id": fields.Int(required=True),
        "answer_best": fields.Int(required=True),
        "answer_worst": fields.Int(required=True)
    }
    
    # Add annotation into db
    @use_args(user_args, location="json")
    def post(self, args):
        email = args['email']
        project_id = args['project_id']
        tup_id = args['tup_id']
        answer_best = args['answer_best']
        answer_worst = args['answer_worst']
        
        x, y = annotate(project_id, email, tup_id, answer_best, answer_worst)
        return jsonify({"Annotations": x, "Tuples": y})        

# ---------------------------------------------------------------------------------------------------- #

# ------------------------------.......-------GOLD RESOURCE------------------------------------------- #

class GoldAPI(Resource):
    def __init__(self):
        super(GoldAPI, self).__init__() 
        
    user_args = {
        "email": fields.Str(required=True),
        "project_id": fields.Int(required=True),
    }
    
    # Add annotation into db
    @use_args(user_args, location="json")
    def get(self, args):
        project_id = args['project_id']
        
        rst, file = generate_gold(project_id)

        if not rst:
            abort(404)
         
        response = make_response(file)   
        response.headers['content-type'] = 'application/octet-stream'
        return response


api.add_resource(UsersAPI, '/litescale/api/users', endpoint='users')
api.add_resource(ProjectListAPI, '/litescale/api/projectList', endpoint='projects')
api.add_resource(ProjectsAPI, '/litescale/api/projects', endpoint='project')
api.add_resource(TuplesAPI, '/litescale/api/tuples', endpoint='tuples')
api.add_resource(AnnotationsAPI, '/litescale/api/annotations', endpoint='annotation')
api.add_resource(GoldAPI, '/litescale/api/gold', endpoint='gold')

if __name__ == '__main__':
    app.run(debug=True)
