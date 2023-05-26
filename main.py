from flask import Flask, render_template, request, flash, url_for, redirect
from firebase_admin import auth, initialize_app
from credentials import credentials
from flask_sqlalchemy import SQLAlchemy
from os import getenv

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URI")

db = SQLAlchemy(app)
firebase = initialize_app(credentials)

class ForumModel(db.Model):
    post_id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default = db.func.now())
    author = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Integer)
    likes = db.Column(db.Integer, default = 0)
    image_url = db.Column(db.String(50))

    def __init__(self, title, text, author):
        self.title = title
        self.text = text
        self.author = author

#show all forum posts
@app.route("/forum")
def show_forum():
    forums = ForumModel.query.all()
    return render_template('show_forum.html', posts = forums), 200

#create new post
@app.route("/forum/create", methods = ['GET', 'POST'])
def create():
    if request.method == 'POST':
        if not request.form['title'] or not request.form['text'] or not request.form['author']:
            flash('Please enter all the fields', 'error')
        else:
            post = ForumModel(request.form['title'], request.form['text'], request.form['author'])
            db.session.add(post)
            db.session.commit()
            flash('Record was successfully added')
            return redirect(url_for('show_forum'))
    return render_template('create.html')

#get specific post detail
@app.route('/forum/<int:id>')
def get_post(id):
    post = ForumModel.query.filter_by(post_id=id).first()
    if post:
        return render_template('data.html', post = post)
    return f"Post with id = {id} doesn't exists"
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080)
