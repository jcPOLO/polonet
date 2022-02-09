from bs4 import BeautifulSoup
from flask import url_for


def test_home_no_logged(client):
    """
    GIVEN no user logged in
    WHEN the '/' page is requested (GET)
    THEN check a redirect to login page, show Login and Sign Up navbar buttons
    """
    response = client.get('/')
    assert  b'login' in response.data
    assert response.status_code == 302
    assert response.headers['Location'] == f'http://localhost/login?next=%2F'
    response = client.get('/', follow_redirects=True)
    assert b'>Login</a>' in response.data
    assert b'>Sign Up</a>' in response.data

def test_home_user_logged(client):
    """
    GIVEN user logged in
    WHEN the '/' page is requested (GET)
    THEN user home page is shown and flash sucess msg appears. Logout and Home buttons shown in navbar.
    """
    response = client.get('/login')
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.body.find('input', attrs={'name' : 'csrf_token'})
    res = client.post('/login', data=dict(email='test@test.com', password='T3st3r1n0',
    csrf_token=csrf_token['value'])
    ,follow_redirects=True)
    assert  b'Logged in successfully!' in res.data
    assert  b'Inventories</h3>' in res.data
    assert res.status_code == 200
    assert b'>Logout</a>' in res.data
    assert b'>Home</a>' in res.data
