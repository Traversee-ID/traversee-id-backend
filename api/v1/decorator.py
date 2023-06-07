from firebase_admin import auth
from flask import request
from functools import wraps
from .helper import parse_token

def authenticated_only(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        if not request.headers.get("Authorization"):
            return {"message": "No credentials provided."}, 401
        try:
            _, token = parse_token(request.headers["Authorization"])
            user = auth.verify_id_token(token)
            request.user = user
        except:
            return {"message": "Invalid token provided."}, 401
        return func(*args, **kwargs)
    return wrap