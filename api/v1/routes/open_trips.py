from datetime import datetime
from flask import Blueprint, request
from ..extensions import db
from ..decorator import authenticated_only
from ..models.open_trips import *

open_trip = Blueprint("open_trip", __name__)

@open_trip.route('/open-trips')
@authenticated_only
def get_trips():
    page = request.args.get("page")

    if page is not None and page.isdecimal():
        trips = db.session.query(OpenTrip) \
            .order_by(OpenTrip.regis_deadline.desc()) \
            .paginate(page=int(page), per_page=10, error_out=False).items
    else:
        trips = db.session.query(OpenTrip).order_by(OpenTrip.regis_deadline.desc()).all()
    
    return {"data": trips}, 200

@open_trip.route('/open-trips', methods = ['POST'])
@authenticated_only
def create_trip():
    title = request.json.get("title")
    description = request.json.get("description")
    price = request.json.get("price")
    organizer = request.json.get("organizer")
    start_str = request.json.get("trip_start")
    end_str = request.json.get("trip_end")
    deadline_str = request.json.get("regis_deadline")
    phone_number = request.json.get("phone_number")

    if not title or not description or not price or not organizer or not start_str or not end_str or not deadline_str or not phone_number:
        return {"message": "Please input all required data"}, 400
    
    trip_start = datetime.strptime(start_str, "%Y-%m-%d")
    trip_end = datetime.strptime(end_str, "%Y-%m-%d")
    regis_deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
    trip = OpenTrip(title=title, description=description, price=price, organizer=organizer, trip_start=trip_start, trip_end=trip_end, regis_deadline=regis_deadline, phone_number=phone_number)
    db.session.add(trip)
    db.session.commit()

    return {"data": trip}, 200

@open_trip.route('/open-trips/<int:id>')
@authenticated_only
def get_trip(id):
    trip = db.session.get(OpenTrip, id)
    if not trip:
        return {"message": f"Open trip with id {id} doesn't exist"}, 404
    
    return {"data": trip}, 200

@open_trip.route('/open-trips/<int:id>', methods=["DELETE"])
@authenticated_only
def delete_trip(id):
    trip = db.session.get(OpenTrip, id)
    if not trip:
        return {"message": f"Open trip with id {id} doesn't exist"}, 404
    
    db.session.delete(trip)
    db.session.commit()
    return {"message": f"Open trip with id {id} deleted"}, 200

@open_trip.route('/open-trips/<int:id>/destinations')
@authenticated_only
def get_destinations(id):
    trip = db.session.get(OpenTrip, id)
    if not trip:
        return {"message": f"Open trip with id {id} doesn't exist"}, 404

    destinations = db.session.query(TripDestination).filter_by(trip_id=trip.id).all()
    
    return {"data": destinations}, 200

@open_trip.route('/open-trips/<int:id>/destinations' , methods=["POST"])
@authenticated_only
def post_destination(id):
    name = request.json.get("name")
    location_name = request.json.get("location_name")
    image_url = request.json.get("image_url")
    category = request.json.get("category")
    trip_id = id

    trip = db.session.get(OpenTrip, id)
    if not trip:
        return {"message": f"Open trip with id {id} doesn't exist"}, 404
    
    if not name or not location_name:
        return {"message": "Name and location are required"}, 400
    
    destination = TripDestination(name=name, location_name=location_name, image_url=image_url, category=category, trip_id=trip_id)
    db.session.add(destination)
    db.session.commit()
    
    return {"data": destination}, 200

@open_trip.route('/open-trips/<int:id>/destinations/<int:destination_id>', methods=["DELETE"])
@authenticated_only
def delete_destination(id, destination_id):
    trip = db.session.get(OpenTrip, id)
    if not trip:
        return {"message": f"Open trip with id {id} doesn't exist"}, 404

    destination = db.session.get(TripDestination, destination_id)
    if not destination:
        return {"message": f"Destination with id {destination_id} doesn't exist"}, 404
    
    db.session.delete(destination)
    db.session.commit()
    return {"message": f"Destination with id {destination_id} deleted"}, 200
    