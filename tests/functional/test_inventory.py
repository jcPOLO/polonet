import io
import json
from bs4 import BeautifulSoup

def logged_user(client):
    response = client.get('/login')
    client.post(
        '/login', 
        data=dict(
            email='test@test.com', 
            password='T3st3r1n0'
        ),follow_redirects=True
    )

def test_inventory_no_logged(client):
    """
    GIVEN no user logged in
    WHEN the '/inventory/<inventory>' page is requested (GET)
    THEN check a redirect to login page, show Login and Sign Up navbar buttons
    """
    response = client.get('/inventory/inventory1')
    assert  b'login' in response.data
    assert response.status_code == 302
    assert f'login?next=%2Finventory%2Finventory1' in response.headers['Location']
    response = client.get('/', follow_redirects=True)
    assert b'>Login</a>' in response.data
    assert b'>Sign Up</a>' in response.data

def test_inventory_user_logged(client):
    """
    GIVEN user logged in
    WHEN the '/inventory/<inventory>' page is requested (GET)
    THEN user inventory page is shown. Logout and Home buttons shown in navbar.
    """
    response = client.get('/login')
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.body.find('input', attrs={'name' : 'csrf_token'})
    client.post(
        '/login', 
        data=dict(
            email='test@test.com', 
            password='T3st3r1n0',
            csrf_token=csrf_token['value']
        ),follow_redirects=True
    )
    response = client.get('/inventory/inventory1')
    assert  b'Modify inventory' in response.data
    assert response.status_code == 200
    assert b'>Logout</a>' in response.data
    assert b'>Home</a>' in response.data

def test_inventory_csv_is_loaded(client_no_csrf):
    """
    GIVEN inventory <inventory> selected in home
    WHEN '/inventory/<inventory>' page is requested (GET)
    THEN inventory csv is loaded in textarea.
    """
    logged_user(client_no_csrf)
    response = client_no_csrf.get('/inventory/inventory1')
    assert  b'3.3.3.3,22,ios,teruel' in response.data
    assert response.status_code == 200

# TODO: I have no idea how to test if js table is being loaded and doing fetch to API to get the data
def test_inventory_table_is_loaded(client_no_csrf):
    """
    GIVEN inventory <inventory> selected in home
    WHEN '/inventory/<inventory>' page is requested (GET)
    THEN inventory csv is loaded in textarea.
    """
    logged_user(client_no_csrf)
    res = client_no_csrf.post(
        '/', 
        data=dict(
            name='inventory2', 
            inventory='hostname,port,site\n1.2.1.1,23,zaragoza\n2.3.2.2,22,teruel',
        ),follow_redirects=True
    )
    response = client_no_csrf.get('/inventory/inventory2',follow_redirects=True)
    assert b'teruel' in response.data
    assert response.status_code == 200
