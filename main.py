from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from firebase_admin import auth, initialize_app
from credentials import credentials
from flask_sqlalchemy import SQLAlchemy
from os import getenv

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URI")

db = SQLAlchemy(app)
firebase = initialize_app(credentials)

@dataclass
class Forum(db.Model):

    forum_id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(100), nullable=False)
    text: str = db.Column(db.String(500), nullable=False)
    created_at: str = db.Column(db.DateTime, default=datetime.utcnow)
    author: int = db.Column(db.Integer, nullable=False)
    comments = db.relationship('Comment', lazy=True)
    likes: int = db.Column(db.Integer, default = 0)
    image_url: str = db.Column(db.String(50))

    def __init__(self, title, text, author):
        self.title = title
        self.text = text
        self.author = author

@dataclass
class Comment(db.Model):

    comment_id: int = db.Column(db.Integer, primary_key=True)
    text: str = db.Column(db.String(300), nullable=False)
    author: int = db.Column(db.Integer, nullable=False)
    forum: int = db.Column(db.Integer, db.ForeignKey('forum.forum_id'), nullable=False)

    def __init__(self, text, author, forum):
        self.text = text
        self.author = author
        self.forum = forum


#show all forum forums
@app.route("/forums")
def show_forum():
    forums = db.session.query(Forum).order_by(Forum.created_at.desc()).all()
    return {"data": forums}, 200

#create new forum
@app.route("/forums/create", methods = ['POST'])
def create_forum():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = request.get_json()
        newForum = Forum(data['title'], data['text'], data['author'])
        db.session.add(newForum)
        db.session.commit()
        return {"message": f"Forum created"}, 200
    else:
        return {"message": f"Forum failed to create, or content-type not supported!"}, 404

#get specific forum detail
@app.route('/forums/<int:id>')
def get_forum(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    return {"data": forum}, 200

#delete specific forum
@app.route('/forums/<int:id>/delete', methods=["DELETE"])
def delete_forum(id):
    forum = Forum.query.filter_by(forum_id=id).first()
    if forum:
        db.session.delete(forum)
        db.session.commit()
        return {"message": f"Forum with id {id} deleted"}, 200
    return {"message": f"Forum with id {id} doesn't exist"}, 404

#give forum a like
@app.route('/forums/<int:id>/like', methods=["PUT"])
def like_forum(id):
    forum = Forum.query.filter_by(forum_id=id).first()
    if forum:
        forum.likes += 1
        db.session.commit()
        return {"message": f"Added like to forum with id {id}"}, 200
    return {"message": f"Forum with id {id} doesn't exist"}, 404

#show and add comment to forum
@app.route('/forums/<int:id>/comment', methods=["GET", "POST"])
def comment_forum(id):
    forum = Forum.query.filter_by(forum_id=id).first()

    if request.method == 'GET' and forum:
        comments = Comment.query.filter_by(forum=id).all()
        return {"data": comments}, 200

    if request.method == 'POST' and forum:
        content_type = request.headers.get('Content-Type')
        if (content_type == 'application/json'):
            data = request.get_json()
            newComment = Comment(data['text'], data['author'], id)
            db.session.add(newComment)
            db.session.commit()
            return {"message": f"Comment added to forum with id {id}"}, 200
        else:
            return {"message": f"Comment failed to create!"}, 404

    return {"message": f"Forum with id {id} doesn't exist!"}, 404

#delete specific comment
@app.route('/forums/<int:id>/<int:comment_id>', methods=["DELETE"])
def delete_comment(id, comment_id):
    comment = Comment.query.filter_by(comment_id=comment_id).first()
    if comment:
        db.session.delete(comment)
        db.session.commit()
        return {"message": f"Comment with id {comment_id} deleted"}, 200
    return {"message": f"Comment with id {comment_id} doesn't exist"}, 404
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080)
