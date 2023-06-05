from flask import Blueprint
from .routes import campaigns, forums, open_trip, tourisms

v1 = Blueprint("v1", __name__)
v1.register_blueprint(campaigns.campaigns)
v1.register_blueprint(forums.forums)
v1.register_blueprint(open_trip.open_trip)
v1.register_blueprint(tourisms.tourisms)