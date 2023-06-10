import requests
from flask import Blueprint, request
from os import getenv
from ..extensions import db
from ..decorator import authenticated_only
from ..models.tourisms import *

tourisms = Blueprint("tourisms", __name__)

def get_tourism_filters(location_id, category_id, is_favorite, user_id):
    filters = []

    if location_id:
        location_id = int(location_id) if location_id.isdecimal() else None
        filters.append(Tourism.location_id == location_id)

    if category_id:
        category_id = int(category_id) if category_id.isdecimal() else None
        filters.append(Tourism.category_id == category_id)

    if is_favorite:
        tourism_favorites = db.session.query(TourismFavorite.tourism_id) \
            .filter_by(user_id=user_id).all()
        tourism_id = [tourism[0] for tourism in tourism_favorites]
        
        if is_favorite == "true":
            filters.append(Tourism.id.in_(tourism_id))
        elif is_favorite == "false":
            filters.append(Tourism.id.notin_(tourism_id))
    
    return filters

def get_tourism_query(request):
    query = []
    query.append(request.args.get("page"))
    query.append(request.args.get("location_id"))
    query.append(request.args.get("category_id"))
    query.append(request.args.get("is_favorite"))
    query.append(request.user.get("uid"))
    query.append(request.args.get("search"))

    return query

@tourisms.route("/tourisms", methods=["GET"])
@authenticated_only
def get_tourisms():
    page, location_id, category_id, is_favorite, user_id, search = get_tourism_query(request)

    keyword_search = []
    if search:
        keyword_search = [Tourism.name.ilike(f'%{keyword}%') for keyword in search.split()]

    if page is not None and page.isdecimal():
        tourisms = db.session.query(Tourism) \
            .filter(*keyword_search, *get_tourism_filters(location_id, category_id, is_favorite, user_id)) \
            .order_by(Tourism.name.asc()) \
            .paginate(page=int(page), per_page=5, error_out=False)
    else:
        tourisms = db.session.query(Tourism) \
            .filter(*keyword_search, *get_tourism_filters(location_id, category_id, is_favorite, user_id)) \
            .order_by(Tourism.name.asc()).all()

    return {"data": Tourism.serialize_list(user_id, tourisms)}, 200

@tourisms.route("/tourisms/<string:id>", methods=["GET"])
@authenticated_only
def get_tourism(id):
    tourism = db.session.get(Tourism, id)
    if not tourism:
        return {"message": f"Tourism with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("uid")
    return {"data": tourism.serialize(user_id)}, 200

@tourisms.route("/tourisms/<string:id>/favorites", methods=["POST"])
@authenticated_only
def create_tourism_favorite(id):
    tourism = db.session.get(Tourism, id)
    if not tourism:
        return {"message": f"Tourism with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("uid")
    tourism_favorites = db.session.get(TourismFavorite, (tourism.id, user_id))
    if tourism_favorites:
        return {"message": f"Tourism {id} is already in favorites"}, 409
    
    tourism_favorites = TourismFavorite(tourism_id=tourism.id, user_id=user_id)
    db.session.add(tourism_favorites)
    db.session.commit()

    return {"data": tourism.serialize(user_id)}, 200

@tourisms.route("/tourisms/<string:id>/favorites", methods=["DELETE"])
@authenticated_only
def delete_tourism_favorite(id):
    tourism = db.session.get(Tourism, id)
    if not tourism:
        return {"message": f"Tourism with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("uid")
    tourism_favorites = db.session.get(TourismFavorite, (tourism.id, user_id))
    if not tourism_favorites:
        return {"message": f"Tourism {id} isn't a favorite yet"}, 409
    
    db.session.delete(tourism_favorites)
    db.session.commit()

    return {"data": tourism.serialize(user_id)}, 200

@tourisms.route("/tourisms/<string:id>/details", methods=["GET"])
@authenticated_only
def get_tourism_details(id):
    tourism = db.session.get(Tourism, id)
    if not tourism:
        return {"message": f"Tourism with id {id} doesn't exist"}, 404
    
    user_id = request.user.get("uid")
    user_click = db.session.get(TourismUserClick, (tourism.id, user_id))
    if not user_click:
        user_click = TourismUserClick(tourism_id = tourism.id, user_id=user_id, total_click=0)

    user_click.total_click += 1
    db.session.add(user_click)
    db.session.commit()
    
    tourism_details = db.session.get(TourismDetail, tourism.id)
    return {"data": tourism_details}, 200

@tourisms.route("/tourism-categories", methods=["GET"])
@authenticated_only
def get_tourism_categories():
    categories = db.session.query(TourismCategory) \
        .order_by(TourismCategory.name.asc()).all()
    return {"data": categories}, 200

@tourisms.route("/tourism-locations", methods=["GET"])
@authenticated_only
def get_tourism_locations():
    locations = db.session.query(TourismLocation) \
        .order_by(TourismLocation.name.asc()).all()
    return {"data": locations}, 200

@tourisms.route("/tourism-recommendations", methods=["GET"])
@authenticated_only
def get_tourism_recomendations():
    user_id = request.user.get("uid")
    url = getenv("RECOMMENDATIONS_SERVICE")

    response = requests.post(url, json={"user_id": user_id})
    if response.status_code == 200:
        return response.json(), 200
    
    return {"message": "Failed"}, 500