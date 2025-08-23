/**
 * Initialisation de l'accessibilité - FinAgent
 * Intègre et initialise tous les composants d'accessibilité
 */

// Variables globales pour l'accessibilité
let accessibilityManager;
let isAccessibilityReady = false;

/**
 * Initialise le système d'accessibilité complet
 */
function initializeAccessibility() {
    try {
        // Initialiser le gestionnaire d'accessibilité
        if (typeof AccessibilityManager !== 'undefined') {
            accessibilityManager = new AccessibilityManager();
            console.log('Gestionnaire d\'accessibilité initialisé');
        }

        // Configurer les skip links
        setupSkipLinks();

        // Configurer les landmarks ARIA
        setupARIALandmarks();

        // Configurer la navigation clavier
        setupKeyboardNavigation();

        // Configurer les annonces pour les lecteurs d'écran
        setupScreenReaderAnnouncements();

        // Configurer les boutons d'accessibilité
        setupAccessibilityControls();

        // Configurer les raccourcis clavier
        setupKeyboardShortcuts();

        // Marquer l'accessibilité comme prête
        isAccessibilityReady = true;
        
        // Dispatch événement personnalisé
        document.dispatchEvent(new CustomEvent('accessibilityReady', {
            detail: { manager: accessibilityManager }
        }));

        console.log('Système d\'accessibilité complètement initialisé');
    } catch (error) {
        console.error('Erreur lors de l\'initialisation de l\'accessibilité:', error);
    }
}

/**
 * Configure les skip links
 */
function setupSkipLinks() {
    const skipLinks = document.querySelectorAll('.skip-link');
    
    skipLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const target = document.getElementById(targetId);
            
            if (target) {
                target.focus();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                
                // Annoncer le saut pour les lecteurs d'écran
                announceToScreenReader(`Navigation vers ${target.getAttribute('aria-label') || targetId}`);
            }
        });
    });
}

/**
 * Configure les landmarks ARIA
 */
function setupARIALandmarks() {
    // Assurer que tous les landmarks principaux ont des labels appropriés
    const landmarks = {
        'header[role="banner"]': 'En-tête principal',
        'nav[role="navigation"]': 'Navigation principale',
        'main[role="main"]': 'Contenu principal',
        'aside[role="complementary"]': 'Barre latérale',
        'footer[role="contentinfo"]': 'Pied de page'
    };

    Object.entries(landmarks).forEach(([selector, label]) => {
        const element = document.querySelector(selector);
        if (element && !element.getAttribute('aria-label')) {
            element.setAttribute('aria-label', label);
        }
    });
}

/**
 * Configure la navigation clavier avancée
 */
function setupKeyboardNavigation() {
    // Navigation dans les widgets avec flèches
    document.addEventListener('keydown', (e) => {
        const activeElement = document.activeElement;
        
        // Navigation dans les métriques du portefeuille
        if (activeElement.closest('.portfolio-metric')) {
            handlePortfolioMetricNavigation(e);
        }
        
        // Navigation dans les widgets
        if (activeElement.closest('.widget')) {
            handleWidgetNavigation(e);
        }
        
        // Navigation dans les tableaux
        if (activeElement.closest('table')) {
            handleTableNavigation(e);
        }
    });
}

/**
 * Gère la navigation clavier dans les métriques du portefeuille
 */
function handlePortfolioMetricNavigation(e) {
    const currentMetric = e.target.closest('.portfolio-metric');
    const allMetrics = Array.from(document.querySelectorAll('.portfolio-metric'));
    const currentIndex = allMetrics.indexOf(currentMetric);
    
    let targetIndex = -1;
    
    switch (e.key) {
        case 'ArrowRight':
        case 'ArrowDown':
            targetIndex = (currentIndex + 1) % allMetrics.length;
            break;
        case 'ArrowLeft':
        case 'ArrowUp':
            targetIndex = currentIndex > 0 ? currentIndex - 1 : allMetrics.length - 1;
            break;
        case 'Home':
            targetIndex = 0;
            break;
        case 'End':
            targetIndex = allMetrics.length - 1;
            break;
    }
    
    if (targetIndex !== -1) {
        e.preventDefault();
        const targetMetric = allMetrics[targetIndex];
        const focusable = targetMetric.querySelector('[tabindex], button, a, input, select, textarea');
        if (focusable) {
            focusable.focus();
        } else {
            targetMetric.focus();
        }
    }
}

