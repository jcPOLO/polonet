from crypt import methods
import json
import os
import logging
from typing import Dict, List
from flask import Blueprint, render_template, request, flash, redirect, session, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.inventory.schemas import InventorySchema, DeviceSchema
from app.inventory.models import Device, Inventory
from app.core.helpers import dir_path, json_to_csv
from app.core.core import Core


job_bp = Blueprint('job_bp', __name__, template_folder='templates')
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'txt', 'csv'}
DEFAULT_DEVICE_ATTR = [
    'hostname','platform','port','custom','user_id','id',
    'date_created','date_modified'
]
OMITTED_DEVICE_ATTR = ['groups','user_id','_sa_instance_state']
CFG_FILE = f'{dir_path}/config.yaml'


@job_bp.route('/job', methods=['GET','POST'])
@login_required
def tasks():
    tasks = [
        {'name': 'get_version','description': 'hacer un show version'},
        {'name': 'save_config','description': 'guardar la configuracion'},
        {'name': 'set_ip_domain.j2','description': 'poner el ip domain <prueba.com>'}
    ]
    devices = session.get('devices') or []
    if request.method == 'POST':
        devices = json.loads(request.data)
        session['devices'] = devices
        return jsonify(devices), 200
    return render_template("job/tasks.html",
                            tasks=tasks,
                            devices=devices,
                            user=current_user,
    )

# TODO: temporary web result  '/job/<id>/result'
@job_bp.route('/job/result', methods=['GET','POST'])
@login_required
def jobs():
    # GET
    results = session.get('results')

    if request.method == 'POST':
        devices = session['devices']
        tasks = request.form.getlist('data')
        devices = json_to_csv(list(devices))
        print(devices)

        print('tasks: ', tasks)
        print('devices: ', devices)

        core = Core(csv_text=devices, tasks=tasks, cli=False, username='cisco', password='cisco')
        results = core.run()
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
        objects = ", ".join(
            [
                f'{{host: "{host}", success: {not v.failed}, task: "asdf"}}'
                for host, v in results.items()
            ]
        )
        print(objects)

        redirect(url_for('inventory_bp.inventories'))
        return jsonify(output)
    return render_template("job/result.html",
                            user=current_user,
                            jobs=jobs,
                            )