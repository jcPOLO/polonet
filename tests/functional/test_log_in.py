from app.auth.models import User
from flask_login import current_user
from bs4 import BeautifulSoup


def test_get_login_page(client):
    """
    GIVEN get /login
    WHEN not logged in
    THEN shows login page and navbar Sign Up and Login buttons
    """
    response = client.get("/login")
    assert b">Login</h3>" in response.data
    assert response.status_code == 200
    assert b">Login</a>" in response.data
    assert b">Sign Up</a>" in response.data


def test_login_user_success(client):
    """
    GIVEN valid user
    WHEN logs in
    THEN flash sucess msg appears and he gets a redirect his home
    """
    response = client.get("/login")
    soup = BeautifulSoup(response.data, "html.parser")
    csrf_token = soup.body.find("input", attrs={"name": "csrf_token"})
    res = client.post(
        "/login",
        data=dict(
            email="test@test.com", password="T3st3r1n0", csrf_token=csrf_token["value"]
        ),
        follow_redirects=True,
    )
    assert b"Logged in successfully!" in res.data
    user = User.query.filter(User.email == "test@test.com").first()
    assert current_user.id == user.id
    assert current_user.is_active == True
    assert b"DASHBOARD</h1>" in res.data
    assert res.status_code == 200


def test_login_user_success_no_csrf(client_no_csrf):
    """
    GIVEN valid user
    WHEN logs in
    THEN flash sucess msg appears and he gets a redirect his home
    """
    res = client_no_csrf.post(
        "/login",
        data=dict(email="test@test.com", password="T3st3r1n0"),
        follow_redirects=True,
    )
    assert b"Logged in successfully!" in res.data
    user = User.query.filter(User.email == "test@test.com").first()
    assert current_user.id == user.id
    assert current_user.is_active == True
    assert b"DASHBOARD</h1>" in res.data
    assert res.status_code == 200


def test_login_user_bad__password_no_csrf(client_no_csrf):
    """
    GIVEN valid user
    WHEN logs in
    THEN flash sucess msg appears and he gets a redirect his home
    """
    res = client_no_csrf.post(
        "/login",
        data=dict(email="test@test.com", password="B4dPass"),
        follow_redirects=True,
    )
    assert b"Incorrect user password combination." in res.data
    assert current_user.is_active == False
    assert b"Login</h3>" in res.data
    assert res.status_code == 200


def test_login_user_no_exist(client):
    """
    GIVEN not existing user
    WHEN try to log in
    THEN flash fail msg appears and page is reloaded
    """
    response = client.get("/login")
    soup = BeautifulSoup(response.data, "html.parser")
    csrf_token = soup.body.find("input", attrs={"name": "csrf_token"})
    res = client.post(
        "/login",
        data=dict(
            email="noexist@noexist.com",
            password="N03x1sT",
            csrf_token=csrf_token["value"],
        ),
        follow_redirects=True,
    )
    assert b"Incorrect user password combination." in res.data
    assert current_user.is_active == False
    assert b"Login</h3>" in res.data
    assert res.status_code == 200


def test_login_bad_credentials(client):
    """
    GIVEN random chars
    WHEN try to log in
    THEN flash fail msg appears and page is reloaded
    """
    response = client.get("/login")
    soup = BeautifulSoup(response.data, "html.parser")
    csrf_token = soup.body.find("input", attrs={"name": "csrf_token"})
    res = client.post(
        "/login",
        data=dict(
            email="1'or'1'='1@hack.com",
            password="1' or '1' = '1",
            csrf_token=csrf_token["value"],
        ),
        follow_redirects=True,
    )
    assert b"Incorrect user password combination." in res.data
    assert current_user.is_active == False
    assert b"Login</h3>" in res.data
    assert res.status_code == 200


def test_logout_user_success(client):
    """
    GIVEN valid user
    WHEN logout
    THEN redirect to login page and change buttons Home/Logout by Login/Sign Up
    """
    response = client.get("/login")
    soup = BeautifulSoup(response.data, "html.parser")
    csrf_token = soup.body.find("input", attrs={"name": "csrf_token"})
    res = client.post(
        "/login",
        data=dict(
            email="test@test.com", password="T3st3r1n0", csrf_token=csrf_token["value"]
        ),
        follow_redirects=True,
    )
    assert current_user.is_active == True
    response = client.get("/logout")
    assert response.status_code == 302
    response = client.get("/logout", follow_redirects=True)
    assert b">Login</a>" in response.data
    assert b">Sign Up</a>" in response.data
    assert current_user.is_active == False
    assert b"Login</h3>" in response.data
    assert response.status_code == 200
