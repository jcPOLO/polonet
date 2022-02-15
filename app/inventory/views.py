import csv
import io
import json
import os
import logging
from typing import Dict, List
from flask import Blueprint, render_template, request, flash, redirect, session, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.inventory.schemas import InventorySchema, DeviceSchema
from app.inventory.models import Device, Inventory
from werkzeug.utils import secure_filename
from app.core.models.bootstrap import Bootstrap
from app.core.helpers import dir_path, json_to_csv
from app.core.exceptions import ValidationException
from .forms import InventoryForm, UploadForm
from app.core.go import Go


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
        return redirect(url_for('inventory_bp.home'))
    except AttributeError:
        flash('Bad inventory', category='error')
        return redirect(url_for('inventory_bp.home'))
    return redirect(url_for('inventory_bp.home'))
    
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
    return render_template("inventory/home.html",
                            user=current_user, 
                            inventory_form=inventory_form,
                            upload_form=upload_form
                            )

@inventory_bp.route('/inventory/<slug>', methods=['POST', 'GET', 'DELETE'])
@login_required
def inventory(slug):
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
            return redirect(url_for('inventory_bp.inventory', slug=slug))
    if request.method == 'DELETE':
        data = json.loads(request.data) # add data in a python dict
        slug = data['inventorySlug']
        inventory = Inventory.query.filter_by(slug=slug, user_id=current_user.id).first()
        if inventory:
            if inventory.user_id == current_user.id:
                db.session.delete(inventory)
                db.session.commit()
                flash(f'Inventory {inventory.name} deleted!', category='success')
        return jsonify({})

    redirect(url_for('inventory_bp.home'))

@inventory_bp.route('/v1/inventory/<slug>', methods=['POST', 'GET', 'DELETE', 'PUT'])
@login_required
def inventory_api(slug):
    device_schema = DeviceSchema(many=True)
    if request.method == 'GET':
        inventory = Inventory.query.filter_by(slug=slug, user_id=current_user.id).first() 
        if inventory:
            devices = inventory.devices
            devices = device_schema.dump(devices)
            return jsonify(devices)
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
    if request.method == 'DELETE':
        data = json.loads(request.data) # add data in a python dict
        slug = data['inventorySlug']
        inventory = Inventory.query.filter_by(slug=slug, user_id=current_user.id).first()
        if inventory:
            if inventory.user_id == current_user.id:
                db.session.delete(inventory)
                db.session.commit()
        return jsonify({})

    redirect(url_for('inventory_bp.home'))

@inventory_bp.route('/v1/device/<id>', methods=['POST', 'GET', 'DELETE', 'PUT'])
@login_required
def device(id):
    if request.method == 'PUT':
        device_schema = DeviceSchema()
        try:
            data = json.loads(request.data) # add data in a python dict
            data = device_schema.load(data)
            data_dump = device_schema.dump(data)
            device = Device.query.filter_by(id=id).first()
            device = device_schema.dump(device)
            if device == data_dump:
                flash('Nothing has been modified!', category='info')
                return jsonify(''), 304
            device_updated = db.session.merge(Device(**data))
            db.session.commit()
            flash('Inventory modified!', category='success')
            device_updated = device_schema.dump(device_updated)
            return jsonify(device_updated), 200
        except ValidationException as e:
            flash(f'{e.message}', category='error')
            return jsonify({}), 400

@inventory_bp.route('/menu', methods=['POST', 'GET'])
@login_required
def menu():
    tasks = [
            {'name': 'get_version','description': 'hacer un show version'},
            {'name': 'save_config','description': 'guardar la configuracion'},
            {'name': 'set_ipdomain.j2','description': 'poner el ip domain <prueba.com>'}
        ] 
    devices = session.get('devices') or []
    if request.method == 'POST':
        devices = json.loads(request.data)
        session['devices'] = devices
        return jsonify(devices), 200
    return render_template("inventory/menu.html",
                            tasks=tasks,
                            devices=devices,
                            user=current_user,
    )

@inventory_bp.route('/v1/go', methods=['POST', 'GET'])
@login_required
def go():
    if request.method == 'POST':
        devices = session['devices']
        tasks = request.form.getlist('data')
        devices = json_to_csv(list(devices))
        print(devices)
        
        print('tasks: ', tasks)
        print('devices: ', devices)

        go = Go(csv_text=devices, tasks=tasks, cli=False, username='cisco', password='cisco')
        results = go.run()
        output = []
        for device in results:
            num_tasks = len(results[device])
            for i in range(num_tasks - 1):
                node = dict(
                    host = str(results[device][i].host),
                    name_task = str(results[device][i].name),
                    result_task = results[device][i].result,
                    has_failed = str(results[device][i].failed),
                    has_changed = str(results[device][i].changed),
                    diff = str(results[device][i].diff),
                    stderr = str(results[device][i].stderr),
                    exception = str(results[device][i].exception),  
                )
                output.append(node)
        return jsonify(output)
 
@inventory_bp.route('/results', methods=['POST', 'GET'])
def results():
    if request.method == 'POST':
        pass

    return render_template(
                    "inventory/results.html",
                    user=current_user,
    )
