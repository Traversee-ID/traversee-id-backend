from dataclasses import dataclass
from firebase_admin import auth
from ..models.campaigns import Campaign
from ..extensions import db

@dataclass
class Forum(db.Model):
    __tablename__ = "forums"

    total_likes: int
    total_comments: int
    user_display_name: str
    user_profile_image: str
    created_date: str

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

    @property
    def total_comments(self):
        return len(self.comments)

    @property
    def user_display_name(self):
        try:
            user = auth.get_user(uid=self.author_id)
            return user.display_name
        except auth.UserNotFoundError:
            return None
    
    @property
    def user_profile_image(self):
        try:
            user = auth.get_user(uid=self.author_id)
            return user.photo_url
        except auth.UserNotFoundError:
            return None
        
    @property
    def created_date(self):
        return self.created_at.strftime("%d %B %Y")
        
    def serialize(self, user_id):
        forum_likes = db.session.query(ForumLike) \
            .filter_by(forum_id=self.id, user_id=user_id).first()

        forum_campaign = db.session.get(ForumCampaign, self.id)
        campaign = db.session.get(Campaign, forum_campaign.campaign_id) if forum_campaign else None
        campaign_extracted = {
            "id": campaign.id,
            "name": campaign.name,
            "category": campaign.category_name,
            "image_url": campaign.image_url
            } if campaign else None

        return {
            "forum": self,
            "is_liked": forum_likes != None,
            "campaign": campaign_extracted
        }
    
    @staticmethod
    def serialize_list(user_id, forums):
        return [forum.serialize(user_id) for forum in forums]

@dataclass
class ForumLike(db.Model):
    __tablename__ = "forum_likes"

    forum_id: int = db.Column(db.ForeignKey('forums.id'), primary_key=True)
    user_id: str = db.Column(db.String, primary_key=True)

@dataclass
class ForumCampaign(db.Model):
    __tablename__ = "forum_campaigns"

    forum_id: int = db.Column(db.ForeignKey('forums.id'), primary_key=True)
    campaign_id: int = db.Column(db.ForeignKey('campaigns.id'), nullable=False)

@dataclass
class Comment(db.Model):
    __tablename__ = "comments"

    user_display_name: str
    user_profile_image: str
    created_date: str

    id: int = db.Column(db.Integer, primary_key=True)
    text: str = db.Column(db.String(300), nullable=False)
    author_id: str = db.Column(db.String, nullable=False)
    forum_id: int = db.Column(db.Integer, db.ForeignKey('forums.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    @property
    def user_display_name(self):
        try:
            user = auth.get_user(uid=self.author_id)
            return user.display_name
        except auth.UserNotFoundError:
            return None
    
    @property
    def user_profile_image(self):
        try:
            user = auth.get_user(uid=self.author_id)
            return user.photo_url
        except auth.UserNotFoundError:
            return None
        
    @property
    def created_date(self):
        return self.created_at.strftime("%d %B %Y")