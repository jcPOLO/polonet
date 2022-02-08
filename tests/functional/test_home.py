from bs4 import BeautifulSoup


def test_home_no_logged(client):
    """
    GIVEN no user logged in
    WHEN the '/' page is requested (GET)
    THEN check a redirect to login page
    """
    response = client.get('/')
    assert  b'login' in response.data
    assert client.get('/').status_code == 302
    assert response.headers['Location'] == f'http://localhost/login?next=%2F'

def test_home_user_logged(client):
    """
    GIVEN user logged in
    WHEN the '/' page is requested (GET)
    THEN user inventories list is shown
    """
    response = client.get('/login')
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.body.find('input', attrs={'name' : 'csrf_token'})
    res = client.post('/login', data=dict(email='test@test.com', password='T3st3r1n0',
    csrf_token=csrf_token['value'])
    ,follow_redirects=True)
    response = client.get('/')
    assert  b'Inventory' in response.data
    assert client.get('/').status_code == 200
