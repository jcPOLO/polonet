from nornir.core import Task
from app.core.helpers import check_directory
from app.core.tasks import backup_config, basic_configuration, get_factory
from typing import List
import logging

logger = logging.getLogger(__name__)

OUTPUT_PATH = "outputs/"
FINAL_TEMPLATE = "final.j2"
JINJA_EXTENSION = ".j2"

def container_task(task: Task, selections: List, **kwargs) -> None:
    # makes a log file output for every device accessed by netmiko config
    session_log(task)
    # backup running config
    backup_config(task)
    # tasks
    apply_actions(task, selections, **kwargs)

def apply_actions(task: Task, selections: List[str], **kwargs) -> None:
    template_applied = False
    for action in selections:
        if JINJA_EXTENSION not in action:
            logger.info(f"Applying: {action}...")
            get_factory(task, action, **kwargs)
        else:
            template_applied = True
    
    if template_applied:
        logger.info("Applying: jinja2 template")
        basic_configuration(task, FINAL_TEMPLATE)        

def session_log(task: Task, path: str = OUTPUT_PATH) -> str:
    file = f"{task.host}-output.txt"
    filename = f"{path}{file}"
    check_directory(path)
    group_object = task.host.groups[0]
    group_object.connection_options["netmiko"].extras["session_log"] = filename
    return filename
