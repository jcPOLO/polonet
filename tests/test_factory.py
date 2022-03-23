import os
import tempfile
from app import create_app
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow


db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
login_manager = LoginManager()


def test_config():
    """Test create_app for testing pourposes."""
    assert not create_app().testing
    db_fd, db_path = tempfile.mkstemp()
    app = create_app(test=True, db_path=db_path)
    assert app.testing
    os.close(db_fd)
    os.unlink(db_path)


def test_config_no_csrf():
    """Test create_app without WTF CSRF checks."""
    assert not create_app().testing
    db_fd, db_path = tempfile.mkstemp()
    app = create_app(test="no_csrf", db_path=db_path)
    assert app.testing
    os.close(db_fd)
    os.unlink(db_path)
