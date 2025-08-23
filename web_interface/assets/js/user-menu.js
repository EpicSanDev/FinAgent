/**
 * Gestionnaire du menu utilisateur
 * Gère l'affichage du dropdown et l'intégration avec l'authentification
 */

class UserMenuManager {
    constructor() {
        this.userMenu = null;
        this.userDropdown = null;
        this.userAvatar = null;
        this.isDropdownOpen = false;
        
        this.init();
    }

    init() {
        this.userMenu = document.querySelector('.user-menu');
        this.userDropdown = document.querySelector('.user-dropdown');
        this.userAvatar = document.querySelector('.user-avatar');

        if (this.userAvatar && this.userDropdown) {
            this.setupEventListeners();
            this.loadUserInfo();
        }
    }

    setupEventListeners() {
        // Toggle dropdown au clic sur l'avatar
        this.userAvatar.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown();
        });

        // Fermer le dropdown en cliquant ailleurs
        document.addEventListener('click', (e) => {
            if (!this.userMenu.contains(e.target)) {
                this.closeDropdown();
            }
        });

        // Gestion des raccourcis clavier
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isDropdownOpen) {
                this.closeDropdown();
            }
        });

        // Gérer les clics sur les éléments du dropdown
        this.userDropdown.addEventListener('click', (e) => {
            const dropdownItem = e.target.closest('.dropdown-item');
            if (dropdownItem) {
                this.handleDropdownItemClick(dropdownItem);
            }
        });
    }

    toggleDropdown() {
        if (this.isDropdownOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }

    openDropdown() {
        this.userDropdown.classList.add('show');
        this.isDropdownOpen = true;
        
        // Focus sur le premier élément pour l'accessibilité
        const firstItem = this.userDropdown.querySelector('.dropdown-item');
        if (firstItem) {
            firstItem.focus();
        }
    }

    closeDropdown() {
        this.userDropdown.classList.remove('show');
        this.isDropdownOpen = false;
    }

    handleDropdownItemClick(item) {
        const action = item.dataset.action;
        
        switch (action) {
            case 'profile':
                this.showProfile();
                break;
            case 'settings':
                this.showSettings();
                break;
            case 'notifications':
                this.showNotifications();
                break;
            case 'help':
                this.showHelp();
                break;
            case 'logout':
                this.handleLogout();
                break;
            default:
                console.warn('Action inconnue:', action);
        }
        
        this.closeDropdown();
    }

    loadUserInfo() {
        // Charger les informations utilisateur depuis le localStorage ou l'API
        const userData = this.getUserData();
        
        if (userData) {
            this.updateUserDisplay(userData);
        }
    }

    getUserData() {
        // Récupérer les données utilisateur depuis le localStorage
        const userDataStr = localStorage.getItem('finagent_user');
        if (userDataStr) {
            try {
                return JSON.parse(userDataStr);
            } catch (e) {
                console.error('Erreur lors du parsing des données utilisateur:', e);
                return null;
            }
        }
        
        // Données par défaut si pas d'utilisateur connecté
        return {
            name: 'Utilisateur Demo',
            email: 'demo@finagent.com',
            avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face'
        };
    }

    updateUserDisplay(userData) {
        // Mettre à jour l'affichage dans le header
        const userName = this.userMenu.querySelector('.user-name');
        const userImg = this.userMenu.querySelector('.user-avatar img');
        
        if (userName) {
            userName.textContent = userData.name;
        }
        
        if (userImg) {
            userImg.src = userData.avatar;
            userImg.alt = `Avatar de ${userData.name}`;
        }

        // Mettre à jour l'affichage dans le dropdown
        const dropdownName = this.userDropdown.querySelector('.dropdown-user-name');
        const dropdownEmail = this.userDropdown.querySelector('.dropdown-user-email');
        const dropdownAvatar = this.userDropdown.querySelector('.dropdown-avatar');
        
        if (dropdownName) {
            dropdownName.textContent = userData.name;
        }
        
        if (dropdownEmail) {
            dropdownEmail.textContent = userData.email;
        }
        
        if (dropdownAvatar) {
            dropdownAvatar.src = userData.avatar;
            dropdownAvatar.alt = `Avatar de ${userData.name}`;
        }
    }

    showProfile() {
        // Afficher la page/modal de profil utilisateur
        console.log('Affichage du profil utilisateur');
        // TODO: Implémenter l'affichage du profil
        this.showNotification('Profil utilisateur - En cours de développement', 'info');
    }

    showSettings() {
        // Afficher la page/modal des paramètres
        console.log('Affichage des paramètres');
        // TODO: Implémenter l'affichage des paramètres
        this.showNotification('Paramètres - En cours de développement', 'info');
    }

    showNotifications() {
        // Afficher le panneau de notifications
        console.log('Affichage des notifications');
        // TODO: Implémenter l'affichage des notifications
        this.showNotification('Notifications - En cours de développement', 'info');
    }

    showHelp() {
        // Afficher l'aide/documentation
        console.log('Affichage de l\'aide');
        // TODO: Implémenter l'affichage de l'aide
        this.showNotification('Aide & Support - En cours de développement', 'info');
    }

    handleLogout() {
        // Confirmer la déconnexion
        if (confirm('Êtes-vous sûr de vouloir vous déconnecter ?')) {
            this.logout();
        }
    }

    logout() {
        // Nettoyer les données de session
        localStorage.removeItem('finagent_user');
        localStorage.removeItem('finagent_token');
        localStorage.removeItem('finagent_refresh_token');
        
        // Rediriger vers la page d'authentification
        window.location.href = 'auth.html';
    }

    showNotification(message, type = 'info') {
        // Afficher une notification temporaire
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Styles pour la notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 16px',
            backgroundColor: type === 'info' ? '#3b82f6' : '#10b981',
            color: 'white',
            borderRadius: '8px',
            zIndex: '9999',
            fontSize: '14px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });
        
        document.body.appendChild(notification);
        
        // Animer l'entrée
        requestAnimationFrame(() => {
            notification.style.transform = 'translateX(0)';
        });
        
        // Supprimer après 3 secondes
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // Méthode pour rafraîchir les informations utilisateur
    refreshUserInfo() {
        this.loadUserInfo();
    }

    // Méthode pour vérifier si l'utilisateur est connecté
    isUserLoggedIn() {
        const token = localStorage.getItem('finagent_token');
        return token && token !== '';
    }
}

// Initialiser le gestionnaire du menu utilisateur
document.addEventListener('DOMContentLoaded', () => {
    window.userMenuManager = new UserMenuManager();
});

// Exporter pour usage dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UserMenuManager;
}