from flask import Blueprint, request
from firebase_admin import auth
from os import getenv
from ..helper import get_bucket_storage
from ..decorator import authenticated_only

profiles = Blueprint("profiles", __name__)

@profiles.route("/profile-pictures", methods=["PUT"])
@authenticated_only
def update_profile_picture():
    bucket = get_bucket_storage(getenv("BUCKET_NAME"))
    user_id = request.user.get("uid")

    file = request.files.get("photo")
    if not (file and file.content_type.startswith("image/")):
        return {"message": "File is not a valid image"}, 400
    
    blob = bucket.blob(f"profiles/photo-{user_id}.{file.content_type[6:]}")
    blob.upload_from_file(file)
    blob.make_public()

    user = auth.update_user(uid=user_id, photo_url=blob.public_url)

    return {"data": user.photo_url}, 200