/**
 * Gère la navigation clavier dans les widgets
 */
function handleWidgetNavigation(e) {
    if (e.key === 'Escape') {
        // Fermer les modales ou menus ouverts dans le widget
        const openModals = e.target.closest('.widget').querySelectorAll('[aria-expanded="true"]');
        openModals.forEach(modal => {
            modal.setAttribute('aria-expanded', 'false');
            modal.focus();
        });
    }
}

/**
 * Gère la navigation clavier dans les tableaux
 */
function handleTableNavigation(e) {
    const cell = e.target.closest('td, th');
    if (!cell) return;
    
    const row = cell.closest('tr');
    const table = cell.closest('table');
    const rows = Array.from(table.querySelectorAll('tr'));
    const cells = Array.from(row.querySelectorAll('td, th'));
    
    const rowIndex = rows.indexOf(row);
    const cellIndex = cells.indexOf(cell);
    
    let targetRow, targetCell;
    
    switch (e.key) {
        case 'ArrowUp':
            targetRow = rows[rowIndex - 1];
            if (targetRow) {
                targetCell = targetRow.querySelectorAll('td, th')[cellIndex];
            }
            break;
        case 'ArrowDown':
            targetRow = rows[rowIndex + 1];
            if (targetRow) {
                targetCell = targetRow.querySelectorAll('td, th')[cellIndex];
            }
            break;
        case 'ArrowLeft':
            targetCell = cells[cellIndex - 1];
            break;
        case 'ArrowRight':
            targetCell = cells[cellIndex + 1];
            break;
        case 'Home':
            targetCell = cells[0];
            break;
        case 'End':
            targetCell = cells[cells.length - 1];
            break;
    }
    
    if (targetCell) {
        e.preventDefault();
        targetCell.focus();
    }
}

/**
 * Configure les annonces pour les lecteurs d'écran
 */
function setupScreenReaderAnnouncements() {
    // Observer les changements de données en temps réel
    const observeDataChanges = () => {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' || mutation.type === 'characterData') {
                    const target = mutation.target;
                    
                    // Annoncer les changements de prix/valeurs
                    if (target.classList?.contains('portfolio-metric-value') ||
                        target.closest('.portfolio-metric-value')) {
                        announceValueChange(target);
                    }
                    
                    // Annoncer les nouvelles notifications
                    if (target.classList?.contains('notification-badge') ||
                        target.closest('.notification-badge')) {
                        announceNotificationChange(target);
                    }
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });
    };
    
    // Démarrer l'observation après un délai pour éviter les annonces initiales
    setTimeout(observeDataChanges, 2000);
}

/**
 * Annonce les changements de valeur
 */
function announceValueChange(element) {
    const metric = element.closest('.portfolio-metric');
    if (metric) {
        const label = metric.querySelector('.portfolio-metric-label')?.textContent;
        const value = element.textContent;
        const change = metric.querySelector('.portfolio-metric-change')?.textContent;
        
        const message = `${label}: ${value}${change ? ', ' + change : ''}`;
        announceToScreenReader(message);
    }
}

/**
 * Annonce les changements de notification
 */
function announceNotificationChange(element) {
    const count = element.textContent;
    if (count && parseInt(count) > 0) {
        announceToScreenReader(`${count} nouvelle${parseInt(count) > 1 ? 's' : ''} notification${parseInt(count) > 1 ? 's' : ''}`);
    }
}

/**
 * Configure les contrôles d'accessibilité
 */
