from app import db
from flask_login import UserMixin
from app.models import Base


class User(Base, UserMixin):
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    inventories = db.relationship('Inventory') # 1:N
    devices = db.relationship('Device') # 1:N