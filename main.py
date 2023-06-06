from api.v1 import v1
from api.v1.extensions import db
from flask import Flask
from firebase_admin import initialize_app
from credentials import credentials
from os import getenv

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URI")
app.register_blueprint(v1, url_prefix="/api/v1")

db.init_app(app)
firebase = initialize_app(credentials)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=8080)
