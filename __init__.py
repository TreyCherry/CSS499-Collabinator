#dependencies: (pip installs)
#   flask, flask-sqlalchemy, flask-login
import os

from flask import Flask, send_from_directory
#from flask_sqlalchemy import SQLAlchemy
#from flask_login import LoginManager

#can replace this with whatever db instantiation we need later
#db = SQLAlchemy()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'CS499-Collabinator.sqlite')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)

    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)
    app.jinja_env.globals.update(get_role=db.get_role)
    app.jinja_env.globals.update(check_state=db.check_state)
    app.jinja_env.globals.update(date_format=db.date_format)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import document
    app.register_blueprint(document.bp)
    app.add_url_rule('/', endpoint='index')

    from . import members
    app.register_blueprint(members.bp, url_prefix=None)
    app.add_url_rule('/members', endpoint='members')

    from . import roles
    app.register_blueprint(roles.bp, url_prefix=None)
    app.add_url_rule('/roles', endpoint='roles')

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    return app

    '''
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
    '''