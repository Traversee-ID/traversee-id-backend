from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from firebase_admin import auth, initialize_app
from credentials import credentials
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from authentication import authenticated_only
from dataclasses import dataclass

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URI")

db = SQLAlchemy(app)
firebase = initialize_app(credentials)

@dataclass
class Forum(db.Model):
    __tablename__ = "forums"

    total_likes: int

    id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(100), nullable=False)
    text: str = db.Column(db.String(500), nullable=False)
    author_id: str = db.Column(db.String, nullable=False)
    image_url: str = db.Column(db.String)
    comments = db.relationship('Comment', uselist=True)
    likes = db.relationship('ForumLike', uselist=True)
    created_at = db.Column(db.DateTime, default=db.func.now())

    @property
    def total_likes(self):
        return len(self.likes)
    

@dataclass
class ForumLike(db.Model):
    __tablename__ = "forum_likes"

    forum_id: int = db.Column(db.ForeignKey('forums.id'), primary_key=True)
    user_id: str = db.Column(db.String, primary_key=True)

@dataclass
class Comment(db.Model):
    __tablename__ = "comments"

    id: int = db.Column(db.Integer, primary_key=True)
    text: str = db.Column(db.String(300), nullable=False)
    author_id: str = db.Column(db.String, nullable=False)
    forum_id: int = db.Column(db.Integer, db.ForeignKey('forums.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())


@app.route("/forums")
def get_forums():
    page = request.args.get("page")

    if page is not None and page.isdecimal():
        forums = db.session.query(Forum) \
            .order_by(Forum.created_at.desc()) \
            .paginate(page=int(page), per_page=5, error_out=False).items

    else:
        forums = db.session.query(Forum).order_by(Forum.created_at.desc()).all()
    
    return {"data": forums}, 200

@app.route("/forums", methods = ['POST'])
@authenticated_only
def create_forum():
    title = request.json.get("title")
    text = request.json.get("text")

    if not title or not text:
        return {"message": "Title and text are required"}, 400
    
    forum = Forum(title=title, text=text, author_id=request.user.get('user_id'))
    db.session.add(forum)
    db.session.commit()
    return {"data": forum}, 200

@app.route('/forums/<int:id>')
def get_forum(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    return {"data": forum}, 200

@app.route('/forums/<int:id>', methods=["DELETE"])
@authenticated_only
def delete_forum(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    
    if forum.author_id != request.user.get("user_id"):
        return {"message": f"You're not author of the forum with id {id}"}, 403
    
    db.session.delete(forum)
    db.session.commit()
    return {"message": f"Forum with id {id} deleted"}, 200

@app.route('/forums/<int:id>/likes', methods=["POST"])
@authenticated_only
def add_forum_likes(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("user_id")
    forum_likes = db.session.get(ForumLike, (forum.id, user_id))
    if forum_likes:
        return {"message": f"Forum {id} is already liked"}, 409
    
    forum_likes = ForumLike(forum_id=forum.id, user_id=user_id)
    db.session.add(forum_likes)
    db.session.commit()
    return {"data": forum}, 200
    

@app.route('/forums/<int:id>/likes', methods=["DELETE"])
@authenticated_only
def delete_forum_likes(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("user_id")
    forum_likes = db.session.get(ForumLike, (forum.id, user_id))
    if not forum_likes:
        return {"message": f"Forum {id} is not liked yet"}, 409
    
    db.session.delete(forum_likes)
    db.session.commit()
    return {"data": forum}, 200

@app.route('/forums/<int:id>/comments', methods=["POST"])
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

@app.route('/forums/<int:id>/comments', methods=["GET"])
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

@app.route('/forums/<int:id>/comments/<int:comment_id>', methods=["DELETE"])
@authenticated_only
def delete_forum_comment(id, comment_id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    
    comment = db.session.get(Comment, comment_id)
    if not comment:
        return {"message": f"Comment with id {id} doesn't exist"}, 404
    
    if comment.author_id != request.user.get("user_id"):
        return {"message": f"You're not author of the comment with id {id}"}, 403
    
    db.session.delete(comment)
    db.session.commit()
    return {"message": f"Comment with id {comment_id} deleted"}, 200

   
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080)