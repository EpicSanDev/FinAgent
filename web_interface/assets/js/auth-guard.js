/**
 * Auth Guard - Protection des routes et gestion de session
 * Système de protection pour l'accès aux pages sécurisées
 */

class AuthGuard {
    constructor() {
        this.isAuthenticated = false;
        this.currentUser = null;
        this.authToken = null;
        this.sessionTimeout = null;
        this.inactivityTimeout = 30 * 60 * 1000; // 30 minutes
        this.warningTimeout = 5 * 60 * 1000; // 5 minutes avant expiration
        this.lastActivity = Date.now();
        
        this.init();
    }

    /**
     * Initialisation du garde d'authentification
     */
    init() {
        this.checkAuthStatus();
        this.setupInactivityTracking();
        this.setupSessionManagement();
        console.log('Auth Guard initialisé');
    }

    /**
     * Vérification du statut d'authentification
     */
    checkAuthStatus() {
        const token = localStorage.getItem('auth_token');
        const userData = localStorage.getItem('user_data');
        const expirationTime = localStorage.getItem('auth_expires');

        if (token && userData && expirationTime) {
            const now = Date.now();
            const expires = parseInt(expirationTime);

            if (now < expires) {
                // Session valide
                this.authToken = token;
                this.currentUser = JSON.parse(userData);
                this.isAuthenticated = true;
                this.startSessionTimer(expires - now);
                this.updateUserInterface();
                return true;
            } else {
                // Session expirée
                this.logout('Session expirée');
                return false;
            }
        } else {
            // Pas de session
            this.redirectToAuth();
            return false;
        }
    }

    /**
     * Redirection vers la page d'authentification
     */
    redirectToAuth(message = null) {
        let url = 'auth.html';
        
        if (message) {
            url += `?message=${encodeURIComponent(message)}&type=warning`;
        }
        
        // Stockage de la page actuelle pour redirection après connexion
        localStorage.setItem('redirect_after_auth', window.location.pathname + window.location.search);
        
        window.location.href = url;
    }

    /**
     * Déconnexion
     */
    logout(reason = 'Déconnexion') {
        // Nettoyage des données locales
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        localStorage.removeItem('auth_expires');
        localStorage.removeItem('redirect_after_auth');
        
        // Nettoyage de l'état
        this.isAuthenticated = false;
        this.currentUser = null;
        this.authToken = null;
        
        // Arrêt des timers
        if (this.sessionTimeout) {
            clearTimeout(this.sessionTimeout);
        }
        
        // Redirection avec message
        this.redirectToAuth(reason);
    }

    /**
     * Actualisation du token
     */
    async refreshToken() {
        try {
            // Simulation d'appel API pour rafraîchir le token
            const response = await this.makeApiCall('/auth/refresh', {
                token: this.authToken
            });

            if (response.success) {
                // Mise à jour des données d'authentification
                this.authToken = response.data.token;
                localStorage.setItem('auth_token', response.data.token);
                
                const newExpiration = Date.now() + (24 * 60 * 60 * 1000);
                localStorage.setItem('auth_expires', newExpiration.toString());
                
                this.startSessionTimer(24 * 60 * 60 * 1000);
                console.log('Token rafraîchi avec succès');
                return true;
            } else {
                throw new Error('Échec du rafraîchissement du token');
            }
        } catch (error) {
            console.error('Erreur lors du rafraîchissement du token:', error);
            this.logout('Session expirée');
            return false;
        }
    }

    /**
     * Démarrage du timer de session
     */
    startSessionTimer(timeUntilExpiration) {
        // Nettoyage du timer précédent
        if (this.sessionTimeout) {
            clearTimeout(this.sessionTimeout);
        }

        // Timer d'avertissement (5 minutes avant expiration)
        const warningTime = Math.max(0, timeUntilExpiration - this.warningTimeout);
        
        setTimeout(() => {
            this.showSessionWarning();
        }, warningTime);

        // Timer d'expiration
        this.sessionTimeout = setTimeout(() => {
            this.logout('Session expirée');
        }, timeUntilExpiration);
    }

