from dataclasses import dataclass
from firebase_admin import auth, initialize_app
from flask import Flask
from credentials import credentials
from flask_sqlalchemy import SQLAlchemy
from os import getenv

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URI")

db = SQLAlchemy(app)
firebase = initialize_app(credentials)

@app.route("/", methods=["GET"])
def hello_world():
    return {"message": "Hello, World!"}, 200

@app.route("/user/<string:id>", methods=["GET"])
def user_info(id):
    try:
        user = auth.get_user(id)
        return {"data": {"id": user.id}}, 200
    except:
        return {"message": "User not found!"}, 404
    
@dataclass
class Category(db.Model):
    __tablename__ = "categories"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), unique=True, nullable=False)
    image_url: str = db.Column(db.String, nullable=False)

@app.route("/campaigns", methods=["GET"])
def get_campaigns():
    return {"data": ""}, 200

@app.route("/categories/<int:id>/campaigns", methods=["GET"])
def get_campaigns_by_category():
    return {"data": ""}, 200

@app.route("/categories", methods=["GET"])
def get_categories():
    categories = db.session.query(Category).order_by(Category.name.asc()).all()
    return {"data": categories}, 200

@app.route("/categories/<int:id>", methods=["GET"])
def get_category(id):
    category = db.session.get(Category, id)
    if not category:
        return {"message": f"Category with id {id} not found!"}, 404
    return {"data": category}, 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080)