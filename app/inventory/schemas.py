import csv
import io
import json
from typing import Dict, List
from marshmallow import post_dump, post_load, pre_dump, pre_load, validates
from app import ma
from app.core.models.device import Device as NornirDevice
from app.core.models.bootstrap import Bootstrap 
from app.core.exceptions import ValidationException
from app.inventory.models import Inventory, Device
from app.core.helpers import json_to_csv
from app import db
from flask_login import current_user
from slugify import slugify


DEFAULT_DEVICE_ATTR = [
    'hostname','platform','port','custom','user_id','id',   
]
OMITTED_DEVICE_ATTR = [
    'groups','_sa_instance_state','date_created','date_modified'
]


class DeviceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Device
        include_relationships = True
        include_fk = True
        fields = ("hostname", "platform", "port", "custom", "date_modified", "date_created")
    
    hostname = ma.auto_field()
    platform = ma.auto_field()
    port = ma.auto_field()
    custom = ma.auto_field()


    @pre_dump
    def device_dump(self, data, **kwargs):
        a = data
        return a

    @post_dump
    def device_post(self, data, **kwargs):
        def generator(device: dict) -> str:
            for k, v in device.items():
                # remove empty attributes
                if v:
                    # custom keys inside data are shown, data key is not shown.
                    if k == 'custom':
                        if device[k] != 'None':
                            for a, b in device[k].items():
                                yield a, b
                        else:
                            pass
                    # do not return groups column either
                    elif k in OMITTED_DEVICE_ATTR:
                        pass
                    else:
                        yield k, v
        device = data.copy()
        if device['custom'] != 'None':
            device['custom'] = json.loads(device['custom'])
            print(device)
        data = {k:v for k,v in generator(device)}
        return data

    @pre_load
    def device_db(self, data, **kwargs):
        custom = {k:v for k,v in data.items() if k not in DEFAULT_DEVICE_ATTR and k not in OMITTED_DEVICE_ATTR}
        device = {k:v for k,v in data.items() if k in DEFAULT_DEVICE_ATTR }
        device['custom'] = json.dumps(custom)
        return device
        # d,_ = Device.get_or_create(db.session, user_id=current_user.id, **device)

    @validates('hostname')
    def validate_hostname(self,a):
        return NornirDevice.validate_hostname(a)
    
    @validates('port')
    def validate_port(self,a):
        return NornirDevice.validate_port(a)

    @validates('platform')
    def validate_platform(self,a):
        return NornirDevice.validate_platform(a)

    @post_load
    def create_devices(self, data, **kwargs):
        try:
            d,_ = Device.get_or_create(db.session, user_id=current_user.id, **data)
        except Exception as e:
            raise ValidationException("fail-config", e.error)
        return d


class InventorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Inventory
        include_relationships = True
        include_fk = True
        fields = ("name", "data", "user_id", "date_created", "date_modified")

    devices = []
    name = ma.auto_field()
    data = ma.auto_field()
    user_id = ma.auto_field()
    devices = ma.auto_field()


    @pre_load 
    def inventory_db(self, data, **kwargs):
        self.devices = Bootstrap.import_inventory_text(data['data'].lower())
        csv = json_to_csv(self.devices)
        data['data'] = csv
        return data
    
    @validates('name')
    def validate_name(self, a):
        if not a:
            message = 'Inventory does not have name'
            raise ValidationException('fail-config', message)
        exists = Inventory.query.filter_by(slug=slugify(a), user_id=current_user.id).first()
        if a in '< > | { / } \ , .'.split() :
                message = "name '{}' is not a valid. ".format(a)
                raise ValidationException("fail-config", message)
        if exists:
            message = "Inventory named '{}' already exists! Use a different name.".format(a)
            raise ValidationException('fail-config', message)
        else:
            return a


    @validates('data')
    def validate_data(self, a):
        if not a:
            message = 'Inventory is empty.'
            raise ValidationException('fail-config', message)
        exists = Inventory.query.filter_by(data=a, user_id=current_user.id).first()
        if exists:
            message = "Inventory named '{}' has the same data. Invetory not created!".format(exists.name)
            raise ValidationException('fail-config', message)
        else:
            return a

    @post_load
    def create_inventory(self, data, **kwargs):
        device_schema = DeviceSchema()
        data['slug'] = slugify(data['name'])
        new_inventory,_ = Inventory.get_or_create(db.session, **data)
        for device in self.devices:
            try:
                device = device_schema.load(device)
            except Exception as e:
                raise ValidationException("fail-config", e.error)
            new_inventory.devices.append(device) 
        db.session.add(new_inventory)
        db.session.commit()
        return new_inventory
