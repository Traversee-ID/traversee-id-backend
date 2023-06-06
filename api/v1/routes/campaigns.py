from datetime import date
from firebase_admin import auth
from flask import Blueprint, request
from ..extensions import db
from ..decorator import authenticated_only
from ..models.campaigns import *

campaigns = Blueprint("campaigns", __name__)

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

@campaigns.route("/users/<string:id>/campaigns", methods=["GET"])
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

    user_id = request.user.get("uid")
    return {"data": Campaign.serialize_list(user_id, campaigns)}, 200

@campaigns.route("/campaigns", methods=["GET"])
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

    user_id = request.user.get("uid")
    return {"data": Campaign.serialize_list(user_id, campaigns)}, 200

@campaigns.route("/campaigns/<int:id>", methods=["GET"])
@authenticated_only
def get_campaign(id):
    campaign = db.session.get(Campaign, id)
    if not campaign:
        return {"message": f"Campaign with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("uid")
    return {"data": campaign.serialize(user_id)}, 200

@campaigns.route("/campaigns/<int:id>/registrations", methods=["POST"])
@authenticated_only
def register_campaign(id):
    campaign = db.session.get(Campaign, id)
    if not campaign:
        return {"message": f"Campaign with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("uid")
    campaign_participant = db.session.query(CampaignParticipant) \
        .filter_by(user_id=user_id, campaign_id=campaign.id).first()
    
    if campaign_participant:
        return {"message": f"User {user_id} is already registered"}, 409
    
    campaign_participant = CampaignParticipant(user_id=user_id, campaign_id=campaign.id)
    db.session.add(campaign_participant)
    db.session.commit()

    return {"data": campaign_participant}, 201

@campaigns.route("/campaigns/<int:id>/submissions", methods=["POST"])
@authenticated_only
def submit_campaign_tasks(id):
    campaign = db.session.get(Campaign, id)
    if not campaign:
        return {"message": f"Campaign with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("uid")
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

@campaigns.route("/campaigns/<int:id>/details", methods=["GET"])
@authenticated_only
def get_campaign_detail(id):
    campaign_detail = db.session.query(CampaignDetails) \
        .filter_by(campaign_id=id).first()
    if not campaign_detail:
        return {"message": f"Campaign with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("uid")
    return {"data": campaign_detail.serialize(user_id, id)}, 200

@campaigns.route("/campaigns/<int:id>/participants", methods=["GET"])
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

@campaigns.route("/campaign-locations", methods=["GET"])
@authenticated_only
def get_campaign_locations():
    locations = db.session.query(CampaignLocation) \
        .order_by(CampaignLocation.name.asc()).all()
    return {"data": locations}, 200

@campaigns.route("/campaign-categories/<int:id>/campaigns", methods=["GET"])
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

@campaigns.route("/campaign-categories", methods=["GET"])
@authenticated_only
def get_campaign_categories():
    categories = db.session.query(CampaignCategory) \
        .order_by(CampaignCategory.name.asc()).all()
    return {"data": categories}, 200

@campaigns.route("/campaign-categories/<int:id>", methods=["GET"])
@authenticated_only
def get_campaign_category(id):
    category = db.session.get(CampaignCategory, id)
    if not category:
        return {"message": f"Category with id {id} doesn't exist"}, 404
    return {"data": category}, 200