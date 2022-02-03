import json
import os
import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.inventory.models import Inventory
from werkzeug.utils import secure_filename
from app.core.models.bootstrap import Bootstrap
from app.core.models.device import Device
from app.core.helpers import configure_logging, dir_path, json_to_csv
from nornir import InitNornir
from .forms import InventoryForm
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
    form = InventoryForm()
    if form.validate_on_submit():
        inventory = form.inventory.data
        try:
            inventory = Bootstrap.import_inventory_text(inventory)
            inventory = json_to_csv(inventory)
        except ValidationException as e:
            flash(f'{e.message}', category='error')
            return redirect(url_for('inventory_bp.home'))
        except AttributeError:
            flash('Bad inventory', category='error')
            return redirect(url_for('inventory_bp.home'))
        name = form.name.data
        inventory_exists = Inventory.query.filter_by(data=inventory, user_id=current_user.id).first() 
        name_exists = Inventory.query.filter_by(name=name, user_id=current_user.id).first()
        if inventory_exists or name_exists:
            flash('Inventory already exists!', category='error')
        else:
            if len(inventory) < 1 or name=='':
                flash('Inventory does not have name or is empty', category='error')
            else:
                new_inventory = Inventory(
                    name=name,
                    data=inventory, 
                    user_id=current_user.id
                )
                db.session.add(new_inventory)
                db.session.commit()
                flash('Inventory created!', category='success')
                return redirect(url_for('inventory_bp.home'))

    return render_template("inventory/home.html", user=current_user, form=form)

@inventory_bp.route('/upload', methods=['POST', 'GET'])
@login_required
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', category='error')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash("You haven't selected any file", category='warning')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            final_filename = os.path.join(
                current_app.config['UPLOAD_FOLDER'], 
                current_app.config['INVENTORY_FILE'])
            file.save(final_filename)
            with open(final_filename) as f:
                inventory = f.read()
            print(inventory)
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
    return redirect(url_for('inventory_bp.home'))

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

@inventory_bp.route('/v1/inventory/<name>', methods=['POST', 'GET', 'DELETE', 'UPDATE'])
@login_required
def inventory_api(name):
    print('aqui si') 
    if request.method == 'GET':
        print('entra')
        inventory = Inventory.query.filter_by(name=name, user_id=current_user.id).first() 
        if inventory:
            # get Device.__iter__() dict for every device in a dict container.
            values = Bootstrap.import_inventory_text(inventory.data)
            json_data = json.dumps(values)
            return json_data
    if request.method == 'UPDATE':
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