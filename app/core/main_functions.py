from nornir.core import Task
from app.core.helpers import check_directory
from app.core.tasks import backup_config, basic_configuration, get_factory
from typing import List

# import configparser
import logging

logger = logging.getLogger(__name__)
FINAL_TEMPLATE = "final.j2"


def container_task(task: Task, selections: List) -> None:
    # makes a log file output for every device accessed by netmiko config
    session_log(task)
    # backup running config
    backup_config(task)
    # tasks
    template = False
    for action in selections:
        if ".j2" not in action:
            logger.info(f"Applying: {action}...")
            get_factory(task, action)
        else:
            template = True

    if template:
        logger.info("Applying: jinja2 template")
        basic_configuration(task, FINAL_TEMPLATE)


def session_log(task: Task, path: str = "outputs/") -> str:
    if path is None:
        path = "outputs/"
    file = f"{task.host}-output.txt"
    filename = f"{path}{file}"
    check_directory(path)
    group_object = task.host.groups[0]
    group_object.connection_options["netmiko"].extras["session_log"] = filename
    return filename
