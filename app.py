# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from database import init_db
from models import db, Utilisateur, Conducteur, Passager, Trajet, Reservation, Message
from cities_data import get_cities, get_universities_by_city, validate_city_university
from datetime import datetime, date
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'eduCovoit_secret_key_2024_tunisia'

init_db(app)

# Configure Socket.IO with proper CORS and async mode
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    manage_session=False,  # Let Flask-Login manage the session
    ping_timeout=60,
    ping_interval=25,
    logger=True,
    engineio_logger=True
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'connexion'

@login_manager.user_loader
def load_user(user_id):
    return Utilisateur.query.get(int(user_id))

# ============================================
# API ENDPOINTS FOR CITIES AND UNIVERSITIES
# ============================================

@app.route('/api/get_cities')
def api_get_cities():
    """Return list of all available cities"""
    return jsonify({'cities': get_cities()})

@app.route('/api/get_universities/<city>')
def api_get_universities(city):
    """Return universities for a given city"""
    universities = get_universities_by_city(city)
    return jsonify({'universities': universities})

# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def get_current_date():
    return date.today().strftime('%Y-%m-%d')

# ============================================
# ROUTES PRINCIPALES
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        nom = request.form['nom']
        email = request.form['email']
        telephone = request.form['telephone']
        mot_de_passe = request.form['mot_de_passe']
        type_utilisateur = request.form['type_utilisateur']
        
        if Utilisateur.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé', 'danger')
            return redirect(url_for('inscription'))
        
        hashed_password = bcrypt.hashpw(mot_de_passe.encode('utf-8'), bcrypt.gensalt())
        
        if type_utilisateur == 'conducteur':
            utilisateur = Conducteur(nom, email, telephone, hashed_password.decode('utf-8'))
        else:
            utilisateur = Passager(nom, email, telephone, hashed_password.decode('utf-8'))
        
        db.session.add(utilisateur)
        db.session.commit()
        
        flash('Inscription réussie ! Connectez-vous.', 'success')
        return redirect(url_for('connexion'))
    
    return render_template('inscription.html')

@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']
        
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        
        if utilisateur and bcrypt.checkpw(mot_de_passe.encode('utf-8'), utilisateur.mot_de_passe.encode('utf-8')):
            login_user(utilisateur)
            flash(f'Bienvenue {utilisateur.nom} !', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou mot de passe incorrect', 'danger')
    
    return render_template('connexion.html')

@app.route('/deconnexion')
@login_required
def deconnexion():
    logout_user()
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('index'))

# ============================================
# TABLEAU DE BORD
# ============================================

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.type_utilisateur == 'conducteur':
        trajets = Trajet.query.filter_by(conducteur_id=current_user.id).order_by(Trajet.date).all()
        reservations_attendues = []
        for trajet in trajets:
            for res in trajet.reservations:
                if res.statut == 'en_attente':
                    reservations_attendues.append(res)
        
        # Récupérer les chats actifs pour le conducteur
        chats_actifs = []
        for trajet in trajets:
            for res in trajet.reservations:
                if res.statut == 'confirmee':
                    messages_non_lus = Message.query.filter_by(
                        reservation_id=res.id, 
                        lu=False
                    ).filter(Message.expediteur_id != current_user.id).count()
                    chats_actifs.append({
                        'reservation': res,
                        'messages_non_lus': messages_non_lus
                    })
        
        return render_template('dashboard.html', 
                             trajets=trajets, 
                             reservations_attendues=reservations_attendues,
                             chats_actifs=chats_actifs,
                             type_user='conducteur',
                             today=get_current_date())
    else:
        reservations = Reservation.query.filter_by(passager_id=current_user.id).order_by(Reservation.date_reservation.desc()).all()
        
        # Récupérer les chats actifs pour le passager
        chats_actifs = []
        for res in reservations:
            if res.statut == 'confirmee':
                messages_non_lus = Message.query.filter_by(
                    reservation_id=res.id, 
                    lu=False
                ).filter(Message.expediteur_id != current_user.id).count()
                chats_actifs.append({
                    'reservation': res,
                    'messages_non_lus': messages_non_lus
                })
        
        return render_template('dashboard.html', 
                             reservations=reservations,
                             chats_actifs=chats_actifs,
                             type_user='passager',
                             today=get_current_date())

