import os
import re
import csv
from io import StringIO
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from app.core.exceptions import AutoNornirException


# Define the expected radius IPs
EXPECTED_RADIUS_IPS = ["172.17.246.111", "172.17.246.112"]
PASS = "PASS"
FAIL = "FAIL"
WARNING = "WARNING"
VTY_TIMEOUT_ALERT = 0
SSH_VERSION_RECOMMENDED = 2.00
VALID_STP_MODES = ["rapid-pvst", "mst"]


# TODO: This is not optimal.
def security_baselines_output(result):
    baselines(result)
    users_csv(result)
    
def apply_conditional_formatting(sheet, row_num, columns):

    # Limpiar todas las reglas de formato condicional que pudiera haber ya
    sheet.conditional_formatting._cf_rules.clear()
    
    # Definir colores para los formatos condicionales
    green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    yellow_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    
    # Aplicar formato condicional para PASS, FAIL, WARNING en todas las columnas
    for col in range(1, len(columns) + 1):
        col_letter = sheet.cell(row=1, column=col).column_letter
        cell_range = f"{col_letter}2:{col_letter}{row_num}"
        
        sheet.conditional_formatting.add(
            cell_range, FormulaRule(
                formula=[f'EXACT({col_letter}2,{PASS})'], fill=green_fill))
        sheet.conditional_formatting.add(
            cell_range, FormulaRule(
                formula=[f'EXACT({col_letter}2,{FAIL})'], fill=red_fill))
        sheet.conditional_formatting.add(
            cell_range, FormulaRule(
                formula=[f'EXACT({col_letter}2,{WARNING})'], fill=yellow_fill))
    
    # Obtener los índices de las columnas específicas
    stp_mode_column = columns.index('STP mode') + 1
    ssh_version_column = columns.index('SSH version') + 1
    vty_timeout_column = columns.index('VTY timeout') + 1
    
    # Aplicar formato condicional a SSH version
    col_letter = sheet.cell(row=1, column=ssh_version_column).column_letter
    cell_range = f"{col_letter}2:{col_letter}{row_num}"
    sheet.conditional_formatting.add(
        cell_range, CellIsRule(operator='greaterThanOrEqual', 
                               formula=[f'{SSH_VERSION_RECOMMENDED}'], fill=green_fill))
    sheet.conditional_formatting.add(
        cell_range, CellIsRule(operator='lessThan', 
                               formula=[f'{SSH_VERSION_RECOMMENDED}'], fill=red_fill))
    
    # Aplicar formato condicional a VTY timeout
    col_letter = sheet.cell(row=1, column=vty_timeout_column).column_letter
    cell_range = f"{col_letter}2:{col_letter}{row_num}"
    sheet.conditional_formatting.add(
        cell_range, CellIsRule(operator='equal', 
                               formula=[f'{VTY_TIMEOUT_ALERT}'], fill=yellow_fill))
    sheet.conditional_formatting.add(
        cell_range, CellIsRule(operator='notEqual', 
                               formula=[f'{VTY_TIMEOUT_ALERT}'], fill=green_fill))
    
    # Aplicar formato condicional a STP mode
    col_letter = sheet.cell(row=1, column=stp_mode_column).column_letter
    cell_range = f"{col_letter}2:{col_letter}{row_num}"
    for stp_mode in VALID_STP_MODES:
        sheet.conditional_formatting.add(
            cell_range, FormulaRule(
                formula=[f'EXACT({col_letter}2,"{stp_mode}")'], fill=green_fill))
        
    stp_conditions = " AND ".join([f'{col_letter}2<>"{mode}"' for mode in VALID_STP_MODES])
    sheet.conditional_formatting.add(
        cell_range, FormulaRule(
            formula=[f'AND({stp_conditions})'], fill=yellow_fill))

def evaluate_check(result: bool, critical: bool = True) -> str:
    """
    Evaluates the result of a check and returns "PASS", "FAIL", or "WARNING".

    Parameters:
        result (bool): The result of the check (True or False).
        critical (bool): Indicates if the check is critical.

    Returns:
        str: "PASS" if result is True, "FAIL" if result is False and critical is True, "WARNING" if result is False and critical is False.
    """
    if result:
        return PASS
    return FAIL if critical else WARNING

