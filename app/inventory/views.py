import csv
import io
import json
import os
import logging
from typing import Dict, List
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
import sqlalchemy
from app import db
from app.inventory.models import Inventory
from app.inventory.models import Device
from werkzeug.utils import secure_filename
from app.core.models.bootstrap import Bootstrap
from app.core.helpers import configure_logging, dir_path, json_to_csv
from nornir import InitNornir
from .forms import InventoryForm, UploadForm
from app.core.exceptions import ValidationException


inventory_bp = Blueprint('inventory_bp', __name__, template_folder='templates')
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'txt', 'csv'}
DEFAULT_DEVICE_ATTR = [
    'hostname','platform','port','custom','user_id','id',
    'date_created','date_modified'
]
OMITTED_DEVICE_ATTR = ['groups','user_id','_sa_instance_state']
CFG_FILE = f'{dir_path}/config.yaml'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Check if it exists if not create it after validate its attributes.
def create_inventory(name, inventory, msg):
    try:
        # Validate data with Device model and return a list of Device __iter__() dicts.
        inventory = Bootstrap.import_inventory_text(inventory)
        # Convert to csv this json-like list
        inventory_csv = json_to_csv(inventory)
    except ValidationException as e:
        flash(f'{e.message}', category='error')
        return redirect(url_for('inventory_bp.home'))
    except AttributeError:
        flash('Bad inventory', category='error')
        return redirect(url_for('inventory_bp.home'))
    inventory_exists = Inventory.query.filter_by(data=inventory_csv, user_id=current_user.id).first() 
    name_exists = Inventory.query.filter_by(name=name, user_id=current_user.id).first()
    if inventory_exists:
        flash(f'Inventory {inventory_exists.name} has the same data. Invetory not created!', category='warning')
    elif name_exists:
        flash('Inventory name already exists! Use a different name', category='error')
    else:
        if len(inventory_csv) < 1 or name=='':
            flash('Inventory does not have name or is empty', category='error')
        else:
            new_inventory = Inventory(
                name=name,
                data=inventory_csv, 
                user_id=current_user.id
            )
            for device in inventory:
                try:
                    d,_ = Device.get_or_create(db.session, user_id=current_user.id, **device)
                except sqlalchemy.exc.InvalidRequestError as e:
                    custom = {k:v for k,v in device.items() if k not in DEFAULT_DEVICE_ATTR}
                    device = {k:v for k,v in device.items() if k in DEFAULT_DEVICE_ATTR}
                    device['custom'] = json.dumps(custom)
                    d,_ = Device.get_or_create(db.session, user_id=current_user.id, **device)
                new_inventory.devices.append(d)
            db.session.add(new_inventory)
            db.session.commit()
            flash(f'{msg}', category='success')
            return redirect(url_for('inventory_bp.home'))

def csv_text_to_devices_db(devices: str) -> List:
    devices = csv.DictReader(io.StringIO(devices))
    result = []
    for device in devices:
        customs = {k:v for k,v in device.items() if k not in DEFAULT_DEVICE_ATTR}
        device = {k:v for k,v in device.items() if k in DEFAULT_DEVICE_ATTR}
        device['custom'] = json.dumps(customs) # aqui device es un dict preparado para subir por SQL
        result.append(device) 
    return result # lista de devices SQL

def devices_db_dict_to_csv_text(devices: List[Dict]) -> str:
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
    result = []
    # This line converts a device SQLAlchemi object row to device dict.
    row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}
    # Gets a List of device dictionaries
    devices  = [row2dict(device) for device in devices]
    for device in devices:
        if 'custom' in device.keys():
            if device['custom'] != 'None':
                device['custom'] = json.loads(device['custom'])
        result.append({k:v for k,v in generator(device)})
    devices = result
    file = io.StringIO()
    keys = devices.keys() if type(devices) != list else devices[0].keys()
    dict_writer = csv.DictWriter(file, fieldnames=keys)
    dict_writer.writeheader()
    dict_writer.writerows([devices]) if type(devices) != list else dict_writer.writerows(devices)
    output = file.getvalue()
    return output
    
