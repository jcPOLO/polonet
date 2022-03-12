from crypt import methods
from datetime import datetime
import json
import os
import logging
from typing import Dict, List
from flask import Blueprint, render_template, request, flash, redirect, session, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.inventory.schemas import InventorySchema, DeviceSchema
from app.inventory.models import Device, Inventory
from app.job.models import Job
from app.job.schemas import JobSchema
from app.core.helpers import dir_path, json_to_csv
from app.core.core import Core
from nornir_utils.plugins.functions import print_result


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
    job_schema = JobSchema()
    # GET
    results = session.get('results')
    if request.method == 'GET':
        pass

    if request.method == 'POST':
        devices = session['devices']
        tasks = request.form.getlist('data')
        devices = json_to_csv(list(devices))

        core = Core(csv_text=devices, tasks=tasks, cli=False, username='cisco', password='cisco')
        data = dict(
            inventory_id = session['inventory_id'],
            output = '',
            status=1,
        )
        job = job_schema.load(data)
        results = core.run()
        job.finished_at = datetime.now()
        db.session.commit()
        result = job_schema.dump(job)

        result_tasks = { k: [] for k in tasks if '.j2' not in k }

        print_result(results)
        status = results.failed # True if at least 1 task failed

        for host, tasks_result in sorted(results.items()):
            for task in tasks_result:
                task_name = str(task.name).split(' ')[0].lower()
                if task_name in tasks or task_name == 'get_config' or 'plantilla' in task_name:
                    taskres = {
                        'result': task.result,
                        'failed': task.failed,
                        'ip': str(host),
                        'changed': task.changed,
                        'diff': task.diff,
                        'stderr': task.stderr,
                        # 'exception': task.exception
                    }
                    result_tasks[task_name] = result_tasks.get(task_name, [])
                    result_tasks[task_name].append(taskres)

        for task,hosts in result_tasks.items():
            print(f'{task} ************')
            for host in hosts:
                if host['failed']:
                    print(f"{host['ip']} : FAIL")
                    # print(f"EXCEPTION: {host['exception']}")
                else:
                    print(f"{host['ip']} : OK")

        return render_template("job/result.html",
                        user=current_user,
                        status=status,
                        session=session,
                        result=result,
                        tasks=result_tasks,
                        )
