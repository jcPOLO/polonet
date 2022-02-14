from nornir import InitNornir
from nornir.core import Nornir
from nornir.core.task import AggregatedResult
from nornir_utils.plugins.functions import print_result
from app.core.main_functions import container_task
from app.core.models.menu import Menu
from app.core.models.bootstrap import Bootstrap
from app.core.models.filter import Filter
from app.core.helpers import configure_logging, dir_path
import getpass
from typing import List
import logging


logger = logging.getLogger(__name__)
CFG_FILE = f'{dir_path}/config.yaml'


class Go(object):
    """
    Main class to launch nornir tasks.

    Args:
        ini_file (str): Path to the ini file
        csv_file (str): Path to inventory file
        encoding (str): csv encoding type

    Attributes:
        groups (list): Associated group belonged
        data (dict): Extra data associated to the device
        devices (list): Device object generator counter
        platforms (list): Total device platforms registered in inventory.

    """
    def __init__(
        self,
        devices: dict = None,
        tasks: list = None,
        cli: str = True,
        **kwargs
    ):

        self.devices = devices
        self.tasks = tasks
        self.cli = cli
        self.data = kwargs or {}


    def run(self) -> None:
        # configure logger
        configure_logging(logger)

        # creates hosts.yaml from csv file, ini file could be passed as arg,
        # by default .global.ini
        bootstrap = Bootstrap(**self.data)
        bootstrap.load_inventory()

        # initialize Nornir object
        nr = InitNornir(config_file=CFG_FILE)

        if self.cli:
            # show filter options menu and return device inventory filtered
            filter_obj = Filter(nr)
            devices = filter_obj.nr

            # show the main menu
            menu_obj = Menu()
            self.tasks = menu_obj.run()

            # before executing the tasks, ask for device credentials
            username = input("\nUsername:")
            password = getpass.getpass()
        else:
            devices = nr

        username = self.data.get('username') or username
        password = self.data.get('password') or password

        devices.inventory.defaults.password = password
        devices.inventory.defaults.username = username

        logger.info('----------- LOADING -----------\n')

        result = self.main_task(devices, self.tasks)
        return result

    def main_task(self, devices: 'Nornir', selections: List, **kwargs) -> 'AggregatedResult':
        result = devices.run(
            task=container_task,
            selections=selections,
            name=f'CONTAINER TASK',
            # severity_level=logging.DEBUG,
            **kwargs
        )
        return result
