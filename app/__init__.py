from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow

db = SQLAlchemy() 
ma = Marshmallow()
login_manager = LoginManager()


def create_app(test=False, db_path=None):
    app = Flask(__name__)
    if test == True:
        # load the test config if passed in
        app.config.from_object('tests.config_test')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
        app.config['DB_NAME'] = path.basename(db_path)
    elif test == 'no_csrf':
        # load the test config if passed in
        app.config.from_object('tests.config_test')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
        app.config['DB_NAME'] = path.basename(db_path)
        app.config['WTF_CSRF_ENABLED'] = False
    else:
        # load the instance config, if it exists, when not testing
        app.config.from_object('config')

    migrate = Migrate(app, db)

    db.init_app(app)
    ma.init_app(app)

    from app.inventory.views import inventory_bp
    from app.auth.views import auth_bp

    app.register_blueprint(inventory_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/')

    from app.auth.models import User

    login_manager.login_view = 'auth_bp.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        user = User.query.filter_by(id=id).first()
        if user:
            return user
        return None
    
    # Sample HTTP error handling
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
        
    if test:
        return app

    create_database(app)
    return app


def create_database(app):
    if not path.exists(
        path.join(app.config['BASE_DIR'], app.config['DB_NAME'])
    ):
        db.create_all(app=app)
