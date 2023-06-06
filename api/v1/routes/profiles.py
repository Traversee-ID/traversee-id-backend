from flask import Blueprint, request
from firebase_admin import auth
from google.cloud import storage
from ..decorator import authenticated_only

profiles = Blueprint("profiles", __name__)

@profiles.route("/profile-pictures", methods=["PUT"])
@authenticated_only
def update_profile_picture():
    storage_client = storage.Client()
    bucket = storage_client.get_bucket("traversee-id")
    user_id = request.user.get("uid")

    file = request.files.get("photo")
    if not (file and file.content_type.startswith("image/")):
        return {"message": "File is not a valid image"}, 400
    
    blob = bucket.blob(f"profiles/photo-{user_id}.{file.content_type[6:]}")
    blob.upload_from_file(file)
    blob.make_public()

    user = auth.update_user(uid=user_id, photo_url=blob.public_url)

    return {"data": user.photo_url}, 200