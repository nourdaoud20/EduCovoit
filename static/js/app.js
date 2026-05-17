/* ============================================
   MODERN EDUCOVOIT JAVASCRIPT
   ============================================ */

// Initialize socket.io for real-time features
let socket = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Socket.IO if available
    if (typeof io !== 'undefined') {
        socket = io({
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: Infinity,
            transports: ['websocket', 'polling']
        });
        setupSocketListeners();
    }
    
    // Initialize tooltips and popovers
    initializeTooltips();
    
    // Add form validation
    initializeFormValidation();
    
    // Add smooth scrolling
    initializeSmoothScroll();
    
    // Initialize notifications
    initializeNotifications();
});

/* ============================================
   SOCKET.IO LISTENERS
   ============================================ */

function setupSocketListeners() {
    // Connection events
    socket.on('connect', function() {
        console.log('✅ Socket.IO connected');
    });
    
    socket.on('disconnect', function() {
        console.log('❌ Socket.IO disconnected, attempting to reconnect...');
    });
    
    socket.on('connect_error', function(error) {
        console.error('Socket.IO connection error:', error);
    });
    
    socket.on('error', function(error) {
        console.error('Socket.IO error:', error);
    });
    
    // Listen for chat notifications
    socket.on('chat_notification', function(data) {
        showNotification('message', `${data.expediteur_nom} vous a envoyé un message`, data.message_court);
    });
    
    // Listen for reservation updates
    socket.on('reservation_update', function(data) {
        showNotification('info', 'Mise à jour de réservation', data.message);
    });
    
    // Listen for trip updates
    socket.on('trip_update', function(data) {
        showNotification('info', 'Mise à jour de trajet', data.message);
    });
}

/* ============================================
   NOTIFICATION SYSTEM
   ============================================ */

