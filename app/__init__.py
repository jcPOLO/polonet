from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_migrate import Migrate


db = SQLAlchemy() 


def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    migrate = Migrate(app, db)

    db.init_app(app)

    from app.inventory.views import inventory_bp
    from app.auth.views import auth_bp

    app.register_blueprint(inventory_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/')

    from app.auth.models import User

    create_database(app)

    login_manager = LoginManager()
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

    return app


def create_database(app):
    if not path.exists(
        path.join(app.config['BASE_DIR'], app.config['DB_NAME'])
    ):
        db.create_all(app=app)
        print('Created Database')
