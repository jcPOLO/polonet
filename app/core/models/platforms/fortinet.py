from nornir_netmiko.tasks import (
    netmiko_send_command,
    netmiko_save_config,
)
from nornir.core.task import Result, Task
from typing import List, Dict
from app.core.models.platform import PlatformBase
from app.core.helpers import HumanBytes
from app.core.exceptions import RuntimeErrorException
import os
import logging


GET_CONFIG_MSG = "GET_VPN - SHOW VPN PARA EL HOST: {}"
GET_CONFIG_CMD = "show vpn ipsec phase2-interface VPN_Orange"


class Fortinet(PlatformBase):
    def __init__(self, task: Task):
        super().__init__(task)

    def get_config(self) -> str:
        r = self.task.run(
            task=netmiko_send_command,
            name=GET_CONFIG_MSG.format(self.task.host.hostname),
            command_string=GET_CONFIG_CMD,
            severity_level=logging.DEBUG,
        ).result
        return r