function setupAccessibilityControls() {
    // Bouton d'accessibilité dans le header
    const accessibilityBtn = document.getElementById('accessibility-toggle');
    if (accessibilityBtn) {
        accessibilityBtn.addEventListener('click', () => {
            toggleAccessibilityPanel();
        });
    }
    
    // Écouter les changements de préférences
    document.addEventListener('accessibilityPreferenceChanged', (e) => {
        handleAccessibilityPreferenceChange(e.detail);
    });
}

/**
 * Bascule le panneau d'accessibilité
 */
function toggleAccessibilityPanel() {
    if (accessibilityManager) {
        accessibilityManager.toggleAccessibilityPanel();
    }
}

/**
 * Gère les changements de préférences d'accessibilité
 */
function handleAccessibilityPreferenceChange(preference) {
    switch (preference.type) {
        case 'high-contrast':
            document.body.classList.toggle('high-contrast', preference.enabled);
            break;
        case 'reduce-motion':
            document.body.classList.toggle('reduce-motion', preference.enabled);
            break;
        case 'large-text':
            document.body.classList.toggle('large-text', preference.enabled);
            break;
        case 'focus-indicators':
            document.body.classList.toggle('enhanced-focus', preference.enabled);
            break;
    }
}

/**
 * Configure les raccourcis clavier globaux
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ignorer si on est dans un champ de saisie
        if (e.target.matches('input, textarea, select, [contenteditable]')) {
            return;
        }
        
        // Raccourcis avec Alt
        if (e.altKey) {
            switch (e.key) {
                case '1':
                    e.preventDefault();
                    navigateToPage('dashboard');
                    break;
                case '2':
                    e.preventDefault();
                    navigateToPage('portfolio');
                    break;
                case '3':
                    e.preventDefault();
                    navigateToPage('market');
                    break;
                case '4':
                    e.preventDefault();
                    navigateToPage('trading');
                    break;
                case 'h':
                    e.preventDefault();
                    document.querySelector('#main-content')?.focus();
                    break;
                case 's':
                    e.preventDefault();
                    document.querySelector('#global-search')?.focus();
                    break;
                case 'n':
                    e.preventDefault();
                    document.querySelector('#notifications-btn')?.click();
                    break;
            }
        }
        
        // Échapper pour fermer
        if (e.key === 'Escape') {
            closeOpenModalsAndMenus();
        }
    });
}

/**
 * Navigue vers une page spécifique
 */
function navigateToPage(pageId) {
    const navLink = document.querySelector(`[data-page="${pageId}"]`);
    if (navLink) {
        navLink.click();
        navLink.focus();
        announceToScreenReader(`Navigation vers ${navLink.textContent.trim()}`);
    }
}

/**
 * Ferme les modales et menus ouverts
 */
function closeOpenModalsAndMenus() {
    // Fermer les dropdowns
    document.querySelectorAll('[aria-expanded="true"]').forEach(element => {
        element.setAttribute('aria-expanded', 'false');
    });
    
    // Fermer les modales
    document.querySelectorAll('.modal.show').forEach(modal => {
        modal.classList.remove('show');
    });
    
    // Fermer les notifications
    const notificationCenter = document.querySelector('.notification-center.show');
    if (notificationCenter) {
        notificationCenter.classList.remove('show');
    }
}

/**
 * Annonce un message aux lecteurs d'écran
 */
function announceToScreenReader(message, priority = 'polite') {
    if (accessibilityManager) {
        accessibilityManager.announceToScreenReader(message, priority);
    } else {
        // Fallback si le gestionnaire n'est pas disponible
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', priority);
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }
}

/**
 * Vérifie si l'accessibilité est prête
 */
function isAccessibilityInitialized() {
    return isAccessibilityReady;
}

/**
 * Obtient le gestionnaire d'accessibilité
 */
function getAccessibilityManager() {
    return accessibilityManager;
}

// Initialisation automatique au chargement du DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAccessibility);
} else {
    initializeAccessibility();
}

// Export pour utilisation dans d'autres modules
window.AccessibilityInit = {
    initialize: initializeAccessibility,
    isReady: isAccessibilityInitialized,
    getManager: getAccessibilityManager,
    announceToScreenReader,
    navigateToPage,
    closeOpenModalsAndMenus
};