function showNotification(type, title, message) {
    const notificationId = 'notification-' + Date.now();
    const icon = getNotificationIcon(type);
    const bgClass = getNotificationClass(type);
    
    const notification = document.createElement('div');
    notification.id = notificationId;
    notification.className = `alert ${bgClass} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 500px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        border-radius: 12px;
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: flex-start; gap: 12px;">
            <i class="${icon}" style="font-size: 1.25em; margin-top: 2px; flex-shrink: 0;"></i>
            <div style="flex-grow: 1;">
                <strong>${title}</strong>
                <p style="margin: 0.5rem 0 0 0; font-size: 0.95rem;">${message}</p>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (document.getElementById(notificationId)) {
            notification.remove();
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle',
        'message': 'fas fa-comment-dots'
    };
    return icons[type] || icons['info'];
}

function getNotificationClass(type) {
    const classes = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info',
        'message': 'alert-info'
    };
    return classes[type] || classes['info'];
}

function initializeNotifications() {
    // Auto-dismiss existing alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (alert.classList.contains('fade-in')) {
            setTimeout(() => {
                const closeBtn = alert.querySelector('.btn-close');
                if (closeBtn) {
                    closeBtn.click();
                }
            }, 5000);
        }
    });
}

/* ============================================
   FORM VALIDATION
   ============================================ */

function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

/* ============================================
   TOOLTIPS & POPOVERS
   ============================================ */

function initializeTooltips() {
    // Add tooltips to elements with data-bs-toggle="tooltip"
    const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipElements.forEach(element => {
        element.setAttribute('title', element.getAttribute('data-bs-title') || '');
    });
}

/* ============================================
   SMOOTH SCROLLING
   ============================================ */

function initializeSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

/* ============================================
   CONFIRMATION DIALOGS
   ============================================ */

function confirmAction(message = 'Êtes-vous sûr ?') {
    return confirm(message);
}

function deleteWithConfirmation(deleteUrl) {
    if (confirmAction('Êtes-vous sûr de vouloir supprimer cet élément ?')) {
        window.location.href = deleteUrl;
    }
}

function cancelWithConfirmation(cancelUrl) {
    if (confirmAction('Êtes-vous sûr de vouloir annuler ? Cette action ne peut pas être annulée.')) {
        window.location.href = cancelUrl;
    }
}

/* ============================================
   CHAT UTILITIES
   ============================================ */

function joinChat(reservationId) {
    if (socket) {
        socket.emit('join_chat', { reservation_id: reservationId });
    }
}

function leaveChat(reservationId) {
    if (socket) {
        socket.emit('leave_chat', { reservation_id: reservationId });
    }
}

function sendMessage(reservationId, userId, messageContent) {
    if (socket) {
        socket.emit('send_message', {
            reservation_id: reservationId,
            user_id: userId,
            message: messageContent
        });
    }
}

function autoScrollChatToBottom() {
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

/* ============================================
   FAVORITES / WISHLIST
   ============================================ */

function toggleFavorite(tripId, element) {
    // This would connect to a backend endpoint to save favorites
    element.classList.toggle('active');
    if (element.classList.contains('active')) {
        element.innerHTML = '<i class="fas fa-heart"></i>';
        element.style.color = '#E70A13';
    } else {
        element.innerHTML = '<i class="far fa-heart"></i>';
        element.style.color = '#999';
    }
}

/* ============================================
   SEARCH FILTERS
   ============================================ */

function applyFilters() {
    const filters = {
        priceMin: document.getElementById('price-min')?.value || 0,
        priceMax: document.getElementById('price-max')?.value || 1000,
        timeMin: document.getElementById('time-min')?.value || '00:00',
        timeMax: document.getElementById('time-max')?.value || '23:59'
    };
    
    // Filter the trips display
    const trips = document.querySelectorAll('.trip-card');
    trips.forEach(trip => {
        const price = parseFloat(trip.dataset.price);
        const time = trip.dataset.time;
        
        const priceMatch = price >= filters.priceMin && price <= filters.priceMax;
        const timeMatch = time >= filters.timeMin && time <= filters.timeMax;
        
        if (priceMatch && timeMatch) {
            trip.style.display = 'block';
        } else {
            trip.style.display = 'none';
        }
    });
}

/* ============================================
   LOADING STATES
   ============================================ */

function setLoadingState(buttonElement, isLoading) {
    if (isLoading) {
        buttonElement.disabled = true;
        buttonElement.innerHTML = `<span class="spinner" style="display: inline-block; width: 16px; height: 16px; border: 2px solid #f3f3f3; border-top: 2px solid #003F87; border-radius: 50%;"></span> Chargement...`;
    } else {
        buttonElement.disabled = false;
        // Reset to original content (you may need to store it)
        buttonElement.innerHTML = buttonElement.dataset.originalContent || 'Envoyer';
    }
}

/* ============================================
   RATING DISPLAY
   ============================================ */

function displayStarRating(rating, container) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        if (i <= Math.round(rating)) {
            stars += '<i class="fas fa-star" style="color: #ffc107;"></i>';
        } else {
            stars += '<i class="far fa-star" style="color: #ccc;"></i>';
        }
    }
    if (container) {
        container.innerHTML = stars + ` <span style="margin-left: 8px; color: #666;">${rating.toFixed(1)}/5</span>`;
    }
    return stars;
}

/* ============================================
   RESPONSIVE UTILITIES
   ============================================ */

function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

function isTabletDevice() {
    return /iPad|Android/i.test(navigator.userAgent);
}

/* ============================================
   ANIMATION UTILITIES
   ============================================ */

function animateElement(element, animationName, duration = 500) {
    element.style.animation = `${animationName} ${duration}ms ease-out`;
    setTimeout(() => {
        element.style.animation = '';
    }, duration);
}

function fadeInElement(element, duration = 500) {
    animateElement(element, 'fadeIn', duration);
}

/* ============================================
   DATETIME UTILITIES
   ============================================ */

function formatTime(time) {
    if (!time) return '';
    const [hours, minutes] = time.split(':');
    return `${hours}:${minutes}`;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', { 
        weekday: 'short', 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function getTimeUntil(dateTimeString) {
    const now = new Date();
    const eventTime = new Date(dateTimeString);
    const diff = eventTime - now;
    
    if (diff < 0) return 'Expiré';
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (days > 0) return `${days}j ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
}

/* ============================================
   EXPORT FUNCTIONS
   ============================================ */

window.EduCovoit = {
    showNotification,
    deleteWithConfirmation,
    cancelWithConfirmation,
    joinChat,
    leaveChat,
    sendMessage,
    toggleFavorite,
    applyFilters,
    displayStarRating,
    formatDate,
    formatTime,
    getTimeUntil,
    isMobileDevice,
    isTabletDevice
};
