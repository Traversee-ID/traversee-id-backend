from firebase_admin import auth
from flask import Blueprint, request
from os import getenv
from ..extensions import db
from ..decorator import authenticated_only
from ..helper import get_bucket_storage
from ..models.campaigns import Campaign
from ..models.forums import *

forums = Blueprint("forums", __name__)

@forums.route("/users/<string:id>/forums")
@authenticated_only
def get_forums_by_author(id):
    try:
        auth.get_user(uid=id)
    except auth.UserNotFoundError:
        return {"message": f"User with id {id} doesn't exist"}, 404
    
    page = request.args.get("page")

    if page is not None and page.isdecimal():
        forums = db.session.query(Forum) \
            .filter_by(author_id=id) \
            .order_by(Forum.created_at.desc()) \
            .paginate(page=int(page), per_page=5, error_out=False)
    else:
        forums = db.session.query(Forum) \
            .filter_by(author_id=id) \
            .order_by(Forum.created_at.desc()).all()
    
    return {"data": Forum.serialize_list(id, forums)}, 200

@forums.route("/forums")
@authenticated_only
def get_forums():
    page = request.args.get("page")

    if page is not None and page.isdecimal():
        forums = db.session.query(Forum) \
            .order_by(Forum.created_at.desc()) \
            .paginate(page=int(page), per_page=5, error_out=False)
    else:
        forums = db.session.query(Forum).order_by(Forum.created_at.desc()).all()
    
    user_id = request.user.get("uid")
    return {"data": Forum.serialize_list(user_id, forums)}, 200

@forums.route("/forums", methods = ['POST'])
@authenticated_only
def create_forum():
    data = request.form if request.content_type.startswith("multipart/form-data") else request.json

    title = data.get("title")
    text = data.get("text")
    campaign_id = data.get("campaign_id")

    if not title or not text:
        return {"message": "Title and text are required"}, 400
    
    image = request.files.get("image")
    if image:
        if not image.content_type.startswith("image/"):
            return {"message": "File is not a valid image"}, 400
        
        bucket = get_bucket_storage(getenv("BUCKET_NAME"))
        blob = bucket.blob(f"forums/{image.filename}.{image.content_type[6:]}")
        blob.upload_from_file(image)
        blob.make_public()

    image_url = blob.public_url if blob else None
    forum = Forum(title=title, text=text, image_url=image_url ,author_id=request.user.get('user_id'))
    db.session.add(forum)
    db.session.commit()

    if campaign_id and isinstance(campaign_id, int):
        campaign = db.session.get(Campaign, campaign_id)

    if campaign:
        forum_campaign = ForumCampaign(forum_id=forum.id, campaign_id=campaign.id)
        db.session.add(forum_campaign)
        db.session.commit()

    user_id = request.user.get("uid")
    return {"data": forum.serialize(user_id)}, 200

@forums.route('/forums/<int:id>')
@authenticated_only
def get_forum(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("uid")
    return {"data": forum.serialize(user_id)}, 200

@forums.route('/forums/<int:id>', methods=["DELETE"])
@authenticated_only
def delete_forum(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    
    if forum.author_id != request.user.get("uid"):
        return {"message": f"You're not author of the forum with id {id}"}, 403
    
    db.session.delete(forum)
    db.session.commit()
    return {"message": f"Forum with id {id} deleted"}, 200

@forums.route('/forums/<int:id>/likes', methods=["POST"])
@authenticated_only
def add_forum_likes(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("uid")
    forum_likes = db.session.get(ForumLike, (forum.id, user_id))
    if forum_likes:
        return {"message": f"Forum {id} is already liked"}, 409
    
    forum_likes = ForumLike(forum_id=forum.id, user_id=user_id)
    db.session.add(forum_likes)
    db.session.commit()
    return {"data": forum}, 200
    

@forums.route('/forums/<int:id>/likes', methods=["DELETE"])
@authenticated_only
def delete_forum_likes(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("uid")
    forum_likes = db.session.get(ForumLike, (forum.id, user_id))
    if not forum_likes:
        return {"message": f"Forum {id} is not liked yet"}, 409
    
    db.session.delete(forum_likes)
    db.session.commit()
    return {"data": forum}, 200

@forums.route('/forums/<int:id>/comments', methods=["POST"])
@authenticated_only
def create_forum_comments(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404

    text = request.json.get("text")
    if not text:
        return {"message": "Text are required"}, 400

    comments = Comment(text=text, author_id=request.user.get('user_id'), forum_id=forum.id)
    db.session.add(comments)
    db.session.commit()
    return {"data": comments}, 200

@forums.route('/forums/<int:id>/comments', methods=["GET"])
@authenticated_only
def get_forum_comments(id):
    page = request.args.get("page")
    forum = db.session.get(Forum, id)

    if page is not None and page.isdecimal():
        comments = db.session.query(Comment) \
            .filter_by(forum_id=forum.id) \
            .order_by(Comment.created_at.desc()) \
            .paginate(page=int(page), per_page=10, error_out=False).items

    else:
        comments = db.session.query(Comment) \
            .filter_by(forum_id=forum.id) \
            .order_by(Comment.created_at.desc()).all()

    return {"data": comments}, 200

@forums.route('/forums/<int:id>/comments/<int:comment_id>', methods=["DELETE"])
@authenticated_only
def delete_forum_comment(id, comment_id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    
    comment = db.session.get(Comment, comment_id)
    if not comment:
        return {"message": f"Comment with id {id} doesn't exist"}, 404
    
    if comment.author_id != request.user.get("uid"):
        return {"message": f"You're not author of the comment with id {id}"}, 403
    
    db.session.delete(comment)
    db.session.commit()
    return {"message": f"Comment with id {comment_id} deleted"}, 200