# ============================================
# GESTION DES TRAJETS (CONDUCTEUR)
# ============================================

@app.route('/publier_trajet', methods=['GET', 'POST'])
@login_required
def publier_trajet():
    if current_user.type_utilisateur != 'conducteur':
        flash('Seuls les conducteurs peuvent publier des trajets', 'warning')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        depart = request.form['depart']
        arrivee = request.form['arrivee']
        date_trajet = request.form['date']
        heure = request.form['heure']
        places = int(request.form['places'])
        prix = float(request.form['prix'])
        
        # Validate city and university
        if not validate_city_university(depart, arrivee):
            flash('La destination sélectionnée n\'est pas disponible pour la ville de départ choisie', 'danger')
            return redirect(url_for('publier_trajet'))
        
        # Vérifier que la date n'est pas passée
        if date_trajet < get_current_date():
            flash('Impossible de publier un trajet avec une date passée', 'danger')
            return redirect(url_for('publier_trajet'))
        
        conducteur = Conducteur.query.get(current_user.id)
        conducteur.publier_trajet(depart, arrivee, date_trajet, heure, places, prix)
        
        flash('Trajet publié avec succès !', 'success')
        return redirect(url_for('dashboard'))
    
    cities = get_cities()
    return render_template('publier_trajet.html', today=get_current_date(), cities=cities)

@app.route('/gestion_trajets')
@login_required
def gestion_trajets():
    if current_user.type_utilisateur != 'conducteur':
        return redirect(url_for('dashboard'))
    trajets = Trajet.query.filter_by(conducteur_id=current_user.id).order_by(Trajet.date).all()
    return render_template('gestion_trajets.html', trajets=trajets, today=get_current_date())

@app.route('/modifier_trajet/<int:trajet_id>', methods=['GET', 'POST'])
@login_required
def modifier_trajet(trajet_id):
    trajet = Trajet.query.get_or_404(trajet_id)
    if trajet.conducteur_id != current_user.id:
        flash('Vous ne pouvez pas modifier ce trajet', 'danger')
        return redirect(url_for('gestion_trajets'))
    
    if request.method == 'POST':
        nouvelle_date = request.form['date']
        depart = request.form['depart']
        arrivee = request.form['arrivee']
        
        # Validate city and university
        if not validate_city_university(depart, arrivee):
            flash('La destination sélectionnée n\'est pas disponible pour la ville de départ choisie', 'danger')
            return redirect(url_for('modifier_trajet', trajet_id=trajet_id))
        
        if nouvelle_date < get_current_date():
            flash('Impossible de modifier avec une date passée', 'danger')
            return redirect(url_for('modifier_trajet', trajet_id=trajet_id))
        
        trajet.depart = depart
        trajet.arrivee = arrivee
        trajet.date = nouvelle_date
        trajet.heure = request.form['heure']
        trajet.places_disponibles = int(request.form['places'])
        trajet.prix = float(request.form['prix'])
        db.session.commit()
        flash('Trajet modifié avec succès', 'success')
        return redirect(url_for('gestion_trajets'))
    
    cities = get_cities()
    return render_template('modifier_trajet.html', trajet=trajet, today=get_current_date(), cities=cities)

@app.route('/supprimer_trajet/<int:trajet_id>')
@login_required
def supprimer_trajet(trajet_id):
    trajet = Trajet.query.get_or_404(trajet_id)
    if trajet.conducteur_id != current_user.id:
        flash('Vous ne pouvez pas supprimer ce trajet', 'danger')
        return redirect(url_for('gestion_trajets'))
    
    db.session.delete(trajet)
    db.session.commit()
    flash('Trajet supprimé', 'success')
    return redirect(url_for('gestion_trajets'))