    /**
     * Affichage de l'avertissement de session
     */
    showSessionWarning() {
        const warningModal = this.createSessionWarningModal();
        document.body.appendChild(warningModal);
        
        // Auto-fermeture après 5 minutes si pas d'action
        setTimeout(() => {
            if (document.body.contains(warningModal)) {
                this.logout('Session expirée par inactivité');
            }
        }, this.warningTimeout);
    }

    /**
     * Création de la modal d'avertissement de session
     */
    createSessionWarningModal() {
        const modal = document.createElement('div');
        modal.className = 'session-warning-modal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-clock"></i> Session bientôt expirée</h3>
                </div>
                <div class="modal-body">
                    <p>Votre session expirera dans <span id="countdown">5:00</span>.</p>
                    <p>Souhaitez-vous prolonger votre session ?</p>
                </div>
                <div class="modal-actions">
                    <button class="btn btn-outline" id="logoutNow">Se déconnecter</button>
                    <button class="btn btn-primary" id="extendSession">Prolonger la session</button>
                </div>
            </div>
        `;

        // Styles en ligne pour la modal
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;

        // Gestionnaires d'événements
        modal.querySelector('#extendSession').addEventListener('click', () => {
            this.refreshToken();
            modal.remove();
        });

        modal.querySelector('#logoutNow').addEventListener('click', () => {
            this.logout('Déconnexion manuelle');
        });

        // Compte à rebours
        this.startCountdown(modal.querySelector('#countdown'));

        return modal;
    }

    /**
     * Démarrage du compte à rebours
     */
    startCountdown(element) {
        let timeLeft = this.warningTimeout / 1000; // Convertir en secondes

        const countdown = setInterval(() => {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            element.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            timeLeft--;
            
            if (timeLeft < 0) {
                clearInterval(countdown);
            }
        }, 1000);
    }

    /**
     * Configuration du suivi d'inactivité
     */
    setupInactivityTracking() {
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        
        events.forEach(event => {
            document.addEventListener(event, () => {
                this.updateLastActivity();
            }, true);
        });

        // Vérification périodique d'inactivité
        setInterval(() => {
            this.checkInactivity();
        }, 60000); // Vérifier chaque minute
    }

    /**
     * Mise à jour de la dernière activité
     */
    updateLastActivity() {
        this.lastActivity = Date.now();
    }

    /**
     * Vérification d'inactivité
     */
    checkInactivity() {
        if (!this.isAuthenticated) return;

        const now = Date.now();
        const inactiveTime = now - this.lastActivity;

        if (inactiveTime >= this.inactivityTimeout) {
            this.logout('Déconnexion par inactivité');
        }
    }

    /**
     * Configuration de la gestion de session
     */
    setupSessionManagement() {
        // Gestion de la fermeture de l'onglet/fenêtre
        window.addEventListener('beforeunload', () => {
            // Sauvegarder l'état si nécessaire
            if (this.isAuthenticated) {
                localStorage.setItem('last_active', Date.now().toString());
            }
        });

        // Gestion du changement de visibilité de la page
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Page cachée, pause des timers si nécessaire
                this.updateLastActivity();
            } else {
                // Page visible, vérification de la session
                this.checkAuthStatus();
            }
        });

        // Gestion du stockage local (synchronisation entre onglets)
        window.addEventListener('storage', (e) => {
            if (e.key === 'auth_token' && !e.newValue) {
                // Token supprimé dans un autre onglet
                this.logout('Déconnexion depuis un autre onglet');
            }
        });
    }

    /**
     * Mise à jour de l'interface utilisateur
     */
    updateUserInterface() {
        if (!this.isAuthenticated || !this.currentUser) return;

        // Mise à jour du nom d'utilisateur
        const userNameElements = document.querySelectorAll('.user-name');
        userNameElements.forEach(element => {
            element.textContent = `${this.currentUser.firstName} ${this.currentUser.lastName}`;
        });

        // Mise à jour de l'email
        const userEmailElements = document.querySelectorAll('.user-email');
        userEmailElements.forEach(element => {
            element.textContent = this.currentUser.email;
        });

        // Mise à jour de l'avatar
        const userAvatarElements = document.querySelectorAll('.user-avatar');
        userAvatarElements.forEach(element => {
            if (element.tagName === 'IMG') {
                element.src = this.currentUser.avatar || this.generateAvatarUrl();
            } else {
                element.style.backgroundImage = `url(${this.currentUser.avatar || this.generateAvatarUrl()})`;
            }
        });

        // Affichage des informations utilisateur
        this.displayUserInfo();
    }

    /**
     * Génération d'URL d'avatar par défaut
     */
    generateAvatarUrl() {
        const name = `${this.currentUser.firstName}+${this.currentUser.lastName}`;
        return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=3b82f6&color=fff&size=128`;
    }