@inventory_bp.route('/', methods=['GET', 'POST'])
@login_required
def home():
    inventory_form = InventoryForm()
    upload_form = UploadForm()
    # POST de csv textArea
    if inventory_form.validate_on_submit():
        inventory = inventory_form.inventory.data
        name = inventory_form.name.data
        # validate data and submit to db
        create_inventory(name, inventory, f'Inventory {name} created!')
    # POST de upload csv
    elif upload_form.validate_on_submit():
        filename = secure_filename(upload_form.file.data.filename)
        if filename == '':
            flash("You haven't selected any file", category='warning')
            return redirect(request.url)
        if allowed_file(filename):
            final_filename = os.path.join(
                current_app.config['UPLOAD_FOLDER'], 
                current_app.config['INVENTORY_FILE'])
            upload_form.file.data.save(final_filename)
            with open(final_filename) as f:
                inventory = f.read()
            name = filename
             # validate data and submit to db
            create_inventory(name, inventory, f'File {name} uploaded!')
        else:
            flash('File type must be csv or txt', category='error')
    # GET
    return render_template("inventory/home.html",
                            user=current_user, 
                            inventory_form=inventory_form,
                            upload_form=upload_form
                            )

@inventory_bp.route('/inventory/<name>', methods=['POST', 'GET', 'DELETE'])
@login_required
def inventory(name):
    if request.method == 'GET':
        inventory = Inventory.query.filter_by(name=name, user_id=current_user.id).first() 
        if inventory:
            # get Device.__iter__() dict for every device in a dict container.
            return render_template(
                "inventory/inventory.html",
                inventory=inventory,
                user=current_user,
            )
    if request.method == 'POST':
        inventory = Inventory.query.filter_by(name=name, user_id=current_user.id).first()
        if inventory:
            data = request.form.get('data')
            if inventory.data != data:
                inventory.data = data
                db.session.commit()
                flash('Inventory modified!', category='success')
            else:
                flash('Nothing has been modified!', category='info')
            return redirect(url_for('inventory_bp.inventory', name=name))
    if request.method == 'DELETE':
        data = json.loads(request.data) # add data in a python dict
        inventory_id = data['inventoryId']
        inventory = Inventory.query.get(inventory_id)
        if inventory:
            if inventory.user_id == current_user.id:
                db.session.delete(inventory)
                db.session.commit()
                flash(f'Inventory {inventory.name} deleted!', category='success')
        return jsonify({})

    redirect(url_for('inventory_bp.home'))

@inventory_bp.route('/v1/inventory/<name>', methods=['POST', 'GET', 'DELETE', 'PUT'])
@login_required
def inventory_api(name):
    if request.method == 'GET':
        inventory = Inventory.query.filter_by(name=name, user_id=current_user.id).first() 
        if inventory:
            # get Device.__iter__() dict for every device in a dict container.
            devices = inventory.devices
            devices_csv = devices_db_dict_to_csv_text(devices)
            values = Bootstrap.import_inventory_text(devices_csv)
            json_data = json.dumps(values)
            return json_data
    if request.method == 'PUT':
        data = json.loads(request.data) # add data in a python dict
        data = json_to_csv(list(data))
        inventory = Inventory.query.filter_by(name=name, user_id=current_user.id).first()
        if inventory:
            if inventory.user_id == current_user.id:
                if inventory.data != data:
                    inventory.data = data
                    db.session.commit()
                    flash('Inventory modified!', category='success')
                else:
                    flash('Nothing has been modified!', category='info')
    if request.method == 'POST':
        inventory = Inventory.query.filter_by(name=name, user_id=current_user.id).first()
        if inventory:
            data = request.form.get('data')
            if inventory.data != data:
                inventory.data = data
                db.session.commit()
                flash('Inventory modified!', category='success')
            else:
                flash('Nothing has been modified!', category='info')
            return inventory.data, 200
    if request.method == 'DELETE':
        data = json.loads(request.data) # add data in a python dict
        inventory_id = data['inventoryId']
        inventory = Inventory.query.get(inventory_id)
        if inventory:
            if inventory.user_id == current_user.id:
                db.session.delete(inventory)
                db.session.commit()
        return jsonify({})

    redirect(url_for('inventory_bp.home'))

@inventory_bp.route('/v1/device/', methods=['POST', 'GET', 'DELETE', 'PUT'])
@login_required
def device():
    if request.method == 'PUT':
        data = json.loads(request.data) # add data in a python dict
        print(data)
        return jsonify({})
        data = json_to_csv(list(data))
        device = Device.query.filter_by(data, user_id=current_user.id).first()
        if inventory:
            if inventory.user_id == current_user.id:
                if inventory.data != data:
                    inventory.data = data
                    db.session.commit()
                    flash('Inventory modified!', category='success')
                else:
                    flash('Nothing has been modified!', category='info')
