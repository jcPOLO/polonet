import json
import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from . import db
from .models import Inventory
from werkzeug.utils import secure_filename
from app.core.models.bootstrap import Bootstrap
from app.core.models.device import Device
from app.core.helpers import configure_logging, dir_path
from nornir import InitNornir
import logging


views = Blueprint('views', __name__)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'txt', 'csv'}

CFG_FILE = f'{dir_path}/config.yaml'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        inventory = request.form.get('inventory')
        inventory_name = request.form.get('inventoryName')
        inventory_exists = Inventory.query.filter_by(data=inventory, user_id=current_user.id).first() 
        inventory_name_exists = Inventory.query.filter_by(name=inventory_name, user_id=current_user.id).first()
        if inventory_exists or inventory_name_exists:
            flash('Inventory already exists!', category='error')
        else:
            if len(inventory) < 1 or inventory_name=='':
                flash('Inventory does not have name or is empty', category='error')
            else:
                try:
                    Bootstrap.import_inventory_text(inventory)
                except:
                    flash('Inventory validation failed', category='error')
                    return redirect(url_for('views.home'))
                new_inventory = Inventory(
                    name=inventory_name,
                    data=inventory, 
                    user_id=current_user.id
                )
                db.session.add(new_inventory)
                db.session.commit()
                flash('Inventory created!', category='success')
                return redirect(url_for('views.home'))

    return render_template("home.html", user=current_user)

@views.route('/upload', methods=['POST', 'GET'])
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
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], 'inventory.csv'))
            with open(f"{os.path.join(current_app.config['UPLOAD_FOLDER'], 'inventory.csv')}") as f:
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
                    return redirect(url_for('views.home'))
        else:
            flash('File type must be csv or txt', category='error')
    return redirect(url_for('views.home'))

@views.route('/auto-nornir', methods=['POST', 'GET'])
@login_required
def auto_nornir():
    if request.method == 'GET':
        # configure logger
        configure_logging(logger)

        # creates hosts.yaml from csv file, ini file could be passed as arg,
        # by default .global.ini
        bootstrap = Bootstrap()
        bootstrap.load_inventory()

        # initialize Nornir object
        nr = InitNornir(config_file=CFG_FILE)

        custom_keys = Device.get_devices_data_keys()
        print(custom_keys)

        devices = nr.inventory.hosts

        logger.info('----------- LOADING -----------\n')


        return render_template(
            "filter.html", 
            user=current_user, 
            devices=devices,
            custom_keys=custom_keys,
        )


@views.route('/inventory/<name>', methods=['POST', 'GET', 'DELETE'])
@login_required
def inventory(name):
    if request.method == 'GET':
        inventory = Inventory.query.filter_by(name=name, user_id=current_user.id).first() 
        if inventory:
            # get Device.__iter__() dict for every device in a dict container.
            values = Bootstrap.import_inventory_text(inventory.data)
            # get first dict element keys.
            keys = list(values.values())[0].keys()
            return render_template(
                "inventory.html",
                inventory=inventory,
                values=values,
                keys=keys,
                user=current_user
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
            return redirect(url_for('views.home'))
    if request.method == 'DELETE':
        data = json.loads(request.data) # add data in a python dict
        inventory_id = data['inventoryId']
        inventory = Inventory.query.get(inventory_id)
        if inventory:
            if inventory.user_id == current_user.id:
                db.session.delete(inventory)
                db.session.commit()
        return jsonify({})

    redirect(url_for('views.home'))

def csv_to_table(csv):
    pass