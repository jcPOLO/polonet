from app.auth.models import User
from flask_login import current_user
from bs4 import BeautifulSoup



def test_sign_up_page(client):
    """
    GIVEN get /sign-up
    WHEN not logged in
    THEN shows /sign-up page and navbar Sign Up and Login buttons
    """
    response = client.get('/sign-up')
    assert  b'>Sign Up</h3>' in response.data
    assert response.status_code == 200
    assert b'>Login</a>' in response.data
    assert b'>Sign Up</a>' in response.data

def test_user_sign_up_success(client):
    """
    GIVEN new user
    WHEN signs up
    THEN flash sucess msg appears and user is redirected to inventories list
    """
    response = client.get('/sign-up')
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.body.find('input', attrs={'name' : 'csrf_token'})
    res = client.post(
        '/sign-up',
        data=dict(
            email="new@user.com",
            first_name="Newerino Useriano",
            password1="P4ssw0rd",
            password2="P4ssw0rd",
            csrf_token=csrf_token['value'],
        ),follow_redirects=True
    )
    assert  b'Account created!' in res.data
    assert  b'Inventories</h3>' in res.data
    assert res.status_code == 200


def test_user_sign_up_password_missmatch(client):
    """
    GIVEN new user
    WHEN signs up
    THEN flash fail msg Passwords are not the same appears
    """
    response = client.get('/sign-up')
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.body.find('input', attrs={'name' : 'csrf_token'})
    res = client.post(
        '/sign-up',
        data=dict(
            email="new@user.com",
            first_name="Newerino Useriano",
            password1="P4ssw0rd",
            password2="NotTheSamePassword",
            csrf_token=csrf_token['value'],
        ),follow_redirects=True
    )
    assert  b'Passwords are not the same' in res.data
    assert  b'Sign Up</h3>' in res.data
    assert res.status_code == 200

def test_user_sign_up_already_exists(client):
    """
    GIVEN existing user
    WHEN signs up
    THEN flash fail msg Email already exists appears 
    """
    response = client.get('/sign-up')
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.body.find('input', attrs={'name' : 'csrf_token'})
    res = client.post(
        '/sign-up',
        data=dict(
            email="test@test.com",
            first_name="Newerino Useriano",
            password1="P4ssw0rd",
            password2="P4ssw0rd",
            csrf_token=csrf_token['value'],
        ),follow_redirects=True
    )
    assert  b'Email already exists.' in res.data
    assert  b'Sign Up</h3>' in res.data
    assert res.status_code == 200
    
def test_user_sign_up_bad_credentials(client):
    """
    GIVEN injection user
    WHEN signs up
    THEN flash sucess msg appears and user is redirected to inventories list
    """
    response = client.get('/sign-up')
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.body.find('input', attrs={'name' : 'csrf_token'})
    res = client.post(
        '/sign-up',
        data=dict(
            email="1'or'1'='1@hack.com",
            first_name="1' or '1' = '1",
            password1="1' or '1' = '1",
            password2="1' or '1' = '1",
            csrf_token=csrf_token['value'],
        ),follow_redirects=True
    )
    assert  b'Account created!' in res.data
    assert  b'Inventories</h3>' in res.data
    assert res.status_code == 200
    user = User.query.filter(User.email=="1'or'1'='1@hack.com").first()
    assert user.first_name == "1' or '1' = '1"
    