/**
 * Gestionnaire des thèmes sombre/clair
 * Gère la bascule entre les thèmes et la persistance des préférences
 */

class ThemeManager {
    constructor() {
        this.currentTheme = 'light';
        this.themeStorageKey = 'finagent_theme';
        this.themeToggleButton = null;
        this.rootElement = document.documentElement;
        
        this.init();
    }

    init() {
        this.loadSavedTheme();
        this.setupThemeToggle();
        this.setupSystemThemeDetection();
        this.applyTheme(this.currentTheme);
    }

    /**
     * Charge le thème sauvegardé depuis le localStorage
     */
    loadSavedTheme() {
        const savedTheme = localStorage.getItem(this.themeStorageKey);
        
        if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
            this.currentTheme = savedTheme;
        } else {
            // Si aucun thème n'est sauvegardé, détecter la préférence système
            this.currentTheme = this.getSystemThemePreference();
        }
    }

    /**
     * Détecte la préférence de thème du système
     */
    getSystemThemePreference() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    /**
     * Configure le bouton de bascule de thème
     */
    setupThemeToggle() {
        // Créer le bouton de bascule s'il n'existe pas
        this.createThemeToggleButton();
        
        if (this.themeToggleButton) {
            this.themeToggleButton.addEventListener('click', () => {
                this.toggleTheme();
            });
            
            // Raccourci clavier pour basculer le thème
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.shiftKey && e.key === 'T') {
                    e.preventDefault();
                    this.toggleTheme();
                }
            });
        }
    }

    /**
     * Crée le bouton de bascule de thème dans le header
     */
    createThemeToggleButton() {
        const headerRight = document.querySelector('.header-right');
        
        if (headerRight) {
            // Vérifier si le bouton existe déjà
            let existingButton = document.getElementById('theme-toggle');
            
            if (!existingButton) {
                // Créer le bouton
                const themeButton = document.createElement('button');
                themeButton.id = 'theme-toggle';
                themeButton.className = 'header-btn theme-toggle';
                themeButton.title = 'Basculer le thème (Ctrl+Shift+T)';
                themeButton.innerHTML = '<i class="fas fa-moon"></i>';
                
                // Insérer avant le menu utilisateur
                const userMenu = headerRight.querySelector('.user-menu');
                if (userMenu) {
                    headerRight.insertBefore(themeButton, userMenu);
                } else {
                    headerRight.appendChild(themeButton);
                }
                
                this.themeToggleButton = themeButton;
            } else {
                this.themeToggleButton = existingButton;
            }
        }
    }

    /**
     * Configure la détection des changements de thème système
     */
    setupSystemThemeDetection() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            mediaQuery.addEventListener('change', (e) => {
                // Seulement appliquer le changement si aucun thème manuel n'est défini
                const savedTheme = localStorage.getItem(this.themeStorageKey);
                if (!savedTheme) {
                    this.currentTheme = e.matches ? 'dark' : 'light';
                    this.applyTheme(this.currentTheme);
                }
            });
        }
    }

    /**
     * Bascule entre les thèmes clair et sombre
     */
    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(this.currentTheme);
        this.saveTheme();
        this.showThemeChangeNotification();
    }

    /**
     * Applique le thème spécifié
     */
    applyTheme(theme) {
        // Retirer l'ancien thème
        this.rootElement.classList.remove('light-theme', 'dark-theme');
        
        // Ajouter le nouveau thème
        this.rootElement.classList.add(`${theme}-theme`);
        
        // Mettre à jour l'attribut data-theme pour les styles CSS
        this.rootElement.setAttribute('data-theme', theme);
        
        // Mettre à jour l'icône du bouton
        this.updateThemeToggleIcon(theme);
        
        // Déclencher un événement personnalisé
        this.dispatchThemeChangeEvent(theme);
        
        this.currentTheme = theme;
    }

    /**
     * Met à jour l'icône du bouton de bascule
     */
    updateThemeToggleIcon(theme) {
        if (this.themeToggleButton) {
            const icon = this.themeToggleButton.querySelector('i');
            if (icon) {
                icon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
            }
            
            // Mettre à jour le titre
            this.themeToggleButton.title = `Basculer vers le thème ${theme === 'light' ? 'sombre' : 'clair'} (Ctrl+Shift+T)`;
        }
    }

    /**
     * Sauvegarde le thème dans le localStorage
     */
    saveTheme() {
        localStorage.setItem(this.themeStorageKey, this.currentTheme);
    }

    /**
     * Déclenche un événement personnalisé lors du changement de thème
     */
    dispatchThemeChangeEvent(theme) {
        const event = new CustomEvent('themeChanged', {
            detail: {
                theme: theme,
                previousTheme: theme === 'light' ? 'dark' : 'light'
            }
        });
        
        document.dispatchEvent(event);
    }

    /**
     * Affiche une notification de changement de thème
     */
    showThemeChangeNotification() {
        const message = `Thème ${this.currentTheme === 'light' ? 'clair' : 'sombre'} activé`;
        
        // Utiliser le système de notification existant s'il est disponible
        if (window.userMenuManager && window.userMenuManager.showNotification) {
            window.userMenuManager.showNotification(message, 'info');
        } else {
            // Affichage de notification simple
            this.showSimpleNotification(message);
        }
    }

    /**
     * Affiche une notification simple
     */
    showSimpleNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'theme-notification';
        notification.textContent = message;
        
        // Styles pour la notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 16px',
            backgroundColor: 'var(--primary-500)',
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
        
        // Supprimer après 2 secondes
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 2000);
    }

    /**
     * Retourne le thème actuel
     */
    getCurrentTheme() {
        return this.currentTheme;
    }

    /**
     * Définit le thème programmatiquement
     */
    setTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            this.currentTheme = theme;
            this.applyTheme(theme);
            this.saveTheme();
        }
    }

    /**
     * Réinitialise le thème à la préférence système
     */
    resetToSystemTheme() {
        localStorage.removeItem(this.themeStorageKey);
        this.currentTheme = this.getSystemThemePreference();
        this.applyTheme(this.currentTheme);
        this.showSimpleNotification('Thème réinitialisé à la préférence système');
    }

    /**
     * Vérifie si le thème sombre est actif
     */
    isDarkTheme() {
        return this.currentTheme === 'dark';
    }

    /**
     * Vérifie si le thème clair est actif
     */
    isLightTheme() {
        return this.currentTheme === 'light';
    }
}

// Initialiser le gestionnaire de thèmes
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
    
    // Exposer globalement pour faciliter l'accès
    window.setTheme = (theme) => window.themeManager.setTheme(theme);
    window.toggleTheme = () => window.themeManager.toggleTheme();
    window.getCurrentTheme = () => window.themeManager.getCurrentTheme();
});

// Exporter pour usage dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}