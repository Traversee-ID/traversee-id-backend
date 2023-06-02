from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from firebase_admin import auth, initialize_app
from credentials import credentials
from os import getenv
from authentication import authenticated_only
from dataclasses import dataclass
from datetime import date

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URI")

db = SQLAlchemy(app)
firebase = initialize_app(credentials)

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
        return {
            "forum": self,
            "is_liked": forum_likes != None,
            "campaign_id": forum_campaign.campaign_id if forum_campaign else None
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

@app.route("/forums")
@authenticated_only
def get_forums():
    page = request.args.get("page")

    if page is not None and page.isdecimal():
        forums = db.session.query(Forum) \
            .order_by(Forum.created_at.desc()) \
            .paginate(page=int(page), per_page=5, error_out=False)

    else:
        forums = db.session.query(Forum).order_by(Forum.created_at.desc()).all()
    
    user_id = request.user.get("user_id")
    return {"data": Forum.serialize_list(user_id, forums)}, 200

@app.route("/forums", methods = ['POST'])
@authenticated_only
def create_forum():
    title = request.json.get("title")
    text = request.json.get("text")
    campaign_id = request.json.get("campaign_id")

    if not title or not text:
        return {"message": "Title and text are required"}, 400
    
    forum = Forum(title=title, text=text, author_id=request.user.get('user_id'))
    db.session.add(forum)
    db.session.commit()

    if campaign_id is not None and campaign_id.isdecimal():
        campaign = db.session.get(Campaign, campaign_id)
        forum_campaign = ForumCampaign(forum_id=forum.id, campaign_id=campaign.id)
        db.session.add(forum_campaign)
        db.session.commit()

    user_id = request.user.get("user_id")
    return {"data": forum.serialize(user_id)}, 200

@app.route('/forums/<int:id>')
@authenticated_only
def get_forum(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("user_id")
    return {"data": forum.serialize(user_id)}, 200

@app.route('/forums/<int:id>', methods=["DELETE"])
@authenticated_only
def delete_forum(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    
    if forum.author_id != request.user.get("user_id"):
        return {"message": f"You're not author of the forum with id {id}"}, 403
    
    db.session.delete(forum)
    db.session.commit()
    return {"message": f"Forum with id {id} deleted"}, 200

@app.route('/forums/<int:id>/likes', methods=["POST"])
@authenticated_only
def add_forum_likes(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("user_id")
    forum_likes = db.session.get(ForumLike, (forum.id, user_id))
    if forum_likes:
        return {"message": f"Forum {id} is already liked"}, 409
    
    forum_likes = ForumLike(forum_id=forum.id, user_id=user_id)
    db.session.add(forum_likes)
    db.session.commit()
    return {"data": forum}, 200
    

@app.route('/forums/<int:id>/likes', methods=["DELETE"])
@authenticated_only
def delete_forum_likes(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("user_id")
    forum_likes = db.session.get(ForumLike, (forum.id, user_id))
    if not forum_likes:
        return {"message": f"Forum {id} is not liked yet"}, 409
    
    db.session.delete(forum_likes)
    db.session.commit()
    return {"data": forum}, 200

@app.route('/forums/<int:id>/comments', methods=["POST"])
@authenticated_only
def create_forum_comments(id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404

    text = request.json.get("text")
    if not text:
        return {"message": "Text are required"}, 400

    comments = Comment(text=text, author_id=request.user.get('user_id'), forum_id=forum.id)
    db.session.add(comments)
    db.session.commit()
    return {"data": comments}, 200

@app.route('/forums/<int:id>/comments', methods=["GET"])
@authenticated_only
def get_forum_comments(id):
    page = request.args.get("page")
    forum = db.session.get(Forum, id)

    if page is not None and page.isdecimal():
        comments = db.session.query(Comment) \
            .filter_by(forum_id=forum.id) \
            .order_by(Comment.created_at.desc()) \
            .paginate(page=int(page), per_page=10, error_out=False).items

    else:
        comments = db.session.query(Comment) \
            .filter_by(forum_id=forum.id) \
            .order_by(Comment.created_at.desc()).all()

    return {"data": comments}, 200

@app.route('/forums/<int:id>/comments/<int:comment_id>', methods=["DELETE"])
@authenticated_only
def delete_forum_comment(id, comment_id):
    forum = db.session.get(Forum, id)
    if not forum:
        return {"message": f"Forum with id {id} doesn't exist"}, 404
    
    comment = db.session.get(Comment, comment_id)
    if not comment:
        return {"message": f"Comment with id {id} doesn't exist"}, 404
    
    if comment.author_id != request.user.get("user_id"):
        return {"message": f"You're not author of the comment with id {id}"}, 403
    
    db.session.delete(comment)
    db.session.commit()
    return {"message": f"Comment with id {comment_id} deleted"}, 200
    
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

def get_campaign_filters(status, location_id, user_id, is_registered):
    filters = []
    if status == "ongoing":
        filters = [Campaign._start_date <= date.today(), Campaign._end_date >= date.today()]
    elif status == "coming-soon":
        filters = [Campaign._start_date > date.today(), Campaign._end_date > date.today()]
    elif status == "completed":
        filters = [Campaign._start_date < date.today(), Campaign._end_date < date.today()]

    if location_id:
        location_id = int(location_id) if location_id.isdecimal() else None
        filters.append(Campaign.location_id == location_id)

    if is_registered:
        campaigns_participant = db.session.query(CampaignParticipant.campaign_id) \
            .filter_by(user_id=user_id).all()
        campaigns_id = [campaign_id[0] for campaign_id in campaigns_participant]
        
        if is_registered == "true":
            filters.append(Campaign.id.in_(campaigns_id))
        elif is_registered == "false":
            filters.append(Campaign.id.notin_(campaigns_id))
    
    return filters

def get_campaign_query(request):
    query = []
    query.append(request.args.get("page"))
    query.append(request.args.get("status"))
    query.append(request.args.get("location_id"))
    query.append(request.args.get("is_registered"))
    query.append(request.user.get("uid"))
    query.append(request.args.get("search"))

    return query

@app.route("/users/<string:id>/campaigns", methods=["GET"])
@authenticated_only
def get_registred_campaigns(id):
    try:
        auth.get_user(uid=id)
    except auth.UserNotFoundError:
        return {"message": f"User with id {id} doesn't exist"}, 404

    campaigns_participant = db.session.query(CampaignParticipant.campaign_id) \
        .filter_by(user_id=id).all()
    campaigns_id = [campaign_id[0] for campaign_id in campaigns_participant]

    page = request.args.get("page")
    status = request.args.get("status")
    location_id = request.args.get("location_id")
    orders = Campaign._end_date.desc(), Campaign._start_date.asc()

    if page is not None and page.isdecimal():
        campaigns = db.session.query(Campaign) \
            .filter(*get_campaign_filters(status, location_id), Campaign.id.in_(campaigns_id)) \
            .order_by(*orders) \
            .paginate(page=int(page), per_page=5, error_out=False)
    else:
        campaigns = db.session.query(Campaign) \
            .filter(*get_campaign_filters(status, location_id), Campaign.id.in_(campaigns_id)) \
            .order_by(*orders).all()

    user_id = request.user.get("user_id")
    return {"data": Campaign.serialize_list(user_id, campaigns)}, 200

@app.route("/campaigns", methods=["GET"])
@authenticated_only
def get_campaigns():
    page, status, location_id, is_registered, user_id, search = get_campaign_query(request)
    orders = Campaign._end_date.desc(), Campaign._start_date.asc()

    keyword_search = []
    if search:
        keyword_search = [Campaign.name.ilike(f'%{keyword}%') for keyword in search.split()]

    if page is not None and page.isdecimal():
        campaigns = db.session.query(Campaign) \
            .filter(*keyword_search, *get_campaign_filters(status, location_id, user_id, is_registered)) \
            .order_by(*orders) \
            .paginate(page=int(page), per_page=5, error_out=False)
    else:
        campaigns = db.session.query(Campaign) \
            .filter(*keyword_search, *get_campaign_filters(status, location_id, user_id, is_registered)) \
            .order_by(*orders).all()

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

    if not submission_url:
        return {"message": "Submission url are required"}, 400
    
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
    
    user_id = request.user.get("user_id")
    return {"data": campaign_detail.serialize(user_id, id)}, 200

@app.route("/campaigns/<int:id>/participants", methods=["GET"])
@authenticated_only
def get_campaign_participants(id):
    campaign = db.session.get(Campaign, id)
    if not campaign:
        return {"message": f"Campaign with id {id} doesn't exist"}, 404
    
    campaign_winners = db.session.query(CampaignWinner) \
        .filter_by(campaign_id=id) \
        .order_by(CampaignWinner.position.asc()).all()
    campaign_winners_id = [winner.user_id for winner in campaign_winners]

    campaign_participants = db.session.query(CampaignParticipant) \
        .filter(CampaignParticipant.user_id.notin_(campaign_winners_id), CampaignParticipant.campaign_id==id) \
        .order_by(CampaignParticipant.created_at.asc()).all()
    
    return {"data": [{"winners": campaign_winners}, {"other_participants": campaign_participants}]}, 200

@app.route("/campaign-locations", methods=["GET"])
@authenticated_only
def get_campaign_locations():
    locations = db.session.query(CampaignLocation) \
        .order_by(CampaignLocation.name.asc()).all()
    return {"data": locations}, 200

@app.route("/campaign-categories/<int:id>/campaigns", methods=["GET"])
@authenticated_only
def get_campaigns_by_category(id):
    category = db.session.get(CampaignCategory, id)
    if not category:
        return {"message": f"Category with id {id} doesn't exist"}, 404
    
    page, status, location_id, is_registered, user_id, search = get_campaign_query(request)
    orders = Campaign._end_date.desc(), Campaign._start_date.asc()

    keyword_search = []
    if search:
        keyword_search = [Campaign.name.ilike(f'%{keyword}%') for keyword in search.split()]

    if page is not None and page.isdecimal():
        campaigns = db.session.query(Campaign) \
            .filter(*keyword_search, *get_campaign_filters(status, location_id, user_id, is_registered), Campaign.category_id==id) \
            .order_by(*orders) \
            .paginate(page=int(page), per_page=5, error_out=False)
    else:
        campaigns = db.session.query(Campaign) \
            .filter(*keyword_search, *get_campaign_filters(status, location_id, user_id, is_registered), Campaign.category_id==id) \
            .order_by(*orders).all()
    
    return {"data": Campaign.serialize_list(user_id, campaigns)}, 200

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
