import os

# Base directory of the project
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # SQLite DB stored inside /instance/SecureBank.db
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "instance", "SecureBank.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key for sessions, CSRF, etc.
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecurekey123")

    # Optional: limit query echo for debugging
    SQLALCHEMY_ECHO = False
