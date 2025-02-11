from nornir import InitNornir
from nornir.core import Nornir
from nornir.core.task import AggregatedResult, MultiResult
from nornir_utils.plugins.functions import print_result
from app.core.main_functions import container_task
from app.core.models.menu import Menu
from app.core.models.bootstrap import Bootstrap
from app.core.models.filter import Filter
from app.core.helpers import configure_logging, dir_path, prompt_user
from app.core.output import security_baselines_output
import getpass
from typing import List, Dict
import logging


logger = logging.getLogger(__name__)
CFG_FILE = f"{dir_path}/config.yaml"


class Core(object):
    """
    Main class to launch nornir tasks.

    Args:
        devices (list): Inventory
        tasks (list): Task chosen to execute
        cli (bool): If should go web or cli

    Attributes:
        devices (list): Inventory
        tasks (list): Task chosen to execute
        cli (bool): If should go web or cli

    """

    def __init__(
        self, devices: Dict = None, tasks: List = None, cli: bool = True, **kwargs
    ):

        self.devices = devices
        self.tasks = tasks
        self.cli = cli
        self.data = kwargs or {}

    def run(self) -> MultiResult:
        # configure logger
        configure_logging(logger)

        # creates hosts.yaml from csv file, ini file could be passed as arg,
        # by default .global.ini
        bootstrap = Bootstrap(**self.data)
        bootstrap.load_inventory()

        # initialize Nornir object
        nr = InitNornir(config_file=CFG_FILE)

        menu_obj = Menu(self.tasks)

        if self.cli:
            # show filter options menu and return device inventory filtered
            filter_obj = Filter(nr)
            devices = filter_obj.nr

            # show the main menu
            self.tasks = menu_obj.run()

            # before executing the tasks, ask for device credentials
            username = input("\nUsername:")
            password = getpass.getpass()
        else:
            devices = nr
            # create final.j2 if there are templates selected
            self.tasks = menu_obj.apply()

        username = self.data.get("username") or username
        password = self.data.get("password") or password

        devices.inventory.defaults.password = password
        devices.inventory.defaults.username = username

        # Python program to show time by perf_counter()
        from time import perf_counter

        # Start the stopwatch / counter
        t1_start = perf_counter()

        logger.info("----------- LOADING -----------\n")

        result = self.main_task(devices, self.tasks)

        # Start the stopwatch / counter
        t1_stop = perf_counter()

        if self.cli:
            self.handle_cli(result, devices, self.tasks, t1_start, t1_stop)

        return result

    def main_task(
        self, devices: Nornir, selections: List[str], **kwargs
    ) -> AggregatedResult:
        if 'send_command' in selections:
            command = input('Comando a enviar:\n')
            kwargs['command'] = command
        result = devices.run(
            task=container_task,
            selections=selections,
            name=f"CONTAINER TASK",
            # severity_level=logging.DEBUG,
            **kwargs,
        )
        return result

    def on_failed_host(self, devices: Nornir, result: AggregatedResult) -> None:
        print(
            """
            Failed HOSTS:
            --------------------------------------
            """
        )
        for host in result.failed_hosts:
            logger.error(
                "Host: \x1b[1;31;40m{}\n{}\x1b[0m".format(
                    host, devices.inventory.hosts[host].hostname
                )
            )
            logger.error(
                "|_Error: \x1b[0;31;40m{}\x1b[0m".format(result[host][1].exception)
            )
            logger.error("|_Task: {}".format(result.failed_hosts[host]))

        print(
            """
            --------------------------------------
            """
        )

    def handle_cli(
            self, 
            result: AggregatedResult, 
            devices: Nornir, 
            tasks: List[str], 
            t1_start: float, 
            t1_stop: float
            ) -> None:
        
        print_result(result)
        security_baselines_output(result)

        while result.failed_hosts:
            self.log_failed_hosts(result)
            if prompt_user("Do you want to see the details?[y/n]"):
                self.on_failed_host(devices, result)
            if prompt_user("Do you want to retry tasks on failed hosts?[y/n]"):
                result = self.retry_failed_tasks(devices, tasks)
                print_result(result)
            else:
                break

        self.print_elapsed_time(t1_start, t1_stop)

    def log_failed_hosts(self, result: AggregatedResult) -> None:
        logger.info("Failed hosts:")
        logger.info("hostname")
        for host in result.failed_hosts.keys():
            logger.info(host)

    def retry_failed_tasks(self, devices: Nornir, tasks: List[str]) -> AggregatedResult:
        params = {"on_good": False, "on_failed": True}
        return self.main_task(devices, tasks, **params)

    def print_elapsed_time(self, t1_start: float, t1_stop: float) -> None:
        elapsed_time = t1_stop - t1_start
        print("Elapsed time during the whole program in seconds:", "{0:.2f}".format(elapsed_time))

