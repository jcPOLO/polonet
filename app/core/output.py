import os
import re
import csv
from io import StringIO
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from openpyxl.formatting.rule import CellIsRule, FormulaRule


# Define the expected radius IPs
EXPECTED_RADIUS_IPS = ["172.17.246.111", "172.17.246.112"]


# TODO: This is not optimal.
def facts_for_customer_csv(result):
    baselines(result)
    users_csv(result)
    
def apply_conditional_formatting(wb, row_num, columns):
    sheet = wb["Security Baselines"]

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
        
        sheet.conditional_formatting.add(cell_range, FormulaRule(formula=[f'EXACT({col_letter}2,"PASS")'], fill=green_fill))
        sheet.conditional_formatting.add(cell_range, FormulaRule(formula=[f'EXACT({col_letter}2,"FAIL")'], fill=red_fill))
        sheet.conditional_formatting.add(cell_range, FormulaRule(formula=[f'EXACT({col_letter}2,"WARNING")'], fill=yellow_fill))
    
    # Obtener los índices de las columnas específicas
    stp_mode_column = columns.index('STP mode') + 1
    ssh_version_column = columns.index('SSH version') + 1
    vty_timeout_column = columns.index('VTY timeout') + 1
    
    # Aplicar formato condicional a SSH version
    col_letter = sheet.cell(row=1, column=ssh_version_column).column_letter
    cell_range = f"{col_letter}2:{col_letter}{row_num}"
    sheet.conditional_formatting.add(cell_range, CellIsRule(operator='greaterThanOrEqual', formula=['2.00'], fill=green_fill))
    sheet.conditional_formatting.add(cell_range, CellIsRule(operator='lessThan', formula=['2.00'], fill=red_fill))
    
    # Aplicar formato condicional a VTY timeout
    col_letter = sheet.cell(row=1, column=vty_timeout_column).column_letter
    cell_range = f"{col_letter}2:{col_letter}{row_num}"
    sheet.conditional_formatting.add(cell_range, CellIsRule(operator='equal', formula=['0'], fill=yellow_fill))
    sheet.conditional_formatting.add(cell_range, CellIsRule(operator='notEqual', formula=['0'], fill=green_fill))
    
    # Aplicar formato condicional a STP mode
    col_letter = sheet.cell(row=1, column=stp_mode_column).column_letter
    cell_range = f"{col_letter}2:{col_letter}{row_num}"
    sheet.conditional_formatting.add(cell_range, FormulaRule(formula=[f'EXACT({col_letter}2,"rapid-pvst")'], fill=green_fill))
    sheet.conditional_formatting.add(cell_range, FormulaRule(formula=[f'EXACT({col_letter}2,"mst")'], fill=green_fill))
    sheet.conditional_formatting.add(cell_range, FormulaRule(formula=[f'AND({col_letter}2<>"rapid-pvst", {col_letter}2<>"mst")'], fill=yellow_fill))

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
                password_encryption = check_password_encryption(r)
                password_secret = check_password_secret(r)
                telnet = check_telnet_vty(r)
                vty_acl = check_vty_acl(r)
                vty_timeout = get_vty_exec_timeout(r)
                http_server = is_http_enabled(r)
                snmp = check_snmp_version(r)
                stp = get_stp_mode(r)
                stp_bpduguard = check_stp_bpduguard(r)
                dhcp_snooping = check_dhcp_snooping(r)
                arp_inspection = check_arp_inspection(r)
                syslog_server = check_syslog_server(r)
                logging_buffer = check_logging_buffer(r)
                dns_server = check_dns_server(r)
                banner = check_banner(r)
            if "RADIUS" in task_result.name:
                r = task_result.result
                radius_servers = validate_radius_servers(r)
            if "SSH_VERSION" in task_result.name:
                r = task_result.result
                ssh_version = get_ssh_version(r)
            if "NTP_STATUS" in task_result.name:
                r = task_result.result
                ntp_synchronized = check_ntp_synchronized(r)
        
        try:
            ssh_version = float(ssh_version)
        except ValueError:
            ssh_version = 0

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
    apply_conditional_formatting(workbook, row_num, columns)
    workbook.save(output_file)
    
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

