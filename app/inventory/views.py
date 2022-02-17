import json
import os
import logging
import time
from typing import Dict, List
from flask import Blueprint, render_template, request, flash, redirect, session, url_for, jsonify, current_app, Response
from flask_login import login_required, current_user
from app import db
from app.inventory.schemas import InventorySchema, DeviceSchema
from app.inventory.models import Device, Inventory
from werkzeug.utils import secure_filename
from app.core.helpers import dir_path, json_to_csv
from app.core.exceptions import ValidationException
from .forms import InventoryForm, UploadForm
from app.core.core import Core


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
        inventory_schema = InventorySchema()
        inventory = inventory_schema.load({
            'name': name, 
            'data': inventory, 
            'user_id': current_user.id
        })
        flash(f'{msg}', category='success')
    except ValidationException as e:
        flash(f'{e.message}', category='error')
        return redirect(url_for('inventory_bp.inventories'))
    except AttributeError:
        flash('Bad inventory', category='error')
        return redirect(url_for('inventory_bp.inventories'))
    return redirect(url_for('inventory_bp.inventories'))

@inventory_bp.route('/', methods=['GET', 'POST'])
@login_required
def home():
    # GET
    num_inventories = Inventory.query.filter_by(user_id=current_user.id).count()
    num_devices = Device.query.filter_by(user_id=current_user.id).count()
    return render_template("inventory/home.html",
                            user=current_user,
                            num_inventories=num_inventories,
                            num_devices=num_devices,
                            )

@inventory_bp.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventories():
    inventory_form = InventoryForm()
    upload_form = UploadForm()
    # POST de csv textArea
    if inventory_form.validate_on_submit():
        inventory = inventory_form.inventory.data
        name = inventory_form.name.data
        # validate data and submit to db
        create_inventory(name, inventory, f'Inventory {name} created!')
    # POST de upload csv
    if upload_form.validate_on_submit():
        filename = secure_filename(upload_form.file.data.filename)
        if filename == '':
            message = "You haven't selected any file"
            flash(f'{message}', category='warning')
            return redirect(request.url)
        if not allowed_file(filename):
            message = 'File type must be csv or txt'
            flash(message, category='error')
            return redirect(request.url)
        final_filename = os.path.join(
            current_app.config['UPLOAD_FOLDER'], 
            current_app.config['INVENTORY_FILE'])
        upload_form.file.data.save(final_filename)
        with open(final_filename) as f:
            inventory = f.read()
        name = filename
        # validate data and submit to db
        create_inventory(name, inventory, f'File {name} uploaded!')
    # GET
    return render_template("inventory/inventories.html",
                            user=current_user, 
                            inventory_form=inventory_form,
                            upload_form=upload_form
                            ) 

@inventory_bp.route('/inventory/<slug>', methods=['POST', 'GET', 'DELETE'])
@login_required
def inventory(slug):
    # GET
    if request.method == 'GET':
        inventory = Inventory.query.filter_by(slug=slug, user_id=current_user.id).first() 
        if inventory:
            # get Device.__iter__() dict for every device in a dict container.
            return render_template(
                "inventory/inventory.html",
                inventory=inventory,
                user=current_user,
            )
    # TODO: Need to think how to accomplish this csv inventory modify thing
    # POST
    if request.method == 'POST':
        inventory_schema = InventorySchema()
        inventory = Inventory.query.filter_by(slug=slug, user_id=current_user.id).first()
        if inventory:
            data = request.form.get('data')
            if inventory.data != data:
                inventory.data = data
                db.session.commit()
                flash('Inventory modified!', category='success')
            else:
                flash('Nothing has been modified!', category='info')
            return redirect(url_for('inventory_bp.inventories', slug=slug))
    # DELETE
    if request.method == 'DELETE':
        data = json.loads(request.data) # add data in a python dict
        slug = data['inventorySlug']
        inventory = Inventory.query.filter_by(slug=slug, user_id=current_user.id).first()
        if inventory:
            if inventory.user_id == current_user.id:
                db.session.delete(inventory)
                db.session.commit()
                flash(f'Inventory {inventory.name} deleted!', category='success')
        return jsonify({}), 200

    redirect(url_for('inventory_bp.inventories'))

@inventory_bp.route('/v1/inventory/<slug>', methods=['POST', 'GET', 'DELETE', 'PUT'])
@login_required
def inventory_api(slug):
    device_schema = DeviceSchema(many=True)
    # GET
    if request.method == 'GET':
        inventory = Inventory.query.filter_by(slug=slug, user_id=current_user.id).first() 
        if inventory:
            devices = inventory.devices
            devices = device_schema.dump(devices)
            return jsonify(devices), 200
        return jsonify({}), 400
    # PUT
    if request.method == 'PUT':
        data = json.loads(request.data) # add data in a python dict
        # data = json_to_csv(list(data))
        inventory = Inventory.query.filter_by(slug=slug, user_id=current_user.id).first()
        if inventory:
            if inventory.user_id == current_user.id:
                devices = inventory.devices
                devices = device_schema.dump(devices)
                if data == devices:
                    flash('Nothing has been modified!', category='info')
                    return jsonify(devices), 304
                flash('Inventory modified!', category='success')
                return jsonify(data), 200
                temp_inventory = Inventory()
                db.session.commit()
                flash('Inventory modified!', category='success')
            else:
                flash('Nothing has been modified!', category='info')
    # POST
    if request.method == 'POST':
        inventory = Inventory.query.filter_by(slug=slug, user_id=current_user.id).first()
        if inventory:
            data = request.form.get('data')
            if inventory.data != data:
                inventory.data = data
                db.session.commit()
                flash('Inventory modified!', category='success')
            else:
                flash('Nothing has been modified!', category='info')
            return inventory.data, 200
    # DELETE
    if request.method == 'DELETE':
        data = json.loads(request.data) # add data in a python dict
        slug = data['inventorySlug']
        inventory = Inventory.query.filter_by(slug=slug, user_id=current_user.id).first()
        if inventory:
            if inventory.user_id == current_user.id:
                db.session.delete(inventory)
                db.session.commit()
        return jsonify({})

    redirect(url_for('inventory_bp.inventory'))


