# database.py
from flask_sqlalchemy import SQLAlchemy
from models import db

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///covoiturage.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'eduCovoit_secret_key_2024_tunisia'
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        print("✅ Base de données créée avec succès !")