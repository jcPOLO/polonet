from app import db
from app.models import Base


inventory_device = db.Table('devices',
    db.Column('inventory_id', db.Integer, db.ForeignKey("inventory.id"), primary_key=True),
    db.Column('device_id', db.Integer, db.ForeignKey("device.id"), primary_key=True)
)

class Inventory(Base):
    name = db.Column(db.String(150), unique=True)
    data = db.Column(db.String(10000))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id")) # 1:N
    devices = db.relationship('Device', secondary=inventory_device, backref='devices')


class Device(Base):
    hostname = db.Column(db.String(150), unique=True)
    platform = db.Column(db.String(150))
    port = db.Column(db.Integer)
    custom = db.Column(db.JSON)
