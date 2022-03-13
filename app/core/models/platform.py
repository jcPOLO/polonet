from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko.tasks import netmiko_send_command
from nornir.core.task import Task
import logging


class PlatformBase:
    def __init__(self, task: Task):
        self.task = task

    def get_facts(self) -> str:
        r = self.task.run(
            task=napalm_get,
            name=f'FACTs PARA: {self.task.host}',
            getters=['facts'],
            # severity_level=logging.DEBUG,
        ).result
        return r
    
    # TODO: Think about this cause this is not multiplatform
    def send_command(self, command: str) -> str:
        r = self.task.run(
            task=netmiko_send_command,
            name="SEND COMMAND - Send the command to all devices",
            # severity_level=logging.DEBUG
            command_string=command,
            use_textfsm=True
            ).result
        return r

    def get_version(self):
        pass

    def get_config(self):
        pass

    def get_config_section(self):
        pass

    def get_interfaces_status(self):
        pass

    def get_interfaces_trunk(self):
        pass

    def get_interface_description(self, interface: str):
        pass

    def get_neighbor(self, interface: str):
        pass

    def save_config(self):
        pass

    def software_upgrade(self):
        pass

    def set_rsa(self):
        pass

    def get_dir(self):
        pass
