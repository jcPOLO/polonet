from app import db
from app.models import Base


class Inventory(Base):
    name = db.Column(db.String(150), unique=True)
    data = db.Column(db.String(10000))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id")) # 1:N


class Device(Base):
    hostname = db.Column(db.String(150), unique=True)
    platform = db.Column(db.String(150))
    site = db.Column(db.String(150))
    company = db.Column(db.String(150))