def check_telnet_vty(config: str) -> str:
    """
    Verifica si Telnet está habilitado en la configuración de las líneas VTY.

    Parámetros:
        config (str): Texto de salida del comando 'show running-config'.

    Retorna:
        str: 'FAIL' si Telnet está habilitado, 'PASS' si está deshabilitado.
    """
    # Extraer bloques de configuración de line vty
    vty_blocks = re.findall(r"line vty \d+ \d+(?:\n .*)*", config)

    for block in vty_blocks:
        # Buscar la línea 'transport input ...'
        transport_match = re.search(r"transport input (.+)", block)

        if transport_match:
            transport_methods = transport_match.group(1).split()
            # Si 'telnet' o 'all' están presentes, Telnet está habilitado -> FAIL
            if "telnet" in transport_methods or "all" in transport_methods:
                return "FAIL"
        else:
            # Si no hay 'transport input' especificado, Telnet está habilitado -> FAIL
            return "FAIL"

    # Si todas las líneas VTY tienen 'transport input' sin telnet, está deshabilitado -> PASS
    return "PASS"


def check_password_encryption(config: str) -> str:
    """
    Search for the line "service password-encryption" in the running-config.
    
    Parameters:
        config (str): The running configuration of the device.
    
    Returns:
        str: 'PASS' if the service password-encryption is enabled, 'FAIL' otherwise.
    """
    match = re.search(r"^\s*(no\s+)?service password-encryption\s*$", config, re.MULTILINE)
    if match:
        if match.group(1) is None:
            return "PASS"
    return "FAIL"

def check_password_secret(config: str) -> str:
    """
    Search for the line "enable secret" in the running-config.
    If it exists, return "PASS". If it does not exist, return "WARNING".
    """
    match = re.search(r"^\s*enable secret\s+\S+", config, re.MULTILINE)
    if match:
        return "PASS"
    return "WARNING"

def parse_user_info(user_info: str):
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

def validate_radius_servers(output):
    """
    Valida si los servidores RADIUS configurados tienen las IPs correctas.
    
    Parámetros:
        output (str): Texto de salida del comando 'sh aaa servers public'.
    
    Retorna:
        str: 'PASS' si las IPs son correctas, 'FAIL' si no hay servidores,
             o un mensaje con las IPs encontradas si son diferentes.
    """
    # Buscar todas las direcciones IP de los servidores RADIUS
    found_ips = re.findall(r'host (\d+\.\d+\.\d+\.\d+)', output)

    # IPs esperadas
    expected_ips = set(EXPECTED_RADIUS_IPS)
    
    if not found_ips:
        return "FAIL"  # No hay servidores configurados

    found_ips_set = set(found_ips)

    if found_ips_set == expected_ips:
        return "PASS"  # Las IPs son correctas
    else:
        return f"Las IPs encontradas son: {', '.join(found_ips)}"

def get_ssh_version(output):
    """
    Extrae la versión de SSH del output del comando 'show ip ssh'.
    
    Parámetros:
        output (str): Texto de salida del comando.
    
    Retorna:
        str: La versión de SSH encontrada o 'No SSH version found' si no la detecta.
    """
    match = re.search(r'SSH Enabled - version (\d+\.\d+)', output)
    return match.group(1) if match else "No SSH version found"

def check_vty_acl(output):
    """
    Analiza la configuración de un dispositivo Cisco para verificar si hay una ACL aplicada en las líneas VTY.
    
    Parámetros:
        output (str): Texto de salida del comando 'show running-config'.
    
    Retorna:
        str: "PASS" si hay una ACL configurada, "FAIL" si no la hay.
    """
    # Buscar la configuración de las líneas VTY
    vty_section = re.search(r'line vty \d+ \d+([\s\S]+?)!', output)
    
    if vty_section:
        # Verificar si hay un 'access-class' configurado
        if re.search(r'access-class \d+ in', vty_section.group(1)):
            return "PASS"
    
    return "WARNING"

def get_vty_exec_timeout(output):
    """
    Extrae el valor del 'exec-timeout' configurado en la línea VTY 0 de un dispositivo Cisco.

    Parámetros:
        output (str): Texto de salida del comando 'show running-config'.

    Retorna:
        int: El tiempo de espera en segundos.
    """
    match = re.search(r'line vty 0[\s\S]+?exec-timeout (\d+) (\d+)', output)
    if match:
        minutes, seconds = int(match.group(1)), int(match.group(2))
        return minutes * 60 + seconds
    else:
        return 0  # No configurado explícitamente (usa el valor por defecto)

def is_http_enabled(output):
    """
    Verifica si el servicio HTTP está habilitado en la configuración de un dispositivo Cisco.

    Parámetros:
        output (str): Texto de salida del comando 'show running-config'.

    Retorna:
        str: 'FAIL' si está activado, 'PASS' si está desactivado.
    """
    # Busca los comandos que activan el servicio HTTP
    if re.search(r'ip http server|ip http secure-server', output, re.IGNORECASE):
        return "FAIL"
    
    return "PASS"

