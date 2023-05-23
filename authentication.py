from firebase_admin import auth
from flask import request
from functools import wraps

def authenticated_only(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not request.headers.get("Authorization"):
            return {"message": "No credentials provided."}, 401
        try:
            _, token = parse_credentials(request.headers["Authorization"])
            user = auth.verify_id_token(token)
            request.user = user
        except:
            return {"message": "Invalid token provided."}, 401
        return f(*args, **kwargs)
    return wrap

def parse_credentials(credentials):
    credential_list = credentials.split(" ")
    if len(credential_list) != 2:
        return None, None
    return credential_list