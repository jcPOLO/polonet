import os
from app import create_app
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import tempfile


db = SQLAlchemy() 
ma = Marshmallow()


def test_config():
    """Test create_app for testing pourposes."""
    assert not create_app().testing
    db_fd, db_path = tempfile.mkstemp()
    app = create_app(test=True, db_fd=db_fd, db_path=db_path)
    assert app.testing
    os.close(db_fd)
    os.unlink(db_path)
 

def test_config_no_csrf():
    """Test create_app without WTF CSRF checks."""
    assert not create_app().testing
    db_fd, db_path = tempfile.mkstemp()
    app = create_app(test='no_csrf', db_fd=db_fd, db_path=db_path)
    assert app.testing
    os.close(db_fd)
    os.unlink(db_path)
