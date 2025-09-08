import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session

# ----------------------------
# Extensions (single instances)
# ----------------------------
db = SQLAlchemy()
migrate = Migrate()

# ----------------------------
# Application Factory
# ----------------------------
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'supersecretkey'

    # Always use absolute path for SQLite DB
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'securebank.db')

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Session settings
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Import and register blueprints
    from .routes import main
    app.register_blueprint(main)

    return app
