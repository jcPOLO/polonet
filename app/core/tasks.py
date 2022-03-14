from typing import Callable
from nornir.core import Task
from nornir_jinja2.plugins.tasks import template_file
from nornir_netmiko.tasks import netmiko_send_config
from app.core.helpers import check_directory, dir_path
from app.core.models.platforms.platform_factory import PlatformFactory
import configparser
import logging
import os


TEMPLATES_DIR = dir_path+'/templates/'


def backup_config(task: Task, path: str = 'backups/') -> None:
    r = ''
    file = f'{task.host}.cfg'
    filename = f'{path}{file}'
    device = PlatformFactory().get_platform(task)
    r = device.get_config()
    if r:
        check_directory(filename)
        with open(filename, 'w') as f:
            f.write(r)


def basic_configuration(
        task: Task,
        template: str,
        ini_vars: configparser = None
) -> None:
    # convert ini_vars configparser object to dict for templates
    if ini_vars:
        path = ini_vars.get('CONFIG', 'templates_path')
        ini_vars = dict(ini_vars['GLOBAL'])
    else:
        path = TEMPLATES_DIR
        ini_vars = None
    # Transform inventory data to configuration via a template file
    r = task.run(task=template_file,
                 name=f"PLANTILLA A APLICAR PARA {task.host.platform}",
                 template=template,
                 path=f"{path}{task.host.platform}",
                 ini_vars=ini_vars,
                 nr=task,
                 severity_level=logging.DEBUG,
                 )
    # Save the compiled configuration into a host variable
    task.host["config"] = r.result
    # Send final configuration template using netmiko
    task.run(task=netmiko_send_config,
             name=f"PLANTILLA APLICADA A {task.host.platform}",
             config_commands=task.host["config"].splitlines(),
             # severity_level=logging.DEBUG,
             )


def get_factory(task: Task, method: str) -> Callable:
    device = PlatformFactory().get_platform(task)
    return getattr(device, method)()
