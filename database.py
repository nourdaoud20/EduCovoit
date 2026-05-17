# database.py
from flask_sqlalchemy import SQLAlchemy
from models import db
from migrations import run_all_migrations
from pathlib import Path

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///covoiturage.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'eduCovoit_secret_key_2024_tunisia'
    
    db.init_app(app)
    
    with app.app_context():
        # Get the database path
        db_path = Path(app.instance_path) / 'covoiturage.db'
        
        # Run migrations before creating tables
        run_all_migrations(str(db_path))
        
        # Create all tables
        db.create_all()
        print("✅ Base de données créée/mise à jour avec succès !")