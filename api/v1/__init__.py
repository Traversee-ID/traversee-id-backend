from flask import Blueprint
from .routes import campaigns, forums, open_trips, tourisms, profiles

v1 = Blueprint("v1", __name__)
v1.register_blueprint(campaigns.campaigns)
v1.register_blueprint(forums.forums)
v1.register_blueprint(open_trips.open_trip)
v1.register_blueprint(profiles.profiles)
v1.register_blueprint(tourisms.tourisms)