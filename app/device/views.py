from crypt import methods
import json
import os
import logging
from typing import Dict, List
from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    session,
    url_for,
    jsonify,
    current_app,
)
from flask_login import login_required, current_user
from app import db
from app.inventory.schemas import InventorySchema, DeviceSchema
from app.inventory.models import Device, Inventory
from app.core.helpers import dir_path, json_to_csv
from app.core.exceptions import ValidationException


device_bp = Blueprint("device_bp", __name__, template_folder="templates")
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"txt", "csv"}
DEFAULT_DEVICE_ATTR = [
    "hostname",
    "platform",
    "port",
    "custom",
    "user_id",
    "id",
    "date_created",
    "date_modified",
]
OMITTED_DEVICE_ATTR = ["groups", "user_id", "_sa_instance_state"]
CFG_FILE = f"{dir_path}/config.yaml"


@device_bp.route("/device", methods=["GET", "POST"])
@login_required
def devices():
    # GET
    devices = Device.query.filter_by(user_id=current_user.id)
    return render_template(
        "device/devices.html",
        user=current_user,
        devices=devices,
    )


@device_bp.route("/device/<id>", methods=["POST", "GET", "DELETE", "PUT"])
@login_required
def device(id):
    # PUT
    if request.method == "PUT":
        device_schema = DeviceSchema()
        try:
            data = json.loads(request.data)  # add data in a python dict
            data = device_schema.load(data)
            data_dump = device_schema.dump(data)
            device = Device.query.filter_by(id=id).first()
            device = device_schema.dump(device)
            if device == data_dump:
                flash("Nothing has been modified!", category="info")
                return jsonify(""), 304
            device_updated = db.session.merge(Device(**data))
            db.session.commit()
            flash("Inventory modified!", category="success")
            device_updated = device_schema.dump(device_updated)
            return jsonify(device_updated), 200
        except ValidationException as e:
            flash(f"{e.message}", category="error")
            return jsonify({}), 400