# ============================================
# RECHERCHE ET RÉSERVATION (PASSAGER)
# ============================================

@app.route('/rechercher', methods=['GET', 'POST'])
@login_required
def rechercher():
    trajets = []
    if request.method == 'POST':
        depart = request.form.get('depart', '').strip()
        arrivee = request.form.get('arrivee', '').strip()
        date_recherche = request.form.get('date', '').strip()
        
        if date_recherche < get_current_date():
            flash('Vous ne pouvez pas rechercher des trajets avec une date passée', 'warning')
        else:
            # Only search if both departure and arrival are provided
            if depart and arrivee:
                passager = Passager.query.get(current_user.id)
                trajets = passager.rechercher_trajet(depart, arrivee, date_recherche)
            else:
                flash('Veuillez sélectionner une ville de départ et une destination', 'warning')
    
    cities = get_cities()
    return render_template('rechercher.html', trajets=trajets, today=get_current_date(), cities=cities)

@app.route('/reserver/<int:trajet_id>')
@login_required
def reserver(trajet_id):
    if current_user.type_utilisateur != 'passager':
        flash('Seuls les passagers peuvent réserver', 'warning')
        return redirect(url_for('dashboard'))
    
    trajet = Trajet.query.get_or_404(trajet_id)
    
    if trajet.date < get_current_date():
        flash('Impossible de réserver un trajet avec une date passée', 'danger')
        return redirect(url_for('rechercher'))
    
    passager = Passager.query.get(current_user.id)
    reservation = passager.reserver_place(trajet_id)
    
    if reservation:
        flash('Réservation effectuée ! En attente de confirmation.', 'success')
    else:
        flash('Plus de places disponibles', 'danger')
    
    return redirect(url_for('rechercher'))

@app.route('/mes_reservations')
@login_required
def mes_reservations():
    if current_user.type_utilisateur != 'passager':
        return redirect(url_for('dashboard'))
    
    passager = Passager.query.get(current_user.id)
    reservations = passager.consulter_historique()
    return render_template('mes_reservations.html', 
                         reservations=reservations, 
                         now=date.today())

@app.route('/annuler_reservation/<int:reservation_id>')
@login_required
def annuler_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if reservation.passager_id != current_user.id:
        flash('Vous ne pouvez pas annuler cette réservation', 'danger')
        return redirect(url_for('dashboard'))
    
    passager = Passager.query.get(current_user.id)
    passager.annuler_reservation(reservation_id)
    
    flash('Réservation annulée', 'info')
    return redirect(url_for('mes_reservations'))

# ============================================
# GESTION DES RÉSERVATIONS (CONDUCTEUR)
# ============================================

@app.route('/gerer_reservations')
@login_required
def gerer_reservations():
    if current_user.type_utilisateur != 'conducteur':
        return redirect(url_for('dashboard'))
    
    trajets = Trajet.query.filter_by(conducteur_id=current_user.id).all()
    demandes = []
    for trajet in trajets:
        for res in trajet.reservations:
            if res.statut == 'en_attente':
                demandes.append(res)
    
    return render_template('gerer_reservations.html', demandes=demandes)

@app.route('/accepter_reservation/<int:reservation_id>')
@login_required
def accepter_reservation(reservation_id):
    conducteur = Conducteur.query.get(current_user.id)
    if conducteur.accepter_reservation(reservation_id):
        flash('Réservation acceptée', 'success')
    else:
        flash('Erreur lors de l\'acceptation', 'danger')
    return redirect(url_for('gerer_reservations'))

@app.route('/refuser_reservation/<int:reservation_id>')
@login_required
def refuser_reservation(reservation_id):
    conducteur = Conducteur.query.get(current_user.id)
    if conducteur.refuser_reservation(reservation_id):
        flash('Réservation refusée', 'info')
    else:
        flash('Erreur lors du refus', 'danger')
    return redirect(url_for('gerer_reservations'))

