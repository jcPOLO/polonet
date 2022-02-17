from app.auth.models import User
from werkzeug.security import generate_password_hash, check_password_hash

def test_new_user():
    user = User(
        email='testuser@testuser.com', 
        first_name='Testiliano Userino', 
        password=generate_password_hash('T3sTp4ss', method='sha256')
    )
    assert user.email == 'testuser@testuser.com'
    assert user.password != 'T3sTp4ss'
    assert check_password_hash(user.password, 'T3sTp4ss')
