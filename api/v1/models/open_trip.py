from dataclasses import dataclass
from ..extensions import db

@dataclass
class OpenTrip(db.Model):
    __tablename__ = "open_trips"

    duration: str
    images_url: list
    categories: list

    id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(100), nullable=False)
    description: str = db.Column(db.String, nullable=False)
    price: str = db.Column(db.String(20), nullable=False)
    organizer: str = db.Column(db.String(50), nullable=False)
    trip_start: str = db.Column(db.DateTime, nullable=False)
    trip_end: str = db.Column(db.DateTime, nullable=False)
    regis_deadline: str = db.Column(db.DateTime, nullable=False)
    destinations = db.relationship('TripDestination', uselist=True)
    phone_number: str = db.Column(db.String(15), nullable=False)

    @property
    def duration(self):
        delta = self.trip_end - self.trip_start
        return (str(delta.days) + " days")
    
    @property
    def images_url(self):
        images_url = [r.image_url for r in db.session.query(TripDestination.image_url).filter_by(trip_id=self.id).distinct()]
        return images_url

    @property
    def categories(self):
        categories = [r.category for r in db.session.query(TripDestination.category).filter_by(trip_id=self.id).distinct()]
        return categories
    

@dataclass
class TripDestination(db.Model):
    __tablename__ = "trip_destinations"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(50), nullable=False)
    location_name: str = db.Column(db.String(100))
    image_url: str = db.Column(db.String)
    category: str = db.Column(db.String(20))
    trip_id: int = db.Column(db.Integer, db.ForeignKey('open_trips.id'), nullable=False)