# ============================================
# CHAT EN TEMPS RÉEL (Socket.IO)
# ============================================

@app.route('/chat/<int:reservation_id>')
@login_required
def chat(reservation_id):
    """Page de chat pour une réservation confirmée"""
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if reservation.passager_id != current_user.id and reservation.trajet.conducteur_id != current_user.id:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard'))
    
    if reservation.statut != 'confirmee':
        flash('Le chat n\'est disponible qu\'après confirmation de la réservation', 'warning')
        return redirect(url_for('dashboard'))
    
    Message.query.filter_by(
        reservation_id=reservation_id, 
        lu=False
    ).filter(Message.expediteur_id != current_user.id).update({'lu': True}, synchronize_session='fetch')
    db.session.commit()
    
    messages = Message.query.filter_by(reservation_id=reservation_id).order_by(Message.date_envoi).all()
    autre_participant = reservation.passager if current_user.id == reservation.trajet.conducteur_id else reservation.trajet.conducteur
    
    return render_template('chat.html', 
                         reservation=reservation, 
                         messages=messages,
                         autre_participant=autre_participant)

@app.route('/chats')
@login_required
def chats():
    """Page listing all conversations for the current user"""
    conversations = []
    
    # Get reservation-based chats
    if current_user.type_utilisateur == 'conducteur':
        trajets = Trajet.query.filter_by(conducteur_id=current_user.id).all()
        for trajet in trajets:
            for res in trajet.reservations:
                if res.statut == 'confirmee':
                    messages_non_lus = Message.query.filter_by(
                        reservation_id=res.id, 
                        lu=False
                    ).filter(Message.expediteur_id != current_user.id).count()
                    conversations.append({
                        'type': 'reservation',
                        'id': res.id,
                        'reservation': res,
                        'autre_participant': res.passager,
                        'messages_non_lus': messages_non_lus,
                        'trajet': trajet
                    })
    else:  # passager
        reservations = Reservation.query.filter_by(passager_id=current_user.id).filter(
            Reservation.statut == 'confirmee'
        ).all()
        for res in reservations:
            messages_non_lus = Message.query.filter_by(
                reservation_id=res.id, 
                lu=False
            ).filter(Message.expediteur_id != current_user.id).count()
            conversations.append({
                'type': 'reservation',
                'id': res.id,
                'reservation': res,
                'autre_participant': res.trajet.conducteur,
                'messages_non_lus': messages_non_lus,
                'trajet': res.trajet
            })
    
    # Get direct message conversations
    direct_messages = Message.query.filter(
        db.or_(
            Message.expediteur_id == current_user.id,
            Message.destinataire_id == current_user.id
        ),
        Message.reservation_id.is_(None)
    ).order_by(Message.date_envoi.desc()).all()
    
    direct_convs = {}
    for msg in direct_messages:
        other_user_id = msg.destinataire_id if msg.expediteur_id == current_user.id else msg.expediteur_id
        if other_user_id not in direct_convs:
            other_user = Utilisateur.query.get(other_user_id)
            direct_convs[other_user_id] = {
                'type': 'direct',
                'id': other_user_id,
                'autre_participant': other_user,
                'messages_non_lus': 0,
                'last_message_date': msg.date_envoi  # Store date from most recent message (first in desc order)
            }
        
        
        if msg.expediteur_id != current_user.id and not msg.lu:
            direct_convs[other_user_id]['messages_non_lus'] += 1
    
    conversations.extend(direct_convs.values())
    
    # Sort by most recent message - direct chats by last_message_date, reservation chats by reservation date
    def get_sort_date(conv):
        if conv.get('type') == 'direct':
            return conv.get('last_message_date', datetime.min)
        else:
            return conv.get('reservation').date_reservation if conv.get('reservation') else datetime.min
    
    conversations.sort(key=get_sort_date, reverse=True)
    
    return render_template('chats.html', conversations=conversations)

