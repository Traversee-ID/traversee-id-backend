from dataclasses import dataclass
from datetime import date
from firebase_admin import auth
from ..extensions import db

@dataclass
class Campaign(db.Model):
    __tablename__ = "campaigns"

    status: str
    start_date: str
    end_date: str
    category_name: str
    location_name: str
    total_participants: int

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    image_url: str = db.Column(db.String, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('campaign_locations.id'), nullable=False)
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
        if self._end_date >= date.today():
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
    def location_name(self):
        return db.session.get(CampaignLocation, self.location_id).name
    
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

    initiator_name: str

    id = db.Column(db.Integer, primary_key=True)
    initiator_id = db.Column(db.String, nullable=False)
    description: str = db.Column(db.Text, nullable=False)
    terms: str = db.Column(db.Text, nullable=False)
    mission: str = db.Column(db.Text, nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)

    @property
    def initiator_name(self):
        initiator = auth.get_user(uid=self.initiator_id)
        return initiator.display_name
    
    def serialize(self, user_id, campaign_id):
        participant = db.session.query(CampaignParticipant) \
            .filter_by(user_id=user_id, campaign_id=campaign_id).first()
        return {
            "campaign_detail": self,
            "submission_url": participant.submission_url if participant else None
        }
    
@dataclass
class CampaignLocation(db.Model):
    __tablename__ = "campaign_locations"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    campaigns = db.relationship("Campaign", uselist=True)

@dataclass
class CampaignWinner(db.Model):
    __tablename__ = "campaign_winners"

    submission_url: str
    user_display_name: str
    user_profile_image: str

    user_id: str = db.Column(db.String, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), primary_key=True)
    position: int = db.Column(db.Integer, nullable=False)

    @property
    def submission_url(self):
        submission_url = db.session.query(CampaignParticipant.submission_url) \
              .filter_by(user_id=self.user_id, campaign_id=self.campaign_id).first()
        return submission_url[0] if submission_url else None
    
    @property
    def user_display_name(self):
        try:
            user = auth.get_user(uid=self.user_id)
            return user.display_name
        except auth.UserNotFoundError:
            return None
    
    @property
    def user_profile_image(self):
        try:
            user = auth.get_user(uid=self.user_id)
            return user.photo_url
        except auth.UserNotFoundError:
            return None

@dataclass
class CampaignParticipant(db.Model):
    __tablename__ = "campaign_participants"

    user_display_name: str
    user_profile_image: str

    user_id: str = db.Column(db.String, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), primary_key=True)
    submission_url: str = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    @property
    def user_display_name(self):
        try:
            user = auth.get_user(uid=self.user_id)
            return user.display_name
        except auth.UserNotFoundError:
            return None
    
    @property
    def user_profile_image(self):
        try:
            user = auth.get_user(uid=self.user_id)
            return user.photo_url
        except auth.UserNotFoundError:
            return None

@dataclass
class CampaignCategory(db.Model):
    __tablename__ = "campaign_categories"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), unique=True, nullable=False)
    image_url: str = db.Column(db.String, nullable=False)