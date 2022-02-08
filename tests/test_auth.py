from app.auth.models import User
from flask_login import current_user
from bs4 import BeautifulSoup


def test_login_page(client_no_csrf):
    """Get /login page"""
    response = client_no_csrf.get('/login')
    assert  b'<h3 align="center">Login</h3>' in response.data
    assert response.status_code == 200


def test_login_page(client):
    """Get /login page"""
    response = client.get('/login')
    assert  b'<h3 align="center">Login</h3>' in response.data
    assert response.status_code == 200


def test_login_user_success(client):
    """ Login in with a valid user """
    response = client.get('/login')
    soup = BeautifulSoup(response.data, 'html.parser')
    csrf_token = soup.body.find('input', attrs={'name' : 'csrf_token'})
    res = client.post('/login', data=dict(email='test@test.com', password='T3st3r1n0',
    csrf_token=csrf_token['value'])
    ,follow_redirects=True)
    user = User.query.filter(User.email=='test@test.com').first()
    assert current_user.id == user.id
    assert res.status_code == 200
    assert current_user.is_active == True
    assert b'inventory' in res.data


def test_add_used_no_csrf(client_no_csrf):
    """ Login in with a valid user """
    # new_user = User(
    #             email="test1@test.com",  
    #             password=generate_password_hash('T3st3r1n0', method='sha256')
    # )
    # assert new_user.email == "test1@test.com"
    # db.session.add(new_user)
    # db.session.commit()
    # user = User.query.filter(User.email=='test@test.com').first()
    # assert user.email == new_user.email
    # response = client.get('/login')
    res = client_no_csrf.post(
        '/login', 
        data=dict(email='test@test.com', password='T3st3r1n0'
        ),follow_redirects=True
    )
    # assert current_user.id == user.id
    assert res.status_code == 200
    assert current_user.is_active == True
    assert b'inventory' in res.data
