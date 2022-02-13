import json
import tempfile
import os
from flask import jsonify
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
    new_user.inventories.append(new_inventory(new_user))
    return new_user

def new_inventory(new_user):
    new_inventory = Inventory(
        name='inventory1',
        slug='inventory1',
        data="""
        hostname,port,platform,site
        1.1.1.1,22,ios,zaragoza
        2.2.2.2,23,nxos,huesca
        3.3.3.3,22,ios,teruel
        """,
        user_id=new_user.id
    )
    devices = new_devices(new_user)
    for device in devices:
        new_inventory.devices.append(device)
    return new_inventory

def new_devices(new_user):
    new_devices = []
    device = Device(
        hostname='1.1.1.1',
        platform='ios',
        port=22,
        custom=json.dumps({ 'site': 'zaragoza' }),
        user_id=new_user.id
    )
    new_devices.append(device)
    device = Device(
        hostname='2.2.2.2',
        platform='nxos',
        port=23,
        custom=json.dumps({ 'site': 'huesca' }),
        user_id=new_user.id
    )
    new_devices.append(device)
    device = Device(
        hostname='3.3.3.3',
        platform='ios',
        port=22,
        custom=json.dumps({ 'site': 'teruel' }),
        user_id=new_user.id
    )
    new_devices.append(device)
    return new_devices

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
