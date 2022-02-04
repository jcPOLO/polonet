import json
import os
import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
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

CFG_FILE = f'{dir_path}/config.yaml'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@inventory_bp.route('/', methods=['GET', 'POST'])
@login_required
def home():
    inventory_form = InventoryForm()
    upload_form = UploadForm()
    # POST de csv textArea
    if inventory_form.validate_on_submit():
        inventory = inventory_form.inventory.data
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
        name = inventory_form.name.data
        inventory_exists = Inventory.query.filter_by(data=inventory_csv, user_id=current_user.id).first() 
        name_exists = Inventory.query.filter_by(name=name, user_id=current_user.id).first()
        if inventory_exists or name_exists:
            flash('Inventory already exists!', category='error')
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
                    # TODO: only allows predefined DB attributes. Need to pass a JSON object in custom field por non-predefined attrb.
                    d,_ = Device.get_or_create(db.session, **device)
                    new_inventory.devices.append(d)
                db.session.add(new_inventory)
                db.session.commit()
                flash('Inventory created!', category='success')
                return redirect(url_for('inventory_bp.home'))
    # POST de upload csv
    elif upload_form.validate_on_submit():
        filename = secure_filename(upload_form.file.data.filename)
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
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
            inventory_name_exists = Inventory.query.filter_by(name=name, user_id=current_user.id).first()
            if inventory_name_exists:
                flash('Inventory already exists!', category='error')
            else:
                if len(inventory) < 1:
                    flash('Inventory does not have enougth text', category='error')
                else:
                    new_inventory = Inventory(
                        name=name,
                        data=inventory, 
                        user_id=current_user.id
                    )
                    db.session.add(new_inventory)
                    db.session.commit()
                    flash('File uploaded', category='success')
                    return redirect(url_for('inventory_bp.home'))
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
            values = Bootstrap.import_inventory_text(inventory.data)
            # get first dict element keys.
            keys = values[0].keys()
            json_data = json.dumps(values)
            return render_template(
                "inventory/inventory.html",
                inventory=inventory,
                values=values,
                keys=keys,
                user=current_user,
                json_data=json_data
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
        return jsonify({})

    redirect(url_for('inventory_bp.home'))

def csv_to_table(csv):
    pass

@inventory_bp.route('/v1/inventory/<name>', methods=['POST', 'GET', 'DELETE', 'PUT'])
@login_required
def inventory_api(name):
    if request.method == 'GET':
        inventory = Inventory.query.filter_by(name=name, user_id=current_user.id).first() 
        if inventory:
            # get Device.__iter__() dict for every device in a dict container.
            values = Bootstrap.import_inventory_text(inventory.data)
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