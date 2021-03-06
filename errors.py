
from werkzeug.exceptions import HTTPException
from webargs.flaskparser import parser
from flask import abort

class InternalServerError(HTTPException):
    pass

class EmailAlreadyExistsError(HTTPException):
    pass

class UnauthorizedError(HTTPException):
    pass

class InvalidEmailError(HTTPException):
    pass

class InvalidPasswordError(HTTPException):
    pass

class ResourceNotFoundError(HTTPException):
    pass

class InvalidTypeListError(HTTPException):
    pass

class UnauthorizedProjectError(HTTPException):
    pass

class InvalidFileUploadError(HTTPException):
    pass

class MissingProjectInfoError(HTTPException):
    pass

class EmptyAnnotationsError(HTTPException):
    pass


errors = {
    "InternalServerError": {
        "message": "Something went wrong",
        "status": 500
    },
    "EmailAlreadyExistsError": {
        "message": "User with given email address already exists",
        "status": 400
    },
    "UnauthorizedError": {
        "message": "Invalid username or password",
        "status": 401
    },
    "InvalidEmailError": {
        "message": "Invalid email",
        "status": 400
    },
    "InvalidPasswordError": {
        "message": "Password must be length at least 6 characters and  must have at least one number, one uppercase and one lowercase character",
        "status": 400
    },
    "ResourceNotFoundError": {
        "message": "Resource not found",
        "status": 404
    },
    "InvalidTypeListError": {
        "message": "Invalid type list. Indicate 'owner' or 'authorized'",
        "status": 400
    },
    "UnauthorizedProjectError": {
        "message": "User not auhtorized",
        "status": 401
    },
    "InvalidFileUploadError": {
        "message": "Invalid file upload",
        "status": 400
    },
    "MissingProjectInfoError": {
        "message": "Missing project info",
        "status": 400
    },
    "EmptyAnnotationsError": {
        "message": "Project not found or empty annotations",
        "status": 404
    }
}


# Function to handle error when missing input parameters
@parser.error_handler
def handle_error(error, req, schema, *, error_status_code, error_headers):
    fields = list(error.args[0].keys())
    abort(400, description="Missing fields: "+"-".join(fields))