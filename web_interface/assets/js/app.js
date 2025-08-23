/**
 * FinAgent Web Interface - Application principale
 * Initialisation et gestion des fonctionnalités de base
 */

class FinAgentApp {
    constructor() {
        this.currentPage = 'dashboard';
        this.theme = this.getStoredTheme() || 'light';
        this.sidebarCollapsed = this.getStoredSidebarState() || false;
        this.widgets = new Map();
        this.notifications = [];
        
        this.init();
    }

    /**
     * Initialisation de l'application
     */
    init() {
        this.setupEventListeners();
        this.initializeTheme();
        this.initializeSidebar();
        this.initializeNotifications();
        this.loadCurrentPage();
        
        // Charger les données initiales
        this.loadInitialData();
        
        console.log('FinAgent App initialisée avec succès');
    }

    /**
     * Configuration des écouteurs d'événements
     */
    setupEventListeners() {
        // Gestion de la navigation
        document.addEventListener('click', (e) => {
            const navLink = e.target.closest('[data-page]');
            if (navLink) {
                e.preventDefault();
                this.navigateTo(navLink.dataset.page);
            }
        });

        // Gestion du toggle theme
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Gestion du toggle sidebar
        const sidebarToggle = document.getElementById('sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }

        // Gestion des notifications
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('notification-close')) {
                this.closeNotification(e.target.closest('.notification'));
            }
        });

        // Gestion du responsive
        window.addEventListener('resize', () => this.handleResize());
        
        // Gestion des raccourcis clavier
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    }

    /**
     * Navigation entre les pages
     */
    navigateTo(page) {
        if (page === this.currentPage) return;

        // Masquer la page actuelle
        const currentPageEl = document.querySelector(`[data-page-content="${this.currentPage}"]`);
        if (currentPageEl) {
            currentPageEl.style.display = 'none';
        }

        // Afficher la nouvelle page
        const newPageEl = document.querySelector(`[data-page-content="${page}"]`);
        if (newPageEl) {
            newPageEl.style.display = 'block';
        } else {
            // Charger dynamiquement la page si elle n'existe pas
            this.loadPage(page);
        }

        // Mettre à jour l'état de navigation
        this.updateNavigationState(page);
        this.currentPage = page;

        // Déclencher l'événement de changement de page
        this.onPageChange(page);
    }

    /**
     * Mise à jour de l'état de navigation
     */
    updateNavigationState(page) {
        // Mettre à jour les liens actifs
        document.querySelectorAll('[data-page]').forEach(link => {
            link.classList.toggle('active', link.dataset.page === page);
        });

        // Mettre à jour le titre de la page
        this.updatePageTitle(page);
    }

    /**
     * Mise à jour du titre de la page
     */
    updatePageTitle(page) {
        const titles = {
            'dashboard': 'Dashboard',
            'portfolio': 'Portefeuille',
            'market': 'Marché',
            'trading': 'Trading',
            'analysis': 'Analyse',
            'strategies': 'Stratégies',
            'risk': 'Gestion des Risques',
            'reports': 'Rapports'
        };

        document.title = `FinAgent - ${titles[page] || 'Dashboard'}`;
        
        const pageTitle = document.querySelector('.page-title');
        if (pageTitle) {
            pageTitle.textContent = titles[page] || 'Dashboard';
        }
    }

    /**
     * Gestion du changement de page
     */
    onPageChange(page) {
        // Charger les données spécifiques à la page
        this.loadPageData(page);
        
        // Mettre à jour l'historique du navigateur
        history.pushState({ page }, '', `#${page}`);
    }

    /**
     * Gestion des thèmes
     */
    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme();
        this.storeTheme();
    }

    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
        
        const themeIcon = document.querySelector('#theme-toggle i');
        if (themeIcon) {
            themeIcon.className = this.theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        }
    }

    initializeTheme() {
        this.applyTheme();
    }

    getStoredTheme() {
        return localStorage.getItem('finagent-theme');
    }

    storeTheme() {
        localStorage.setItem('finagent-theme', this.theme);
    }

    /**
     * Gestion de la sidebar
     */
    toggleSidebar() {
        this.sidebarCollapsed = !this.sidebarCollapsed;
        this.applySidebarState();
        this.storeSidebarState();
    }

    applySidebarState() {
        const appLayout = document.querySelector('.app-layout');
        if (appLayout) {
            appLayout.classList.toggle('sidebar-collapsed', this.sidebarCollapsed);
        }
    }

    initializeSidebar() {
        this.applySidebarState();
    }

    getStoredSidebarState() {
        return localStorage.getItem('finagent-sidebar-collapsed') === 'true';
    }

    storeSidebarState() {
        localStorage.setItem('finagent-sidebar-collapsed', this.sidebarCollapsed);
    }

    /**
     * Système de notifications
     */
    initializeNotifications() {
        this.notificationContainer = document.getElementById('notifications-container');
        if (!this.notificationContainer) {
            this.createNotificationContainer();
        }
    }

    createNotificationContainer() {
        this.notificationContainer = document.createElement('div');
        this.notificationContainer.id = 'notifications-container';
        this.notificationContainer.className = 'notifications-container';
        document.body.appendChild(this.notificationContainer);
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = this.createNotificationElement(message, type);
        this.notificationContainer.appendChild(notification);
        
        // Animation d'entrée
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Auto-fermeture
        if (duration > 0) {
            setTimeout(() => this.closeNotification(notification), duration);
        }
        
        this.notifications.push(notification);
        return notification;
    }

    createNotificationElement(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icons = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle'
        };
        
        notification.innerHTML = `
            <div class="notification-content">
                <i class="${icons[type] || icons.info}"></i>
                <span class="notification-message">${message}</span>
            </div>
            <button class="notification-close" aria-label="Fermer">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        return notification;
    }

    closeNotification(notification) {
        if (!notification) return;
        
        notification.classList.add('closing');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            const index = this.notifications.indexOf(notification);
            if (index > -1) {
                this.notifications.splice(index, 1);
            }
        }, 300);
    }

    /**
     * Gestion responsive
     */
    handleResize() {
        const isMobile = window.innerWidth <= 768;
        
        if (isMobile && !this.sidebarCollapsed) {
            this.sidebarCollapsed = true;
            this.applySidebarState();
        }
        
        // Ajuster les graphiques si nécessaire
        this.resizeCharts();
    }

    /**
     * Raccourcis clavier
     */
    handleKeyboardShortcuts(e) {
        // Échapper ferme les modales
        if (e.key === 'Escape') {
            this.closeActiveModal();
        }
        
        // Raccourcis avec Ctrl/Cmd
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case 'd':
                    e.preventDefault();
                    this.navigateTo('dashboard');
                    break;
                case 'p':
                    e.preventDefault();
                    this.navigateTo('portfolio');
                    break;
                case 'm':
                    e.preventDefault();
                    this.navigateTo('market');
                    break;
                case 't':
                    e.preventDefault();
                    this.navigateTo('trading');
                    break;
            }
        }
    }

    /**
     * Chargement des données
     */
    async loadInitialData() {
        try {
            // Charger les données du dashboard par défaut
            await this.loadPageData('dashboard');
            
            // Charger les données de marché
            await this.loadMarketData();
            
            // Charger les informations utilisateur
            await this.loadUserData();
            
        } catch (error) {
            console.error('Erreur lors du chargement des données initiales:', error);
            this.showNotification('Erreur lors du chargement des données', 'error');
        }
    }

    async loadPageData(page) {
        // Simuler le chargement de données
        console.log(`Chargement des données pour la page: ${page}`);
        
        switch (page) {
            case 'dashboard':
                await this.loadDashboardData();
                break;
            case 'portfolio':
                await this.loadPortfolioData();
                break;
            case 'market':
                await this.loadMarketPageData();
                break;
            case 'trading':
                await this.loadTradingData();
                break;
            default:
                console.log(`Pas de données spécifiques pour la page: ${page}`);
        }
    }

    async loadDashboardData() {
        // Simuler le chargement des données du dashboard
        return new Promise(resolve => {
            setTimeout(() => {
                console.log('Données du dashboard chargées');
                resolve();
            }, 1000);
        });
    }

    async loadPortfolioData() {
        // Simuler le chargement des données du portefeuille
        return new Promise(resolve => {
            setTimeout(() => {
                console.log('Données du portefeuille chargées');
                resolve();
            }, 800);
        });
    }

    async loadMarketData() {
        // Simuler le chargement des données de marché
        return new Promise(resolve => {
            setTimeout(() => {
                console.log('Données de marché chargées');
                resolve();
            }, 600);
        });
    }

    async loadMarketPageData() {
        // Simuler le chargement des données de la page marché
        return new Promise(resolve => {
            setTimeout(() => {
                console.log('Données de la page marché chargées');
                resolve();
            }, 700);
        });
    }

    async loadTradingData() {
        // Simuler le chargement des données de trading
        return new Promise(resolve => {
            setTimeout(() => {
                console.log('Données de trading chargées');
                resolve();
            }, 900);
        });
    }

    async loadUserData() {
        // Simuler le chargement des données utilisateur
        return new Promise(resolve => {
            setTimeout(() => {
                console.log('Données utilisateur chargées');
                resolve();
            }, 400);
        });
    }

    /**
     * Utilitaires
     */
    loadPage(page) {
        // Créer dynamiquement le contenu de la page
        const mainContent = document.querySelector('.app-main');
        if (mainContent) {
            const pageContent = document.createElement('div');
            pageContent.setAttribute('data-page-content', page);
            pageContent.innerHTML = `
                <div class="page-loading">
                    <div class="spinner"></div>
                    <p>Chargement de ${page}...</p>
                </div>
            `;
            mainContent.appendChild(pageContent);
        }
    }

    closeActiveModal() {
        const activeModal = document.querySelector('.modal.show');
        if (activeModal) {
            activeModal.classList.remove('show');
        }
    }

    resizeCharts() {
        // Redimensionner tous les graphiques
        this.widgets.forEach(widget => {
            if (widget.chart && typeof widget.chart.resize === 'function') {
                widget.chart.resize();
            }
        });
    }

    /**
     * Utilitaires de formatage
     */
    formatCurrency(amount, currency = 'EUR') {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }

    formatNumber(number, decimals = 2) {
        return new Intl.NumberFormat('fr-FR', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(number);
    }

    formatPercentage(value, decimals = 2) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'percent',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value / 100);
    }

    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        
        return new Intl.DateTimeFormat('fr-FR', { ...defaultOptions, ...options }).format(new Date(date));
    }
}

/**
 * Utilitaires globaux
 */
window.FinAgentUtils = {
    // Debounce function pour optimiser les performances
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Throttle function pour les événements de scroll/resize
    throttle: (func, limit) => {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Validation d'email simple
    isValidEmail: (email) => {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    },

    // Génération d'ID unique
    generateId: () => {
        return '_' + Math.random().toString(36).substr(2, 9);
    }
};

/**
 * Initialisation de l'application
 */
document.addEventListener('DOMContentLoaded', () => {
    window.app = new FinAgentApp();
});

/**
 * Gestion de l'historique du navigateur
 */
window.addEventListener('popstate', (e) => {
    if (e.state && e.state.page && window.app) {
        window.app.navigateTo(e.state.page);
    }
});

/**
 * Gestion des erreurs globales
 */
window.addEventListener('error', (e) => {
    console.error('Erreur JavaScript:', e.error);
    if (window.app) {
        window.app.showNotification('Une erreur est survenue', 'error');
    }
});

/**
 * Export pour utilisation dans d'autres modules
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FinAgentApp;
}