from flask import Flask, jsonify, abort, make_response, url_for
from flask_restful import Api, Resource, fields, marshal
from werkzeug.security import generate_password_hash, check_password_hash
from webargs import fields
from webargs.flaskparser import use_args, use_kwargs, parser
from litescale import *

app = Flask(__name__)
api = Api(app)


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
    
    
# ----------------------------------------USERS RESOURCE--------------------------------------------- #

class UsersAPI(Resource):
    def __init__(self):
        super(UsersAPI, self).__init__()
        
    # Return user info (email and password) ??? 
    @use_args({"email": fields.Str(required=True)}, location="query")
    def get(self, args): 
        rst, user = search_user(args['email']);
        
        if (rst):
            return {'email': user[0][0], 'passwordHash': user[0][1]}
        else:
            return {'Error': 'User not found'}
         
    user_wargs = {
        "email": fields.Str(required=True),
        "password": fields.Str(required=True)
    }     
       
    # Insert a new user 
    @use_args(user_wargs, location="json") 
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
            
        return {"result": "True"}

# ---------------------------------------------------------------------------------------------------- #

api.add_resource(UsersAPI, '/litescale/api/users', endpoint='users')

if __name__ == '__main__':
    app.run(debug=True)