@app.route('/direct_chat/<int:user_id>')
@login_required
def direct_chat(user_id):
    """Page for direct messaging with a user"""
    autre_user = Utilisateur.query.get_or_404(user_id)
    
    if user_id == current_user.id:
        flash('Vous ne pouvez pas vous envoyer de message', 'danger')
        return redirect(url_for('chats'))
    
    # Mark messages as read
    Message.query.filter_by(
        destinataire_id=current_user.id,
        expediteur_id=user_id,
        reservation_id=None,
        lu=False
    ).update({'lu': True}, synchronize_session='fetch')
    db.session.commit()
    
    # Get messages between these users
    messages = Message.query.filter(
        db.and_(
            db.or_(
                db.and_(Message.expediteur_id == current_user.id, Message.destinataire_id == user_id),
                db.and_(Message.expediteur_id == user_id, Message.destinataire_id == current_user.id)
            ),
            Message.reservation_id.is_(None)
        )
    ).order_by(Message.date_envoi).all()
    
    # Create the direct chat ID (sorted user IDs)
    direct_chat_id = create_direct_chat_id(current_user.id, user_id)
    
    return render_template('direct_chat.html',
                         autre_participant=autre_user,
                         messages=messages,
                         direct_chat_id=direct_chat_id)

@app.route('/contact_driver/<int:trajet_id>')
@login_required
def contact_driver(trajet_id):
    """Route to contact the driver of a trip from search results"""
    if current_user.type_utilisateur != 'passager':
        flash('Seuls les passagers peuvent contacter les conducteurs', 'warning')
        return redirect(url_for('dashboard'))
    
    trajet = Trajet.query.get_or_404(trajet_id)
    driver = trajet.conducteur
    
    # Redirect to direct chat
    return redirect(url_for('direct_chat', user_id=driver.id))


def create_direct_chat_id(user_id1, user_id2):
    """Create a direct chat ID from two user IDs (sorted).
    
    IDs are sorted to ensure consistent room identifiers regardless of
    which user initiates the conversation.
    
    Args:
        user_id1: First user ID
        user_id2: Second user ID
        
    Returns:
        String in format 'min_id_max_id' (e.g., '1_42')
    """
    return f"{min(user_id1, user_id2)}_{max(user_id1, user_id2)}"

@socketio.on('connect')
def handle_connect():
    """Quand un utilisateur se connecte au socket"""
    if current_user.is_authenticated:
        print(f"✅ Nouvelle connexion Socket.IO - Utilisateur: {current_user.nom}")
    else:
        print("❌ Tentative de connexion Socket.IO non authentifiée")
        return False  # Reject the connection if user is not authenticated

@socketio.on('disconnect')
def handle_disconnect():
    """Quand un utilisateur se déconnecte"""
    if current_user.is_authenticated:
        print(f"👋 Déconnexion Socket.IO - Utilisateur: {current_user.nom}")
    else:
        print("❌ Déconnexion Socket.IO (non authentifié)")

