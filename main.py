from firebase_admin import auth, initialize_app
from flask import Flask
from credentials import credentials

app = Flask(__name__)

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
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)