def check_snmp_version(output):
    """
    Verifica si SNMP está configurado y si usa SNMPv1/v2 (inseguro) o SNMPv3 (seguro).

    Parámetros:
        output (str): Texto de salida del comando 'show running-config'.

    Retorna:
        str: 'PASS' si no hay SNMP o solo se usa SNMPv3, 'FAIL' si se usa SNMPv1/v2.
    """
    # Busca comandos de SNMPv1 o SNMPv2 (inseguro)
    if re.search(r'snmp-server community|snmp-server host .* v1|snmp-server host .* v2c', output, re.IGNORECASE):
        return "WARNING"
    
    # Busca SNMPv3 (seguro)
    if re.search(r'snmp-server group .* v3', output, re.IGNORECASE):
        return "PASS"
    
    # Si no encuentra nada de SNMP, también pasa
    return "PASS"

def get_stp_mode(output):
    """
    Extrae el modo STP configurado en un dispositivo Cisco.

    Parámetros:
        output (str): Texto de salida del comando 'show running-config'

    Retorna:
        str: El modo STP encontrado o 'No STP mode found' si no lo detecta.
    """
    match = re.search(r'spanning-tree mode (\S+)', output)
    return match.group(1) if match else "No STP mode found"

def check_stp_bpduguard(output):
    """
    Identifica si el BPDU Guard está habilitado globalmente en un dispositivo Cisco.

    Parámetros:
        output (str): Texto de salida del comando 'show running-config'

    Retorna:
        str: 'PASS' si está habilitado, 'FAIL' si no lo está.
    """
    if re.search(r'bpduguard', output):
        return "PASS"
    return "WARNING"

def check_dhcp_snooping(output):
    """
    Verifica si el DHCP Snooping está habilitado en un dispositivo Cisco.

    Parámetros:
        output (str): Texto de salida del comando 'show running-config'.

    Retorna:
        str: 'PASS' si está habilitado, 'FAIL' si no lo está.
    """
    if re.search(r'ip dhcp snooping', output):
        return "PASS"
    return "WARNING"

def check_arp_inspection(output):
    """
    Verifica si la inspección ARP está habilitada en un dispositivo Cisco.

    Parámetros:
        output (str): Texto de salida del comando 'show running-config'.

    Retorna:
        str: 'PASS' si está habilitada, 'FAIL' si no lo está.
    """
    if re.search(r'ip arp inspection', output):
        return "PASS"
    return "WARNING"   

def check_syslog_server(output):
    """
    Verifica si hay servidores Syslog configurados en un dispositivo Cisco.

    Parámetros:
        output (str): Texto de salida del comando 'show running-config'.
    
    Retorna:
        str: 'PASS' si hay servidores configurados, 'FAIL' si no hay ninguno.
    """
    if re.search(r'logging host', output):
        return "PASS"
    return "FAIL"

def check_logging_buffer(output):
    """
    Verifica si el buffer de registro está configurado en un dispositivo Cisco.

    Parámetros:
        output (str): Texto de salida del comando 'show running-config'.

    Retorna:
        str: 'PASS' si el buffer está configurado, 'FAIL' si no lo está.
    """
    if re.search(r'logging buffered', output):
        return "PASS"
    return "WARNING"

def check_ntp_synchronized(output):
    """
    Verifica si el dispositivo Cisco está sincronizado con un servidor NTP.

    Parámetros:
        output (str): Texto de salida del comando 'show ntp status'.

    Retorna:
        str: 'PASS' si está sincronizado, 'FAIL' si no lo está.
    """
    if re.search(r'Clock is synchronized', output):
        return "PASS"
    return "FAIL"

def check_dns_server(output):
    """
    Verifica si hay servidores DNS configurados en un dispositivo Cisco.

    Parámetros:
        output (str): Texto de salida del comando 'show running-config'.

    Retorna:
        str: 'PASS' si hay servidores configurados, 'FAIL' si no hay ninguno.
    """
    if re.search(r'ip domain name', output):
        return "PASS"
    return "WARNING"  

def check_banner(output):
    """
    Verifica si hay un banner configurado en un dispositivo Cisco.

    Parámetros:
        output (str): Texto de salida del comando 'show running-config'.

    Retorna:
        str: 'PASS' si hay un banner configurado, 'FAIL' si no lo hay.
    """
    if re.search(r'banner motd', output):
        return "PASS"
    return "WARNING"
