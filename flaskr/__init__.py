import os
import secrets

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from .config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH


db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=secrets.token_hex(16),
        SQLALCHEMY_DATABASE_URI='sqlite:///time_capsule.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=UPLOAD_FOLDER,
        MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH
    )

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    db.init_app(app)
    migrate.init_app(app, db)

    from .routes import auth, capsule, main
    app.register_blueprint(auth.bp)
    app.register_blueprint(capsule.bp)
    app.register_blueprint(main.bp)

    return app