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
        self, 
        devices: Dict = None, 
        tasks: List = None, 
        cli: bool = True, 
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

        if self.cli:
            print_result(result)

        # ---------------------------------------------------
        # app.core.output.facts_for_customer_csv(result)
        # ---------------------------------------------------

        # Start the stopwatch / counter
        t1_stop = perf_counter()

        if self.cli:
            while result.failed_hosts:
                self.on_failed_host(devices, result)
                retry = input("Do you want to retry tasks on failed hosts?[y/n]")
                if retry == "y":
                    params = {"on_good": False, "on_failed": True}
                    result = self.main_task(devices, self.tasks, **params)
                    print_result(result)
                else:
                    break

            elapsed_time = t1_stop - t1_start
            print(
                "Elapsed time during the whole program in seconds:",
                "{0:.2f}".format(elapsed_time),
            )

        return result

    def main_task(
        self, devices: "Nornir", selections: List, **kwargs
    ) -> "AggregatedResult":
        result = devices.run(
            task=container_task,
            selections=selections,
            name=f"CONTAINER TASK",
            # severity_level=logging.DEBUG,
            **kwargs,
        )
        return result

    def on_failed_host(self, devices: "Nornir", result: "AggregatedResult"):
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