def baselines(result, output_file="baselines.xlsx"):
    row_num = 0
    columns = [
        "IP", 
        "Hostname", 
        "Version", 
        "Serial", 
        "Model", 
        "Password Encryption",
        "Password Secret", 
        "Radius Servers",
        "No telnet",
        "SSH version",
        "ACL for VTY",
        "VTY timeout",
        "No HTTP Server",
        "No SNMPv1/2",
        "STP mode",
        "STP bpduguard",
        "DHCP Snooping",
        "ARP inspection",
        "Syslog server",
        "Logging buffer",
        "NTP synchronized",
        "DNS server",
        "Banner"
    ]

    if os.path.exists(output_file):
        workbook = load_workbook(output_file)
        sheet = workbook.active
    else:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Security Baselines"
        sheet.append(columns)

    for host in result.keys():
        hostname = ""
        os_version = ""
        serial_number = ""
        model = ""
        password_encryption = ""
        password_secret = ""
        radius_servers = ""
        ssh_version = ""
        facts = {}
        telnet = ""
        vty_acl = ""
        vty_timeout = ""
        http_server = ""
        snmp = ""
        stp = ""
        stp_bpduguard = ""
        dhcp_snooping = ""
        arp_inspection = ""
        syslog_server = ""
        logging_buffer = ""
        ntp_synchronized = ""
        dns_server = ""
        banner = ""

        for task_result in result[host]:
            if "FACT" in task_result.name:
                r = task_result.result
                facts = r["facts"]
                hostname = facts["hostname"]
                os_version = facts["os_version"]
                serial_number = facts["serial_number"]
                model = facts["model"]
            if "GET_CONFIG" in task_result.name:
                r = task_result.result
                password_encryption = evaluate_check(check_password_encryption(r))
                password_secret = evaluate_check(check_password_secret(r), False)
                telnet = evaluate_check( check_telnet_vty(r))
                vty_acl = evaluate_check(check_vty_acl(r), False)
                vty_timeout = get_vty_exec_timeout(r)
                http_server = evaluate_check(is_http_enabled(r))
                snmp = evaluate_check(check_snmp_version(r), False)
                stp = get_stp_mode(r)
                stp_bpduguard = evaluate_check(check_stp_bpduguard(r), False)
                dhcp_snooping = evaluate_check(check_dhcp_snooping(r), False)
                arp_inspection = evaluate_check( check_arp_inspection(r), False)
                syslog_server = evaluate_check(check_syslog_server(r))
                logging_buffer = evaluate_check(check_logging_buffer(r), False)
                dns_server = evaluate_check(check_dns_servers(r), False)
                banner = evaluate_check(check_banner(r), False)
            if "RADIUS" in task_result.name:
                r = task_result.result
                radius_servers = evaluate_check(validate_radius_servers(r))
            if "SSH_VERSION" in task_result.name:
                r = task_result.result
                ssh_version = get_ssh_version(r)
            if "NTP_STATUS" in task_result.name:
                r = task_result.result
                ntp_synchronized = evaluate_check(check_ntp_synchronized(r))
        
        try:
            ssh_version = float(ssh_version)
        except ValueError:
            ssh_version = 0.0

        row = [
            host,
            hostname,
            os_version, 
            serial_number,
            model, 
            password_encryption, 
            password_secret, 
            radius_servers,
            telnet,
            ssh_version,
            vty_acl,
            vty_timeout,
            http_server,
            snmp,
            stp,
            stp_bpduguard,
            dhcp_snooping,
            arp_inspection,
            syslog_server,
            logging_buffer,
            ntp_synchronized,
            dns_server,
            banner
        ]
        sheet.append(row)
    
    row_num = sheet.max_row
    apply_conditional_formatting(sheet, row_num, columns)
    workbook.save(output_file)
    workbook.close()

def users_csv(result, output_file="users.csv"):
    columns = ["IP", "Hostname", "Username", "Privilege", "Encryption", "Password"]

    file_exists = os.path.isfile(output_file)
    with open(output_file, mode='a', newline='') as file:
        csv_writer = csv.writer(file)
        if not file_exists:
            csv_writer.writerow(columns)

        output = StringIO()
        csv_writer_output = csv.writer(output)
        csv_writer_output.writerow(columns)

        for host in result.keys():
            hostname = ""
            users = []
            for task_result in result[host]:
                if "FACT" in task_result.name:
                    r = task_result.result
                    facts = r["facts"]
                    hostname = facts["hostname"]
                if "GET_USERS" in task_result.name:
                    r = task_result.result
                    users = parse_user_info(r)
            if users:
                for user in users:
                    row = [host, hostname, user['username'], user['privilege'], user['encryption'], user['password']]
                    csv_writer.writerow(row)
                    csv_writer_output.writerow(row)

        print(output.getvalue())

