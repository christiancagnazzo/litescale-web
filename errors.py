
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
        "status": 400
    },
    "InvalidFileUploadError": {
        "message": "Invalid file, upload a tsv file",
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
   
   
"""

expired_token_loader()

Funzione da chiamare quando un token scaduto accede a un endpoint protetto

invalid_token_loader()

Funzione da chiamare quando un token non valido accede a un endpoint protetto

needs_fresh_token_loader()

Funzione da chiamare quando un token non aggiornato accede a un fresh_jwt_required()endpoint

unauthorized_loader()

Funzione da chiamare quando una richiesta senza JWT accede a un endpoint protetto

"""