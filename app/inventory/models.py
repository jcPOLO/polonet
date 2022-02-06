import json
from marshmallow import post_load, pre_load
from app import db, ma
from app.models import Base
from sqlalchemy.orm import validates


DEFAULT_DEVICE_ATTR = [
    'hostname','platform','port','custom','user_id','id',   
]
OMITTED_DEVICE_ATTR = [
    'groups','_sa_instance_state','date_created','date_modified'
]


inventory_device = db.Table('devices',
    db.Column('inventory_id', db.Integer, db.ForeignKey("inventory.id"), primary_key=True),
    db.Column('device_id', db.Integer, db.ForeignKey("device.id"), primary_key=True)
)

class Inventory(Base):
    name = db.Column(db.String(150))
    data = db.Column(db.String(10000))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id")) # 1:N
    devices = db.relationship('Device', secondary=inventory_device, backref='devices')

    __table_args__ = (
        # this can be db.PrimaryKeyConstraint if you want it to be a primary key
        db.UniqueConstraint('user_id', 'name', name='unique_inventory_name'),
    )


# TODO: When a device does not have associated any inventory, we could delete the device.
class Device(Base):
    hostname = db.Column(db.String(150))
    platform = db.Column(db.String(150))
    port = db.Column(db.Integer)
    custom = db.Column(db.JSON)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id")) # 1:N

class DeviceSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Device
        include_fk = True

    id = ma.auto_field()
    hostname = ma.auto_field()
    platform = ma.auto_field()
    port = ma.auto_field()
    custom = ma.auto_field()
    user_id = ma.auto_field()

    @pre_load
    def device_db(self, data, **kwargs):
        custom = {k:v for k,v in data.items() if k not in DEFAULT_DEVICE_ATTR and k not in OMITTED_DEVICE_ATTR}
        device = {k:v for k,v in data.items() if k in DEFAULT_DEVICE_ATTR }
        device['custom'] = json.dumps(custom)
        return device
        # d,_ = Device.get_or_create(db.session, user_id=current_user.id, **device)

    # @validates('hostname')
    # def validate_hostname(self, key, a):
    #     try:
    #         a = a.strip()
    #         if not a:
    #             message = "hostname '{}' hostname cannot be empty".format(a)
    #             raise ValidationException("fail-config", message)
    #         if is_ip(a):
    #             return a
    #     except AttributeError:
    #         pass
    #     message = "hostname '{}' must be a valid IPv4 address".format(a)
    #     raise ValidationException("fail-config", message)
        # Return a list of dicts from imported csv file
