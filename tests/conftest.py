import tempfile
import os
import pytest
from app import create_app
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask.testing import FlaskClient
from app.auth.models import User
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

# @pytest.fixture
# def client_no_csrf():
#     db_fd, db_path = tempfile.mkstemp()
#     app = create_app(test='no_csrf', db_fd=db_fd, db_path=db_path)
#     with app.test_client() as client:
#         with app.app_context():
#             db.create_all()
#             yield client
#     os.close(db_fd)
#     os.unlink(db_path)


# @pytest.fixture
# def client():
#     db_fd, db_path = tempfile.mkstemp()
#     app = create_app(test=True, db_fd=db_fd, db_path=db_path)
#     with app.test_client() as client:
#         with app.app_context():
#             db.create_all()
#             yield client
#     os.close(db_fd)
#     os.unlink(db_path)


@pytest.fixture
def add_user():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app(test=True, db_fd=db_fd, db_path=db_path)
    with app.test_client() as client:
        with app.app_context():
            
            yield client
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def runner(client):
    return client.test_cli_runner()


def feed_db(db):
    new_user = User(
        email="test@test.com",  
        password=generate_password_hash('T3st3r1n0', method='sha256')
    )
    assert new_user.email == "test@test.com"
    db.session.add(new_user)
    db.session.commit()

def create_db():
    return db.create_all()

def test_app(test=True):
    db_fd, db_path = tempfile.mkstemp()
    app = create_app(test, db_fd=db_fd, db_path=db_path)
    return app, db_fd, db_path

@pytest.fixture
def client():
    app, db_fd, db_path = test_app()
    with app.test_client() as client:
        with app.app_context():
            create_db()
            feed_db(db)
            yield client
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client_no_csrf():
    app, db_fd, db_path = test_app(test='no_csrf')
    with app.test_client() as client:
        with app.app_context():
            create_db()
            feed_db(db)
            yield client
    os.close(db_fd)
    os.unlink(db_path)