    /**
     * Affichage des informations utilisateur
     */
    displayUserInfo() {
        const userInfoContainer = document.querySelector('.user-info');
        if (userInfoContainer && this.currentUser) {
            userInfoContainer.innerHTML = `
                <div class="user-details">
                    <img src="${this.currentUser.avatar || this.generateAvatarUrl()}" 
                         alt="Avatar" class="user-avatar">
                    <div class="user-text">
                        <div class="user-name">${this.currentUser.firstName} ${this.currentUser.lastName}</div>
                        <div class="user-email">${this.currentUser.email}</div>
                    </div>
                </div>
                <div class="user-actions">
                    <button class="btn btn-outline btn-sm" onclick="authGuard.showProfileModal()">
                        <i class="fas fa-user"></i> Profil
                    </button>
                    <button class="btn btn-outline btn-sm" onclick="authGuard.logout('Déconnexion manuelle')">
                        <i class="fas fa-sign-out-alt"></i> Déconnexion
                    </button>
                </div>
            `;
        }
    }

    /**
     * Affichage de la modal de profil
     */
    showProfileModal() {
        // Implémentation de la modal de profil utilisateur
        console.log('Affichage du profil utilisateur');
        // Cette fonctionnalité pourrait être étendue pour permettre la modification du profil
    }

    /**
     * Appel API sécurisé
     */
    async makeApiCall(endpoint, data = {}, method = 'POST') {
        const headers = {
            'Content-Type': 'application/json'
        };

        if (this.authToken) {
            headers['Authorization'] = `Bearer ${this.authToken}`;
        }

        try {
            const response = await fetch(endpoint, {
                method: method,
                headers: headers,
                body: method !== 'GET' ? JSON.stringify(data) : undefined
            });

            if (response.status === 401) {
                // Token expiré ou invalide
                this.logout('Session expirée');
                throw new Error('Non autorisé');
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Erreur API:', error);
            throw error;
        }
    }

    /**
     * Vérification des permissions
     */
    hasPermission(permission) {
        if (!this.isAuthenticated || !this.currentUser) {
            return false;
        }

        // Logique de vérification des permissions
        // À étendre selon les besoins de l'application
        const userPermissions = this.currentUser.permissions || [];
        return userPermissions.includes(permission) || this.currentUser.role === 'admin';
    }

    /**
     * Protection d'une fonction
     */
    requireAuth(callback, requiredPermission = null) {
        if (!this.isAuthenticated) {
            this.redirectToAuth('Authentification requise');
            return;
        }

        if (requiredPermission && !this.hasPermission(requiredPermission)) {
            console.warn('Permission insuffisante:', requiredPermission);
            return;
        }

        callback();
    }

    /**
     * Obtention des données utilisateur actuelles
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * Vérification du statut d'authentification
     */
    getIsAuthenticated() {
        return this.isAuthenticated;
    }

    /**
     * Obtention du token d'authentification
     */
    getAuthToken() {
        return this.authToken;
    }
}

// Initialisation globale
const authGuard = new AuthGuard();

// Export pour utilisation dans d'autres modules
window.authGuard = authGuard;

// Vérification automatique au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si nous sommes sur la page d'authentification
    if (!window.location.pathname.includes('auth.html')) {
        // Vérifier l'authentification pour les pages protégées
        if (!authGuard.checkAuthStatus()) {
            // Redirection automatique vers l'authentification
            return;
        }
    }
});