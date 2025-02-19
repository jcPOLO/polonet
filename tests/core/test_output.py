import pytest
from app.core.output import check_telnet_vty, \
    check_password_encryption, check_password_secret
from app.core.output import evaluate_check, PASS, FAIL, WARNING
from app.core.output import parse_user_info


def test_parse_user_info_single_user():
    config = """
    username admin privilege 15 secret 5 $1$abc123
    """
    expected = [
        {
            'username': 'admin',
            'privilege': '15',
            'encryption': '5',
            'password': '$1$abc123'
        }
    ]
    assert parse_user_info(config) == expected

def test_parse_user_info_multiple_users():
    config = """
    username admin privilege 15 secret 5 $1$abc123
    username user1 secret 5 $1$def456
    username user2 privilege 10 secret 5 $1$ghi789
    """
    expected = [
        {
            'username': 'admin',
            'privilege': '15',
            'encryption': '5',
            'password': '$1$abc123'
        },
        {
            'username': 'user1',
            'privilege': 'N/A',
            'encryption': '5',
            'password': '$1$def456'
        },
        {
            'username': 'user2',
            'privilege': '10',
            'encryption': '5',
            'password': '$1$ghi789'
        }
    ]
    assert parse_user_info(config) == expected

def test_parse_user_info_no_users():
    config = """
    !
    """
    expected = []
    assert parse_user_info(config) == expected

def test_parse_user_info_incomplete_user():
    config = """
    username admin secret 5
    """
    expected = []
    assert parse_user_info(config) == expected

def test_parse_user_info_no_secret_user():
    config = """
    username admin password 0 cisco
    """
    expected = [
        {
            'username': 'admin',
            'privilege': 'N/A',
            'encryption': '0',
            'password': 'cisco'
        }	
    ]
    assert parse_user_info(config) == expected

def test_evaluate_check_pass():
    assert evaluate_check(True) == PASS

def test_evaluate_check_fail_critical():
    assert evaluate_check(False, critical=True) == FAIL

def test_evaluate_check_warning_non_critical():
    assert evaluate_check(False, critical=False) == WARNING

def test_evaluate_check_default_critical():
    assert evaluate_check(False) == FAIL

def test_evaluate_check_non_critical():
    assert evaluate_check(False, critical=False) == WARNING

def test_password_encryption_enabled():
    config = """
    service password-encryption
    line vty 0 4
     password 7 0822455D0A16
    """
    assert check_password_encryption(config) == True

def test_password_encryption_disabled():
    config = """
    line vty 0 4
     password 7 0822455D0A16
    """
    assert check_password_encryption(config) == False

def test_password_encryption_partial():
    config = """
    service password
    line vty 0 4
     password 7 0822455D0A16
    """
    assert check_password_encryption(config) == False

def test_password_encryption_prepending_no():
    config = """
    no service password-encryption
    line vty 0 4
     password 7 0822455D0A16
    """
    assert check_password_encryption(config) == False

def test_password_encryption_empty_config():
    config = ""
    assert check_password_encryption(config) == False

def test_check_telnet_vty_enabled():
    config = """
    line vty 0 4
     transport input telnet ssh
    line vty 5 15
     transport input all
    """
    assert check_telnet_vty(config) == False

def test_check_telnet_vty_disabled():
    config = """
    line vty 0 4
     transport input ssh
    line vty 5 15
     transport input ssh
    """
    assert check_telnet_vty(config) == True

def test_check_telnet_vty_no_transport_input():
    config = """
    line vty 0 4
    line vty 5 15
    """
    assert check_telnet_vty(config) == False

def test_check_telnet_vty_mixed():
    config = """
    line vty 0 4
     transport input ssh
    line vty 5 15
     transport input telnet
    """
    assert check_telnet_vty(config) == False

def test_check_telnet_vty_no_transport_input_mixed():
    config = """
    line vty 0 4
     transport input ssh
    line vty 5 15
    !
    """
    assert check_telnet_vty(config) == False

def test_check_telnet_vty_empty_config():
    config = ""
    assert check_telnet_vty(config) == True

def test_telnet_vty_disabled():
    output = """
    line vty 0 4
     transport input ssh
    line vty 5 15
     transport input ssh
    """
    assert check_telnet_vty(output) == True

def test_telnet_vty_enabled():
    output = """
    line vty 0 4
     transport input ssh
    line vty 5 15
     transport input telnet
    """
    assert check_telnet_vty(output) == False

def test_check_password_secret_enabled():
    config = """
    enable secret 5 $1$abc123
    """
    assert check_password_secret(config) == True

def test_check_password_secret_disabled():
    config = """
    !
    """
    assert check_password_secret(config) == False

def test_check_password_secret_partial():
    config = """
    enable password 7 0822455D0A16
    """
    assert check_password_secret(config) == False

def test_check_password_secret_multiple_lines():
    config = """
    enable secret 5 $1$td/0$kwSJan8PZEIkSOo9q/
    enable secret 5 $1$abc123
    """
    assert check_password_secret(config) == True

def test_check_password_secret_no_secret():
    config = """
    enable password 7 0822455D0A16
    enable password 7 0822455D0A17
    """
    assert check_password_secret(config) == False
