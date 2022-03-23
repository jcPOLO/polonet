from app import db
from flask_login import UserMixin
from app.models import Base
from app.job.models import Job


class User(Base, UserMixin):
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150))
    inventories = db.relationship("Inventory")  # 1:N
    devices = db.relationship("Device")  # 1:N
    jobs = db.relationship("Job")  # 1:N
