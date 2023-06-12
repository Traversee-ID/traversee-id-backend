from dataclasses import dataclass
from ..extensions import db

@dataclass
class Tourism(db.Model):
    __tablename__ = "tourisms"

    category_name: str
    location_name: str

    id: str = db.Column(db.String(30), primary_key=True)
    name: str = db.Column(db.String, nullable=False)
    image_url: str = db.Column(db.String)
    location_id = db.Column(db.Integer, db.ForeignKey('tourism_locations.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('tourism_categories.id'), nullable=False)
    description = db.relationship("TourismDetail", uselist=False)

    @property
    def category_name(self):
        return db.session.get(TourismCategory, self.category_id).name
    
    @property
    def location_name(self):
        return db.session.get(TourismLocation, self.location_id).name
    
    def serialize(self, user_id):
        tourism = db.session.query(TourismFavorite) \
            .filter_by(user_id=user_id, tourism_id=self.id).first()
        return {
            "tourism": self,
            "is_favorite": tourism != None
        }
    
    @staticmethod
    def serialize_list(user_id, tourisms):
        return [tourism.serialize(user_id) for tourism in tourisms]

@dataclass
class TourismDetail(db.Model):
    __tablename__ = "tourism_details"

    tourism_id = db.Column(db.String(30), db.ForeignKey('tourisms.id'), primary_key=True)
    description: str = db.Column(db.Text)

@dataclass
class TourismFavorite(db.Model):
    __tablename__ = "tourism_favorites"

    tourism_id = db.Column(db.String(30), db.ForeignKey('tourisms.id'), primary_key=True)
    user_id = db.Column(db.String, primary_key=True)

@dataclass
class TourismUserClick(db.Model):
    __tablename__ = "tourism_user_clicks"

    tourism_id: str = db.Column(db.String(30), db.ForeignKey('tourisms.id'), primary_key=True)
    user_id: str = db.Column(db.String, primary_key=True)
    total_click: int = db.Column(db.Integer, nullable=False)

@dataclass
class TourismLocation(db.Model):
    __tablename__ = "tourism_locations"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    tourisms = db.relationship("Tourism", uselist=True)

@dataclass
class TourismCategory(db.Model):
    __tablename__ = "tourism_categories"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), unique=True, nullable=False)
    image_url: str = db.Column(db.String(150), nullable=False)
    tourisms = db.relationship("Tourism", uselist=True)
