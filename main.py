from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from firebase_admin import auth, initialize_app
from credentials import credentials
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from authentication import authenticated_only
from dataclasses import dataclass
from datetime import date

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
    place: str = db.Column(db.String, nullable=False)
    start_date: date = db.Column(db.Date, nullable=False)
    end_date: date = db.Column(db.Date, nullable=False)
    category_id: int = db.Column(db.Integer, db.ForeignKey('campaign_categories.id'), nullable=False)
    details = db.relationship("CampaignDetails", uselist=False)
    participants = db.relationship("CampaignParticipant", uselist=True)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False)

    @property
    def status(self):
        if self.start_date > date.today():
            return "Coming Soon"
        if self.end_date <= date.today():
            return "Ongoing"
        return "Completed"

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "image_url": self.image_url,
            "start_date": self.start_date.strftime("%d %B %Y"),
            "end_date": self.end_date.strftime("%d %B %Y"),
            "status": self.status,
            "category_id": self.category_id,
            "category_name": db.session.get(CampaignCategory, self.category_id).name,
            "total_participants": len(self.participants)
        }
    
    @staticmethod
    def serialize_list(campaigns):
        return [campaign.serialize() for campaign in campaigns]

@dataclass
class CampaignDetails(db.Model):
    __tablename__ = "campaign_details"

    id = db.Column(db.Integer, primary_key=True)
    description: str = db.Column(db.Text, nullable=False)
    terms: str = db.Column(db.Text, nullable=False)
    mission: str = db.Column(db.Text, nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)

@dataclass
class CampaignParticipant(db.Model):
    __tablename__ = "campaign_participants"

    user_id: str = db.Column(db.String, primary_key=True)
    campaign_id: int = db.Column(db.Integer, db.ForeignKey('campaigns.id'), primary_key=True)
    submission_url: str = db.Column(db.String)

@dataclass
class CampaignCategory(db.Model):
    __tablename__ = "campaign_categories"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), unique=True, nullable=False)
    image_url: str = db.Column(db.String, nullable=False)

@app.route("/campaigns", methods=["GET"])
@authenticated_only
def get_campaigns():
    campaigns = db.session.query(Campaign) \
        .order_by(Campaign.created_at.desc()).all()
    return {"data": Campaign.serialize_list(campaigns)}, 200

@app.route("/campaigns/<int:id>", methods=["GET"])
@authenticated_only
def get_campaign(id):
    campaign = db.session.get(Campaign, id)
    if not campaign:
        return {"message": f"Campaign with id {id} doesn't exist"}, 404
    return {"data": campaign.serialize()}, 200

@app.route("/campaigns/<int:id>/registrations", methods=["POST"])
@authenticated_only
def register_campaign(id):
    campaign = db.session.get(Campaign, id)
    if not campaign:
        return {"message": f"Campaign with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("user_id")
    campaign_participant = db.session.query(CampaignParticipant) \
        .filter_by(user_id=user_id, campaign_id=campaign.id).first()
    
    if campaign_participant:
        return {"message": f"User {user_id} is already registered"}, 409
    
    campaign_participant = CampaignParticipant(user_id=user_id, campaign_id=campaign.id)
    db.session.add(campaign_participant)
    db.session.commit()

    return {"data": campaign_participant}, 201

@app.route("/campaigns/<int:id>/submissions", methods=["POST"])
@authenticated_only
def submit_campaign_tasks(id):
    campaign = db.session.get(Campaign, id)
    if not campaign:
        return {"message": f"Campaign with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("user_id")
    campaign_participant = db.session.query(CampaignParticipant) \
        .filter_by(user_id=user_id, campaign_id=campaign.id).first()
    
    submission_url = request.json.get("submission_url")
    if campaign_participant:
        campaign_participant.submission_url = submission_url
    else:
        campaign_participant = CampaignParticipant(user_id=user_id, campaign_id=campaign.id, submission_url=submission_url)
        db.session.add(campaign_participant)
    db.session.commit()
    
    return {"data": campaign_participant}, 201

@app.route("/campaigns/<int:id>/details", methods=["GET"])
@authenticated_only
def get_campaign_detail(id):
    campaign_detail = db.session.query(CampaignDetails) \
        .filter_by(campaign_id=id).first()
    if not campaign_detail:
        return {"message": f"Campaign with id {id} doesn't exist"}, 404
    return {"data": campaign_detail}, 200

@app.route("/campaign-categories/<int:id>/campaigns", methods=["GET"])
@authenticated_only
def get_campaigns_by_category(id):
    category = db.session.get(CampaignCategory, id)
    if not category:
        return {"message": f"Category with id {id} doesn't exist"}, 404
    
    campaigns = db.session.query(Campaign) \
        .filter_by(category_id=id) \
        .order_by(Campaign.created_at.desc()).all()
    return {"data": campaigns}, 200

@app.route("/campaign-categories", methods=["GET"])
@authenticated_only
def get_campaign_categories():
    categories = db.session.query(CampaignCategory) \
        .order_by(CampaignCategory.name.asc()).all()
    return {"data": categories}, 200

@app.route("/campaign-categories/<int:id>", methods=["GET"])
@authenticated_only
def get_campaign_category(id):
    category = db.session.get(CampaignCategory, id)
    if not category:
        return {"message": f"Category with id {id} doesn't exist"}, 404
    return {"data": category}, 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8080)