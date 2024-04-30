import os

from flask import Flask, send_from_directory, flash, redirect, url_for

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    #instantiate the flask app

    app.config.from_mapping(
        SECRET_KEY='091959f559dd2b83ca2a22bf67709c3d26d04b90585c699b231f96549f08d9e7',
        DATABASE=os.path.join(app.instance_path, 'collabinator.sqlite'),
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'documents'),
        MAX_CONTENT_LENGTH = 4 * 1024 * 1024 #max file upload size 4MB
    )

    #make sure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    #make sure the file upload folder exists
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'])
    except OSError:
        pass

    from . import db
    db.init_app(app) #run initial database commands
    #set some global env functions to use in jinja templates
    app.jinja_env.globals.update(get_role=db.get_role)
    app.jinja_env.globals.update(check_state=db.check_state)
    app.jinja_env.globals.update(date_format=db.date_format)
    app.jinja_env.globals.update(date_concise=db.date_concise)
    app.jinja_env.globals.update(check_doc_reviewer=db.check_doc_reviewer)

    from . import auth
    app.register_blueprint(auth.bp) #register auth blueprint

    from . import documents
    app.register_blueprint(documents.bp) #register documents blueprint containing index
    app.add_url_rule('/', endpoint='index') #set default route to index
    app.register_blueprint(documents.bp2) #register remaining documents blueprint

    from . import members
    app.register_blueprint(members.bp, url_prefix=None) #register members blueprint
    app.add_url_rule('/members', endpoint='members') #ensure members routes correctly

    from . import roles
    app.register_blueprint(roles.bp, url_prefix=None) #register roles blueprint
    app.add_url_rule('/roles', endpoint='roles') #ensure roles routes correctly

    from . import alerts
    app.register_blueprint(alerts.bp, url_prefix=None) #register alerts blueprint
    app.add_url_rule('/alerts', endpoint='alerts') #ensure alerts routes correctly

    @app.route('/favicon.ico') #set the icon to be used in the browser
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @app.errorhandler(413) #error handler for uploaded file exceeding config limit
    def file_too_large(error):
        flash("File too large. Maximum file size is 20MB.")
        return redirect(url_for('index'))

    return app