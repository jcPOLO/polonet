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
    user = new_user()
    db.drop_all()
    db.create_all()
    db.session.add(user)
    db.session.commit()
    
def new_user():
    new_user = User(
        email="test@test.com", 
        first_name='Testeriano Testeos', 
        password=generate_password_hash('T3st3r1n0', method='sha256')
    )
    return new_user

def test_app(test=True):
    db_fd, db_path = tempfile.mkstemp()
    app = create_app(test, db_path=db_path)
    return app, db_fd, db_path

@pytest.fixture
def client():
    app, db_fd, db_path = test_app()
    with app.test_client() as client:
        with app.app_context():
            feed_db()
            yield client
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client_no_csrf():
    app, db_fd, db_path = test_app(test='no_csrf')
    with app.test_client() as client:
        with app.app_context():
            feed_db()
            yield client
    os.close(db_fd)
    os.unlink(db_path)
