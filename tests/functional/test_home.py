import io
from bs4 import BeautifulSoup


def logged_user(client):
    response = client.get("/login")
    client.post(
        "/login",
        data=dict(email="test@test.com", password="T3st3r1n0"),
        follow_redirects=True,
    )


def test_home_no_logged(client):
    """
    GIVEN no user logged in
    WHEN the '/' page is requested (GET)
    THEN check a redirect to login page, show Login and Sign Up navbar buttons
    """
    response = client.get("/")
    assert b"login" in response.data
    assert response.status_code == 302
    assert response.headers["Location"] == f"http://localhost/login?next=%2F"
    response = client.get("/", follow_redirects=True)
    assert b">Login</a>" in response.data
    assert b">Sign Up</a>" in response.data


def test_home_user_logged(client):
    """
    GIVEN user logged in
    WHEN the '/' page is requested (GET)
    THEN user home page is shown and flash success msg appears. Logout and Home buttons shown in navbar.
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
    assert b"DASHBOARD</h1>" in res.data
    assert res.status_code == 200
    assert b">Logout</a>" in res.data
    assert b">Home</a>" in res.data


def test_add_csv_inventory(client_no_csrf):
    """
    GIVEN a csv like text in textarea
    WHEN submited
    THEN show inventory name added and flash success msg appears.
    """
    logged_user(client_no_csrf)
    res = client_no_csrf.post(
        "/inventory",
        data=dict(
            name="inventory 1",
            inventory="hostname,port,site\n1.1.1.1,23,zaragoza\n2.2.2.2,22,teruel",
        ),
        follow_redirects=True,
    )
    assert b"Inventory inventory 1 created!" in res.data
    assert b">inventory 1</a>" in res.data


def test_add_csv_inventory_name_exists(client_no_csrf):
    """
    GIVEN a csv like text in textarea
    WHEN submited
    THEN no new inventory is created and flash error appears
    """
    logged_user(client_no_csrf)
    res = client_no_csrf.post(
        "/inventory",
        data=dict(
            name="inventory 1",
            inventory="hostname,port,site\n1.1.1.1,23,zaragoza\n2.2.2.2,22,teruel",
        ),
        follow_redirects=True,
    )
    res = client_no_csrf.post(
        "/inventory",
        data=dict(
            name="inventory 1",
            inventory="hostname,port,site\n1.2.2.1,23,zaragoza\n2.3.3.2,22,huesca",
        ),
        follow_redirects=True,
    )
    assert b"already exists! Use a different name." in res.data
    assert b">inventory 1</a>" in res.data


def test_add_csv_inventory_exists(client_no_csrf):
    """
    GIVEN a csv like text in textarea
    WHEN submited
    THEN no new inventory is created and flash error appears
    """
    logged_user(client_no_csrf)
    res = client_no_csrf.post(
        "/inventory",
        data=dict(
            name="inventory 1",
            inventory="hostname,port,site\n1.1.1.1,23,zaragoza\n2.2.2.2,22,teruel",
        ),
        follow_redirects=True,
    )
    res = client_no_csrf.post(
        "/inventory",
        data=dict(
            name="inventory 1",
            inventory="hostname,port,site\n1.1.1.1,23,zaragoza\n2.2.2.2,22,teruel",
        ),
        follow_redirects=True,
    )
    assert b"has the same data. Invetory not created!" in res.data
    assert b">inventory 1</a>" in res.data


def test_add_csv_inventory_no_name(client_no_csrf):
    """
    GIVEN a csv like text in textarea
    WHEN submited
    THEN no inventory is created
    """
    logged_user(client_no_csrf)
    res = client_no_csrf.post(
        "/inventory",
        data=dict(
            name="",
            inventory="hostname\n1.1.1.1",
        ),
        follow_redirects=True,
    )
    assert b"created!" not in res.data


# Upload CSV
def test_upload_csv_inventory(client_no_csrf):
    """
    GIVEN a csv file
    WHEN submited
    THEN show inventory name added and flash success msg appears.
    """
    file_name = "inventory.csv"
    content = b"hostname,port,site\n1.1.1.1,23,zaragoza\n2.2.2.2,22,teruel"
    logged_user(client_no_csrf)
    res = client_no_csrf.post(
        "/inventory",
        data=dict(file=(io.BytesIO(content), file_name)),
        follow_redirects=True,
    )
    assert b"File inventory.csv uploaded!" in res.data
    assert b">inventory.csv</a>" in res.data


def test_upload_csv_inventory_name_exists(client_no_csrf):
    """
    GIVEN a csv file
    WHEN submited
    THEN no new inventory is created and flash error appears
    """
    file_name = "inventory.csv"
    content = b"hostname,port,site\n1.1.1.1,23,zaragoza\n2.2.2.2,22,teruel"
    logged_user(client_no_csrf)
    res = client_no_csrf.post(
        "/inventory",
        data=dict(file=(io.BytesIO(content), file_name)),
        follow_redirects=True,
    )
    content = b"hostname,port,site\n1.1.2.1,23,huesca\n2.2.2.2,22,teruel"
    res = client_no_csrf.post(
        "/inventory",
        data=dict(file=(io.BytesIO(content), file_name)),
        follow_redirects=True,
    )
    assert b"already exists! Use a different name." in res.data
    assert b">inventory.csv</a>" in res.data


def test_upload_csv_inventory_exists(client_no_csrf):
    """
    GIVEN a csv file
    WHEN submited
    THEN no new inventory is created and flash error appears
    """
    file_name = "inventory.csv"
    content = b"hostname,port,site\n1.1.1.1,23,zaragoza\n2.2.2.2,22,teruel"
    logged_user(client_no_csrf)
    res = client_no_csrf.post(
        "/inventory",
        data=dict(file=(io.BytesIO(content), file_name)),
        follow_redirects=True,
    )
    res = client_no_csrf.post(
        "/inventory",
        data=dict(file=(io.BytesIO(content), file_name)),
        follow_redirects=True,
    )
    assert b"has the same data. Invetory not created!" in res.data
    assert b">inventory.csv</a>" in res.data


def test_upload_csv_inventory_no_name(client_no_csrf):
    """
    GIVEN a csv file
    WHEN submited
    THEN no new inventory is created.
    """
    file_name = "inventory.csv"
    content = b"hostname,port,site\n1.1.1.1,23,zaragoza\n2.2.2.2,22,teruel"
    logged_user(client_no_csrf)
    res = client_no_csrf.post(
        "/inventory",
        data=dict(file=(io.BytesIO(content), file_name)),
        follow_redirects=True,
    )
    assert b"created!" not in res.data
