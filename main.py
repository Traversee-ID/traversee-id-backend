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

    status: str
    start_date: str
    end_date: str
    category_name: str
    total_participants: int

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    image_url: str = db.Column(db.String, nullable=False)
    place: str = db.Column(db.String, nullable=False)
    _start_date = db.Column("start_date", db.Date, nullable=False)
    _end_date = db.Column("end_date", db.Date, nullable=False)
    category_id: int = db.Column(db.Integer, db.ForeignKey('campaign_categories.id'), nullable=False)
    details = db.relationship("CampaignDetails", uselist=False)
    participants = db.relationship("CampaignParticipant", uselist=True)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False)

    @property
    def status(self):
        if self._start_date > date.today():
            return "Coming Soon"
        if self._end_date <= date.today():
            return "Ongoing"
        return "Completed"
    
    @property
    def start_date(self):
        return self._start_date.strftime("%d %B %Y")
    
    @property
    def end_date(self):
        return self._end_date.strftime("%d %B %Y")
    
    @property
    def category_name(self):
        return db.session.get(CampaignCategory, self.category_id).name
    
    @property
    def total_participants(self):
        return len(self.participants)
    
    def serialize(self, user_id):
        participant = db.session.query(CampaignParticipant) \
            .filter_by(user_id=user_id, campaign_id=self.id).first()
        return {
            "campaign": self,
            "is_registered": participant != None
        }
    
    @staticmethod
    def serialize_list(user_id, campaigns):
        return [campaign.serialize(user_id) for campaign in campaigns]

@dataclass
class CampaignDetails(db.Model):
    __tablename__ = "campaign_details"

    id = db.Column(db.Integer, primary_key=True)
    initiator_id = db.Column(db.String, nullable=False)
    description: str = db.Column(db.Text, nullable=False)
    terms: str = db.Column(db.Text, nullable=False)
    mission: str = db.Column(db.Text, nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)

@dataclass
class CampaignWinner(db.Model):
    __tablename__ = "campaign_winners"

    user_id: str = db.Column(db.String, primary_key=True)
    campaign_id: int = db.Column(db.Integer, db.ForeignKey('campaigns.id'), primary_key=True)
    position: int = db.Column(db.Integer, nullable=False)

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
    page = request.args.get("page")

    if isinstance(page, str) & page.isdecimal():
        campaigns = db.session.query(Campaign) \
            .order_by(Campaign.created_at.desc()) \
            .paginate(page=int(page), per_page=1, error_out=False)
    else:
        campaigns = db.session.query(Campaign) \
            .order_by(Campaign.created_at.desc()).all()

    user_id = request.user.get("user_id")
    return {"data": Campaign.serialize_list(user_id, campaigns)}, 200

@app.route("/campaigns/<int:id>", methods=["GET"])
@authenticated_only
def get_campaign(id):
    campaign = db.session.get(Campaign, id)
    if not campaign:
        return {"message": f"Campaign with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("user_id")
    return {"data": campaign.serialize(user_id)}, 200

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