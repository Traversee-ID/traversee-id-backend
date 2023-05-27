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
class Campaign(db.Model):
    __tablename__ = "campaigns"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    image_url: str = db.Column(db.String, nullable=False)
    category_id: int = db.Column(db.Integer, db.ForeignKey('campaign_categories.id'), nullable=False)
    details = db.relationship("CampaignDetails", uselist=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

@dataclass
class CampaignDetails(db.Model):
    __tablename__ = "campaign_details"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)

@dataclass
class CampaignCategory(db.Model):
    __tablename__ = "campaign_categories"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), unique=True, nullable=False)
    image_url: str = db.Column(db.String, nullable=False)

@app.route("/campaigns", methods=["GET"])
def get_campaigns():
    return {"data": ""}, 200

@app.route("/campaigns/<int:id>", methods=["GET"])
def get_campaign(id):
    campaign = db.session.get(Campaign, id)
    if not campaign:
        return {"message": f"Campaign with id {id} doesn't exist"}, 404
    return {"data": campaign}, 200

@app.route("/campaigns/<int:id>/details", methods=["GET"])
def get_campaign_detail(id):
    campaign_detail = db.session.query(CampaignDetails) \
        .filter_by(campaign_id=id).first()
    if not campaign_detail:
        return {"message": f"Campaign with id {id} doesn't exist"}, 404
    return {"data": campaign_detail}, 200

@app.route("/campaign-categories/<int:id>/campaigns", methods=["GET"])
def get_campaigns_by_category(id):
    return {"data": ""}, 200

@app.route("/campaign-categories", methods=["GET"])
def get_campaign_categories():
    categories = db.session.query(CampaignCategory) \
        .order_by(CampaignCategory.name.asc()).all()
    return {"data": categories}, 200

@app.route("/campaign-categories/<int:id>", methods=["GET"])
def get_campaign_category(id):
    category = db.session.get(CampaignCategory, id)
    if not category:
        return {"message": f"Category with id {id} doesn't exist"}, 404
    return {"data": category}, 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080)