def check_telnet_vty(output: str) -> bool:
    """
    Checks if Telnet is disabled on all VTY lines of a Cisco device.

    Parameters:
        output (str): Output text of the 'show running-config' command.

    Returns:
        bool: True if Telnet is disabled on all VTY lines, False otherwise.
    """
    vty_blocks = re.findall(r'line vty \d+ \d+.*?(?=line vty \d+ \d+|$)', output, re.DOTALL)
    
    for block in vty_blocks:
        if not re.search(r'transport input ssh', block):
            return False
    return True

def check_password_encryption(config: str) -> bool:
    """
    Checks if password encryption is enabled in the configuration.

    Parameters:
        config (str): Configuration text.

    Returns:
        bool: True if password encryption is enabled, False otherwise.
    """
    match = re.search(r"^\s*(no\s+)?service password-encryption\s*$", config, re.MULTILINE)
    if match:
        if match.group(1) is None:
            return True
    return False

def check_password_secret(config: str) -> bool:
    """
    Search for the line "enable secret" in the running-config.
    If it exists, return True. If it does not exist, return False.
    """
    match = re.search(r"^\s*enable secret\s+\S+", config, re.MULTILINE)
    return float(match.group(1)) if match else 0.0

def parse_user_info(user_info: str):
    """
    Parses user information from the given string.

    Parameters:
        user_info (str): The string containing user information.

    Returns:
        list: A list of dictionaries, each containing user details such as username, privilege, encryption, and password.
    """
    user_pattern = re.compile(
        r"username\s+(?P<username>\S+)\s+"
        r"(privilege\s+(?P<privilege>\d+)\s+)?"
        r"(secret\s+(?P<encryption>\d+)\s+(?P<password>\S+)|password\s+(?P<encryption_pw>\d+)\s+(?P<password_pw>\S+))"
    )
    users = []
    for match in user_pattern.finditer(user_info):
        user = {
            'username': match.group('username'),
            'privilege': match.group('privilege') or 'N/A',
            'encryption': match.group('encryption') or match.group('encryption_pw'),
            'password': match.group('password') or match.group('password_pw')
        }
        users.append(user)
    return users

def validate_radius_servers(output: str) -> bool:
    """
    Validates if the configured RADIUS servers have the correct IPs.
    
    Parameters:
        output (str): Output text of the 'sh aaa servers public' command.
    
    Returns:
        bool: True if the IPs are correct, False if there are no servers.
    
    Raises:
        AutoNornirException: If the found IPs are different from the expected ones.
    """

    # Find all IP addresses of the RADIUS servers
    found_ips = re.findall(r'host (\d+\.\d+\.\d+\.\d+)', output)

    # Expected IPs
    expected_ips = set(EXPECTED_RADIUS_IPS)
    
    if not found_ips:
        return False  # No servers configured

    found_ips_set = set(found_ips)

    if found_ips_set == expected_ips:
        return True  # The IPs are correct
    else:
        raise AutoNornirException("fail-config", f"The found IPs are: {', '.join(found_ips)}")

def get_ssh_version(output: str) -> float:
    """
    Extracts the SSH version from the output of the 'show ip ssh' command.
    
    Parameters:
        output (str): Output text of the command.
    
    Returns:
        float: The SSH version if found, otherwise 0.0.
    """
    match = re.search(r'SSH Enabled - version (\d+\.\d+)', output)
    return float(match.group(1)) if match else 0.0

def check_vty_acl(output: str) -> bool:
    """
    Analyzes the configuration of a Cisco device to check if there is an ACL applied on the VTY lines.
    
    Parameters:
        output (str): Output text of the 'show running-config' command.
    
    Returns:
        bool: True if there is an ACL configured, False otherwise.
    """
    # Search for the VTY lines configuration
    vty_blocks = re.findall(r'line vty \d+ \d+.*?(?=line vty \d+ \d+|$)', output, re.DOTALL)
    
    for block in vty_blocks:
        if re.search(r'access-class \d+ in', block):
            return True
    return False

