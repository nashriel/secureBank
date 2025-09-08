import os
from app import create_app, db

# Ensure instance folder exists
if not os.path.exists("instance"):
    os.makedirs("instance")

# Database path
db_path = "instance/SecureBank.db"

# Delete existing database if it exists
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Deleted existing database file: {db_path}")

# Create app and initialize DB
app = create_app()

with app.app_context():
    db.create_all()
    print("All tables created successfully!")

print("Database reset complete.")
