from nornir.core.filter import F
from app.core.models.device import Device
from tabulate import tabulate
import os
import sys


class Filter:
    """
    Class for filtering inventory by different ways. Shows a menu and return a Nornir object filtered.

    Args:
        nr (Nornir): Nornir object to be filtered.

    Attributes:
        choices (dict): Menu options
        initial_nr (Nornir): Pre-filtered nornir object needed to recover from filters applied.
        nr (Nornir): Nornir object to be returned filtered.
        platforms (list): Total device platforms registered in inventory.
        keys (list): Total inventory column keys to filter by.

    """

    platforms = []
    keys = []

    def __init__(self, nr) -> None:

        self.choices = {
            "1": self.by_platform,
            "2": self.by_hostname,
            "3": self.by_field,
            "z": self.clear,
            "s": self.show,
            "e": self.exit,
        }

        self.initial_nr = nr
        self.nr = nr
        self.set_parameters()
        self.run()

    @staticmethod
    def display_menu() -> None:
        os.system("clear")
        print(
            """
           Filter by:

           1. Platform
           2. IP
           3. Other fields...

           --------------------------------------------------------------------

           ENTER to continue      s. Show selection       z. Clear selections

           e. Exit

           """
        )

    @staticmethod
    def devices_filtered(self, text="All devices selected:") -> str:
        msg = text + "\n"
        table_header = ["id", "platform", "hostname", "port"]
        table = []

        i = 0
        for device in self.nr.inventory.hosts:
            i += 1
            row = [
                i,
                str(self.nr.inventory.hosts[device].platform),
                str(self.nr.inventory.hosts[device].hostname),
                str(self.nr.inventory.hosts[device].port),
            ]
            table.append(row)
        msg += tabulate(table, headers=table_header, tablefmt="fancy_grid")
        return msg

    def run(self, msg="") -> None:
        self.display_menu()
        if msg:
            print(msg)

        while True:
            choice = input("Enter an option: ")
            if choice.strip() in self.choices.keys():
                field = self.choices.get(choice.strip())
                return field()
            else:
                return self.nr

    def show(self) -> None:
        msg = self.devices_filtered(self)
        self.run(msg)

    def clear(self) -> None:
        self.nr = self.initial_nr
        self.run()
        print(f"All filters cleared.\n")

    @staticmethod
    def exit() -> None:
        print(f"Bye!\n")
        sys.exit()

    def by_platform(self):
        nr = self.nr

        platforms = set()

        for host in nr.inventory.hosts.values():
            platforms.add(host.platform)

        platform = input(f"Platform to filter by: - {', '.join(platforms)}:").lower()

        if platform in platforms:
            devices = nr.filter(F(platform=platform))
            self.nr = devices
            msg = self.devices_filtered(self, "Filtered by {platform}:")
            self.run(msg)
        else:
            msg = self.devices_filtered(self)
            self.run(msg)

    def by_hostname(self):
        nr = self.nr

        hostnames = set()

        for host in nr.inventory.hosts.values():
            hostnames.add(host.hostname)

        hostname = input(f"IP to filter by: - {', '.join(hostnames)}:").lower()
        if "," in hostname:
            hostname_list = [host.strip() for host in hostname.split(",")]
            devices = nr.filter(filter_func=lambda h: h.name in hostname_list)
            self.nr = devices
            msg = self.devices_filtered(self, "Filtered by IPs:")
        elif hostname in hostnames:
            devices = nr.filter(F(hostname=hostname))
            self.nr = devices
            msg = self.devices_filtered(self, "Filtered by IP:")
        else:
            msg = self.devices_filtered(self)
        self.run(msg)

    def by_field(self):
        field = input(f"Field to filter by: - {', '.join(self.keys)}:").lower()

        if field in self.keys:
            nr = self.nr

            values = set()

            for host in nr.inventory.hosts.values():
                values.add(host[field])

            value = input(f"{field} to filter by: - {', '.join(values)}:").lower()

            if value in values:
                devices = nr.filter(F(**{field: str(value)}))
                self.nr = devices
                msg = self.devices_filtered(self, "Filtered by {field}")
                self.run(msg)

        else:
            msg = self.devices_filtered(self)
            self.run(msg)

    # TODO: 0 usages in whole project...
    @staticmethod
    def show_filtering_options(nr, fields=dict):
        if fields:
            devices = nr.filter(F(groups__contains=fields))
        else:
            devices = nr.filter(F(groups__contains="ios"))
        print(devices.inventory.hosts.keys())
        pass

    @classmethod
    def set_parameters(cls):
        cls.platforms = Device.get_devices_platform()
        cls.keys = Device.get_devices_data_keys()