def get_vty_exec_timeout(output: str) -> int:
    """
    Extracts the 'exec-timeout' value configured on the VTY line 0 of a Cisco device.

    Parameters:
        output (str): Output text of the 'show running-config' command.

    Returns:
        int: The timeout value in seconds.
    """
    match = re.search(r'line vty 0[\s\S]+?exec-timeout (\d+) (\d+)', output)
    if match:
        minutes, seconds = int(match.group(1)), int(match.group(2))
        return minutes * 60 + seconds
    else:
        return 0  # Not explicitly configured (uses the default value)

def is_http_enabled(output):
    """
    Checks if the HTTP service is enabled in the configuration of a Cisco device.

    Parameters:
        output (str): Output text of the 'show running-config' command.

    Returns:
        bool: False if it is enabled, True if it is disabled.
    """
    # Search for commands that enable the HTTP service
    if re.search(r'ip http server|ip http secure-server', output, re.IGNORECASE):
        return False
    
    return True

def check_snmp_version(output):
    """
    Checks if SNMP is configured and if it uses SNMPv1/v2 (insecure) or SNMPv3 (secure).

    Parameters:
        output (str): Output text of the 'show running-config' command.

    Returns:
        bool: False if SNMPv1/v2 is used, True if SNMPv3 is used or SNMP is not configured.
    """
    # Search for SNMPv1 or SNMPv2 (insecure) commands
    if re.search(r'snmp-server community|snmp-server host .* v1|snmp-server host .* v2c', output, re.IGNORECASE):
        return False
    
    # Search for SNMPv3 (secure)
    if re.search(r'snmp-server group .* v3', output, re.IGNORECASE):
        return True
    
    # If no SNMP configuration is found, it also passes
    return True

def get_stp_mode(output):
    """
    Extracts the STP mode configured on a Cisco device.

    Parameters:
        output (str): Output text of the 'show running-config' command.

    Returns:
        str: The STP mode found or 'No STP mode found' if not detected.
    """
    match = re.search(r'spanning-tree mode (\S+)', output)
    return match.group(1) if match else "No STP mode found"

def check_stp_bpduguard(output):
    """
    Checks if BPDU Guard is globally enabled on a Cisco device.

    Parameters:
        output (str): Output text of the 'show running-config' command.

    Returns:
        bool: True if it is enabled, False if it is not.
    """
    if re.search(r'bpduguard', output):
        return True
    return False

def check_dhcp_snooping(output: str) -> bool:
    """
    Checks if DHCP Snooping is enabled on a Cisco device.

    Parameters:
        output (str): Output text of the 'show running-config' command.

    Returns:
        bool: True if it is enabled, False otherwise.
    """
    return bool(re.search(r'ip dhcp snooping', output))

def check_arp_inspection(output: str) -> bool:
    """
    Checks if ARP inspection is enabled on a Cisco device.

    Parameters:
        output (str): Output text of the 'show running-config' command.

    Returns:
        bool: True if ARP inspection is enabled, False otherwise.
    """
    return bool(re.search(r'ip arp inspection', output))

def check_syslog_server(output: str) -> bool:
    """
    Checks if there are Syslog servers configured on a Cisco device.

    Parameters:
        output (str): Output text of the 'show running-config' command.
    
    Returns:
        bool: True if there are servers configured, False otherwise.
    """
    return bool(re.search(r'logging host', output))

def check_logging_buffer(output: str) -> bool:
    """
    Checks if the logging buffer is configured on a Cisco device.

    Parameters:
        output (str): Output text of the 'show running-config' command.
    
    Returns:
        bool: True if the buffer is configured, False otherwise.
    """
    return bool(re.search(r'logging buffered', output))

def check_ntp_synchronized(output):
    """
    Checks if the Cisco device is synchronized with an NTP server.

    Parameters:
        output (str): Output text of the 'show ntp status' command.

    Returns:
        bool: True if synchronized, False if not.
    """
    return bool(re.search(r'Clock is synchronized', output))

def check_dns_servers(output: str) -> bool:
    """
    Checks if there are DNS servers configured on a Cisco device.

    Parameters:
        output (str): Output text of the 'show running-config' command.

    Returns:
        bool: True if there are servers configured, False otherwise.
    """
    return bool(re.search(r'ip domain name', output))

def check_banner(output: str) -> bool:
    """
    Checks if there is a banner configured on a Cisco device.

    Parameters:
        output (str): Output text of the 'show running-config' command.

    Returns:
        bool: True if there is a banner configured, False otherwise.
    """
    return bool(re.search(r'banner motd', output))
