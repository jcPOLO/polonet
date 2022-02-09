import tempfile
import os
import pytest
from app import create_app
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask.testing import FlaskClient
from app.auth.models import User
from app.inventory.models import Inventory, Device
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


@pytest.fixture
def runner(client):
    return client.test_cli_runner()

def feed_db():
    db.session.add(new_user())
    db.session.commit()

def new_user():
    new_user = User(
        email="test@test.com", 
        first_name='Testeriano Testeos', 
        password=generate_password_hash('T3st3r1n0', method='sha256')
    )
    return new_user

@pytest.fixture
def new_inventory(new_user):
    new_inventory = Inventory(
        name="inventory 1",  
        user_id=new_user.id,
        data='hostname,port,site\n1.1.1.1,23,zaragoza\n2.2.2.2,22,teruel'
    )
    return new_inventory

def test_app(test=True):
    db_fd, db_path = tempfile.mkstemp()
    app = create_app(test, db_path=db_path)
    return app, db_fd, db_path

@pytest.fixture
def client():
    app, db_fd, db_path = test_app()
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            feed_db()
            yield client
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client_no_csrf():
    app, db_fd, db_path = test_app(test='no_csrf')
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            feed_db()
            yield client
    os.close(db_fd)
    os.unlink(db_path)
