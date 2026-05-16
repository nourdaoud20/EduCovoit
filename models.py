# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ============================================
# CLASSE UTILISATEUR (parente)
# ============================================
class Utilisateur(UserMixin, db.Model):
    __tablename__ = 'utilisateurs'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    telephone = db.Column(db.String(20))
    mot_de_passe = db.Column(db.String(255), nullable=False)
    note_moyenne = db.Column(db.Float, default=0.0)
    nombre_avis = db.Column(db.Integer, default=0)
    type_utilisateur = db.Column(db.String(20))
    
    # Relations
    avis_recus = db.relationship('Avis', foreign_keys='Avis.cible_id', backref='cible')
    avis_donnes = db.relationship('Avis', foreign_keys='Avis.auteur_id', backref='auteur')
    
    def __init__(self, nom, email, telephone, mot_de_passe, type_utilisateur):
        self.nom = nom
        self.email = email
        self.telephone = telephone
        self.mot_de_passe = mot_de_passe
        self.type_utilisateur = type_utilisateur
    
    def noter_utilisateur(self, cible_id, note, commentaire=""):
        avis = Avis(
            auteur_id=self.id,
            cible_id=cible_id,
            note=note,
            commentaire=commentaire
        )
        db.session.add(avis)
        cible = Utilisateur.query.get(cible_id)
        cible.nombre_avis += 1
        cible.note_moyenne = ((cible.note_moyenne * (cible.nombre_avis - 1)) + note) / cible.nombre_avis
        db.session.commit()


# ============================================
# CLASSE CONDUCTEUR
# ============================================
class Conducteur(Utilisateur):
    __tablename__ = 'conducteurs'
    
    id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), primary_key=True)
    trajets = db.relationship('Trajet', backref='conducteur', lazy=True)
    
    def __init__(self, nom, email, telephone, mot_de_passe):
        super().__init__(nom, email, telephone, mot_de_passe, 'conducteur')
    
    def publier_trajet(self, depart, arrivee, date, heure, places_disponibles, prix):
        trajet = Trajet(
            conducteur_id=self.id,
            depart=depart,
            arrivee=arrivee,
            date=date,
            heure=heure,
            places_disponibles=places_disponibles,
            places_initiales=places_disponibles,
            prix=prix
        )
        db.session.add(trajet)
        db.session.commit()
        return trajet
    
    def modifier_trajet(self, trajet_id, **kwargs):
        trajet = Trajet.query.get(trajet_id)
        if trajet and trajet.conducteur_id == self.id:
            for key, value in kwargs.items():
                if hasattr(trajet, key):
                    setattr(trajet, key, value)
            db.session.commit()
            return True
        return False
    
    def supprimer_trajet(self, trajet_id):
        trajet = Trajet.query.get(trajet_id)
        if trajet and trajet.conducteur_id == self.id:
            db.session.delete(trajet)
            db.session.commit()
            return True
        return False
    
    def accepter_reservation(self, reservation_id):
        reservation = Reservation.query.get(reservation_id)
        if reservation and reservation.trajet.conducteur_id == self.id:
            reservation.statut = 'confirmee'
            db.session.commit()
            return True
        return False
    
    def refuser_reservation(self, reservation_id):
        reservation = Reservation.query.get(reservation_id)
        if reservation and reservation.trajet.conducteur_id == self.id:
            reservation.statut = 'refusee'
            db.session.commit()
            return True
        return False


# ============================================
# CLASSE PASSAGER
# ============================================
class Passager(Utilisateur):
    __tablename__ = 'passagers'
    
    id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), primary_key=True)
    reservations = db.relationship('Reservation', backref='passager', lazy=True)
    
    def __init__(self, nom, email, telephone, mot_de_passe):
        super().__init__(nom, email, telephone, mot_de_passe, 'passager')
    
    def rechercher_trajet(self, depart, arrivee, date):
        return Trajet.query.filter_by(
            depart=depart,
            arrivee=arrivee,
            date=date
        ).filter(Trajet.places_disponibles > 0).all()
    
    def reserver_place(self, trajet_id):
        trajet = Trajet.query.get(trajet_id)
        if trajet and trajet.places_disponibles > 0:
            reservation = Reservation(
                passager_id=self.id,
                trajet_id=trajet_id,
                statut='en_attente'
            )
            trajet.places_disponibles -= 1
            db.session.add(reservation)
            db.session.commit()
            return reservation
        return None
    
    def annuler_reservation(self, reservation_id):
        reservation = Reservation.query.get(reservation_id)
        if reservation and reservation.passager_id == self.id and reservation.statut == 'en_attente':
            trajet = reservation.trajet
            trajet.places_disponibles += 1
            reservation.statut = 'annulee'
            db.session.commit()
            return True
        return False
    
    def consulter_historique(self):
        return Reservation.query.filter_by(passager_id=self.id).all()


# ============================================
# CLASSE TRAJET
# ============================================
class Trajet(db.Model):
    __tablename__ = 'trajets'
    
    id = db.Column(db.Integer, primary_key=True)
    conducteur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    depart = db.Column(db.String(200), nullable=False)
    arrivee = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    heure = db.Column(db.String(10), nullable=False)
    places_disponibles = db.Column(db.Integer, nullable=False)
    places_initiales = db.Column(db.Integer, nullable=False)
    prix = db.Column(db.Float, nullable=False)
    
    reservations = db.relationship('Reservation', backref='trajet', lazy=True)


# ============================================
# CLASSE RESERVATION
# ============================================
class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    passager_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    trajet_id = db.Column(db.Integer, db.ForeignKey('trajets.id'), nullable=False)
    statut = db.Column(db.String(20), default='en_attente')
    date_reservation = db.Column(db.DateTime, default=datetime.now)
    
    messages = db.relationship('Message', backref='reservation', lazy=True)


# ============================================
# CLASSE MESSAGE
# ============================================
class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'), nullable=True)  # Now optional for direct messages
    expediteur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    destinataire_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=True)  # For direct messages
    contenu = db.Column(db.String(500), nullable=False)
    date_envoi = db.Column(db.DateTime, default=datetime.now)
    lu = db.Column(db.Boolean, default=False)
    
    # Relations
    expediteur = db.relationship('Utilisateur', foreign_keys=[expediteur_id])
    destinataire = db.relationship('Utilisateur', foreign_keys=[destinataire_id])


# ============================================
# CLASSE AVIS
# ============================================
class Avis(db.Model):
    __tablename__ = 'avis'
    
    id = db.Column(db.Integer, primary_key=True)
    auteur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    cible_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    note = db.Column(db.Integer, nullable=False)
    commentaire = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.now)