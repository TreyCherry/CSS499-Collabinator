#dependencies: (pip installs)
#   flask, flask-sqlalchemy, flask-login


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

#can replace this with whatever db instantiation we need later
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'secret-key-goes-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        #since uid is primary key of table, use it in query for the user
        return User.query.get(int(user_id))

    #blueprint for auth routes in our app
    from .auth import auth as auth_blueprint #importing from auth.py
    app.register_blueprint(auth_blueprint)

    #blueprint for non-auth parts of app
    from .collabinator_backend import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app