@socketio.on('join_chat')
def handle_join_chat(data):
    """Rejoindre une room de chat"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Non authentifié'})
            return
        
        reservation_id = data.get('reservation_id')
        direct_chat_id = data.get('direct_chat_id')  # Format: "user1_user2" (sorted)
        
        if reservation_id:
            # Validate user has access to this reservation
            reservation = Reservation.query.get(reservation_id)
            if not reservation:
                emit('error', {'message': 'Réservation non trouvée'})
                return
            
            if reservation.passager_id != current_user.id and reservation.trajet.conducteur_id != current_user.id:
                emit('error', {'message': 'Accès non autorisé à cette réservation'})
                return
            
            join_room(str(reservation_id))
            print(f"📢 {current_user.nom} a rejoint le chat {reservation_id}")
            emit('chat_joined', {'message': f'{current_user.nom} a rejoint le chat'}, room=str(reservation_id))
            
        elif direct_chat_id:
            # Validate direct chat ID
            chat_ids = direct_chat_id.split('_')
            if len(chat_ids) != 2:
                emit('error', {'message': 'Format de chat direct invalide'})
                return
            
            try:
                chat_id_list = [int(id_str) for id_str in chat_ids]
            except ValueError:
                emit('error', {'message': 'Format des IDs de chat invalide'})
                return
            
            if current_user.id not in chat_id_list:
                emit('error', {'message': 'Utilisateur non autorisé pour ce chat'})
                return
            
            join_room(str(direct_chat_id))
            print(f"📢 {current_user.nom} a rejoint le chat direct {direct_chat_id}")
            emit('chat_joined', {'message': f'{current_user.nom} a rejoint le chat'}, room=str(direct_chat_id))
        else:
            emit('error', {'message': 'Mode de chat invalide'})
            
    except Exception as e:
        print(f"Erreur join_chat: {e}")
        emit('error', {'message': f'Erreur: {str(e)}'})

@socketio.on('send_message')
def handle_send_message(data):
    """Envoyer un message dans le chat"""
    try:
        if not current_user.is_authenticated:
            emit('error', {'message': 'Non authentifié'})
            return
        
        reservation_id = data.get('reservation_id')
        direct_chat_id = data.get('direct_chat_id')
        message_content = data.get('message', '').strip()
        user_id = data.get('user_id')
        destinataire_id = data.get('destinataire_id')  # For direct messages
        
        # Verify the request is coming from the authenticated user
        if int(user_id) != current_user.id:
            print(f"Tentative d'envoi de message avec un user_id différent: {user_id} vs {current_user.id}")
            emit('error', {'message': 'Utilisateur non autorisé'})
            return
        
        if not message_content:
            emit('error', {'message': 'Message vide'})
            return
        
        if len(message_content) > 500:
            message_content = message_content[:500]
        
        if reservation_id:
            # Reservation-based message - validate access
            reservation = Reservation.query.get(reservation_id)
            if not reservation:
                emit('error', {'message': 'Réservation non trouvée'})
                return
            
            if reservation.passager_id != current_user.id and reservation.trajet.conducteur_id != current_user.id:
                print(f"Accès non autorisé à la réservation {reservation_id}")
                emit('error', {'message': 'Accès non autorisé à cette réservation'})
                return
            
            message = Message(
                reservation_id=reservation_id,
                expediteur_id=current_user.id,
                contenu=message_content,
                lu=False
            )
            room = str(reservation_id)
        elif direct_chat_id and destinataire_id:
            # Direct message - validate that user is authorized
            
            try:
                destinataire_id_int = int(destinataire_id)
            except (ValueError, TypeError):
                print("destinataire_id invalide")
                emit('error', {'message': 'ID destinataire invalide'})
                return
            
            # Validate direct_chat_id format (should be "id1_id2" with sorted IDs)
            chat_ids = direct_chat_id.split('_')
            if len(chat_ids) != 2:
                print("Format de chat direct invalide (attendu: user_id1_user_id2)")
                emit('error', {'message': 'Format de chat direct invalide'})
                return
            
            # Parse chat IDs and verify user is a participant
            try:
                chat_id_list = [int(id_str) for id_str in chat_ids]
            except ValueError:
                print("Format des IDs de chat invalide")
                emit('error', {'message': 'Format des IDs de chat invalide'})
                return
            
            if current_user.id not in chat_id_list or destinataire_id_int not in chat_id_list:
                print("Utilisateur non autorisé pour ce chat")
                emit('error', {'message': 'Utilisateur non autorisé pour ce chat'})
                return
            
            expected_chat_id = create_direct_chat_id(current_user.id, destinataire_id_int)
            
            if direct_chat_id != expected_chat_id:
                print("ID de chat direct invalide")
                emit('error', {'message': 'ID de chat direct invalide'})
                return
            
            message = Message(
                reservation_id=None,
                expediteur_id=current_user.id,
                destinataire_id=destinataire_id_int,
                contenu=message_content,
                lu=False
            )
            room = str(direct_chat_id)
        else:
            print("Mode de chat invalide")
            emit('error', {'message': 'Mode de chat invalide'})
            return
        
        db.session.add(message)
        db.session.commit()
        
        message_data = {
            'expediteur_id': current_user.id,
            'expediteur_nom': current_user.nom,
            'contenu': message_content,
            'date_envoi': datetime.now().strftime('%H:%M')
        }
        
        emit('new_message', message_data, room=room)
        print(f"💬 Message de {current_user.nom}: {message_content[:50]}")
        
    except Exception as e:
        print(f"❌ Erreur send_message: {e}")
        db.session.rollback()
        emit('error', {'message': f'Erreur lors de l\'envoi du message: {str(e)}'})

@socketio.on('leave_chat')
def handle_leave_chat(data):
    """Quitter une room de chat"""
    try:
        if not current_user.is_authenticated:
            return
        
        reservation_id = data.get('reservation_id')
        direct_chat_id = data.get('direct_chat_id')
        
        if reservation_id:
            leave_room(str(reservation_id))
            print(f"👋 {current_user.nom} a quitté le chat {reservation_id}")
        elif direct_chat_id:
            leave_room(str(direct_chat_id))
            print(f"👋 {current_user.nom} a quitté le chat direct {direct_chat_id}")
    except Exception as e:
        print(f"Erreur leave_chat: {e}")

# ============================================
# NOTATION / ÉVALUATION
# ============================================

@app.route('/noter/<int:reservation_id>/<string:type_note>')
@login_required
def noter(reservation_id, type_note):
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if type_note == 'conducteur':
        if reservation.passager_id != current_user.id:
            flash('Vous ne pouvez pas noter ce conducteur', 'danger')
            return redirect(url_for('dashboard'))
        cible = reservation.trajet.conducteur
    else:
        if reservation.trajet.conducteur_id != current_user.id:
            flash('Vous ne pouvez pas noter ce passager', 'danger')
            return redirect(url_for('dashboard'))
        cible = reservation.passager
    
    return render_template('noter.html', cible=cible, reservation=reservation, type_note=type_note)

@app.route('/soumettre_note/<int:reservation_id>/<string:type_note>', methods=['POST'])
@login_required
def soumettre_note(reservation_id, type_note):
    reservation = Reservation.query.get_or_404(reservation_id)
    note = int(request.form['note'])
    commentaire = request.form.get('commentaire', '')
    
    if type_note == 'conducteur':
        if reservation.passager_id != current_user.id:
            flash('Action non autorisée', 'danger')
            return redirect(url_for('dashboard'))
        cible_id = reservation.trajet.conducteur_id
    else:
        if reservation.trajet.conducteur_id != current_user.id:
            flash('Action non autorisée', 'danger')
            return redirect(url_for('dashboard'))
        cible_id = reservation.passager_id
    
    current_user.noter_utilisateur(cible_id, note, commentaire)
    reservation.statut = 'terminee'
    db.session.commit()
    
    flash('Merci pour votre évaluation !', 'success')
    return redirect(url_for('dashboard'))

# ============================================
# PROFIL UTILISATEUR
# ============================================

@app.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    if request.method == 'POST':
        current_user.nom = request.form['nom']
        current_user.telephone = request.form['telephone']
        db.session.commit()
        flash('Profil mis à jour', 'success')
    
    return render_template('profil.html', utilisateur=current_user)

# ============================================
# GESTION DES ERREURS
# ============================================

@app.errorhandler(404)
def page_not_found(error):
    """Gérer les pages non trouvées"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Gérer les erreurs serveur"""
    db.session.rollback()
    return render_template('500.html'), 500

# ============================================
# LANCEMENT
# ============================================

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)