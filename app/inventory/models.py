from app import db
from app.models import Base


inventory_device = db.Table('devices',
    db.Column('inventory_id', db.Integer, db.ForeignKey("inventory.id"), primary_key=True),
    db.Column('device_id', db.Integer, db.ForeignKey("device.id"), primary_key=True)
)

# TODO: When a device does not have associated any inventory, we could delete the device.
class Device(Base):
    hostname = db.Column(db.String(39), nullable=False)
    platform = db.Column(db.String(20))
    port = db.Column(db.Integer)
    custom = db.Column(db.JSON)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False) # 1:N


class Inventory(Base):
    name = db.Column(db.String(60), nullable=False)
    slug = db.Column(db.String(60), nullable=False)
    data = db.Column(db.String(10000))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False) # 1:N
    # jobs = db.relationship('Job') # 1:N
    devices = db.relationship('Device', secondary=inventory_device, backref='devices')

    __table_args__ = (
        # this can be db.PrimaryKeyConstraint if you want it to be a primary key
        db.UniqueConstraint('user_id', 'slug', name='unique_inventory_name'),
    )
