from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Base(db.Model):

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.now())
    date_modified = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())


class User(Base, UserMixin):
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    inventories = db.relationship('Inventory') # 1:N


class Inventory(Base):
    name = db.Column(db.String(150), unique=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id")) # 1:N


class Device(Base):
    hostname = db.Column(db.String(150), unique=True)
    platform = db.Column(db.String(150))
    site = db.Column(db.String(150))
    company = db.Column(db.String(150))
