/**
 * Intégration du système de notifications avec l'application FinAgent
 * Connecte les notifications aux événements de trading, alertes, et données de marché
 */

class NotificationsIntegration {
    constructor() {
        this.isInitialized = false;
        this.notificationManager = null;
        this.alertSystem = null;
        this.eventHandlers = new Map();
        
        this.init();
    }

    async init() {
        // Attendre que les systèmes soient disponibles
        await this.waitForSystems();
        this.setupIntegrations();
        this.setupMarketNotifications();
        this.setupTradingNotifications();
        this.setupPortfolioNotifications();
        this.setupRiskNotifications();
        this.setupSystemNotifications();
        this.isInitialized = true;
        
        console.log('Intégration des notifications initialisée');
    }

    /**
     * Attendre que les systèmes nécessaires soient chargés
     */
    async waitForSystems() {
        const maxAttempts = 50;
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            if (window.notificationManager && window.alertSystem) {
                this.notificationManager = window.notificationManager;
                this.alertSystem = window.alertSystem;
                return;
            }
            
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        console.warn('Timeout lors du chargement des systèmes de notification');
    }

    /**
     * Configuration des intégrations principales
     */
    setupIntegrations() {
        // Connecter les événements d'alerte aux notifications
        document.addEventListener('alertTriggered', this.handleAlertTriggered.bind(this));
        
        // Connecter les événements de connexion/déconnexion
        document.addEventListener('userLoggedIn', this.handleUserLogin.bind(this));
        document.addEventListener('userLoggedOut', this.handleUserLogout.bind(this));
        document.addEventListener('sessionExpired', this.handleSessionExpired.bind(this));
        
        // Connecter les événements de thème
        document.addEventListener('themeChanged', this.handleThemeChanged.bind(this));
        
        // Notifications de bienvenue lors du premier chargement
        if (document.readyState === 'complete') {
            this.showWelcomeNotifications();
        } else {
            window.addEventListener('load', this.showWelcomeNotifications.bind(this));
        }
    }

    /**
     * Notifications liées aux données de marché
     */
    setupMarketNotifications() {
        // Données de marché mises à jour
        document.addEventListener('marketDataUpdate', this.handleMarketDataUpdate.bind(this));
        
        // Nouveaux signaux techniques
        document.addEventListener('technicalSignal', this.handleTechnicalSignal.bind(this));
        
        // Actualités importantes
        document.addEventListener('importantNews', this.handleImportantNews.bind(this));
        
        // Volatilité exceptionnelle
        document.addEventListener('highVolatility', this.handleHighVolatility.bind(this));
    }

    /**
     * Notifications liées au trading
     */
    setupTradingNotifications() {
        // Ordres exécutés
        document.addEventListener('orderExecuted', this.handleOrderExecuted.bind(this));
        
        // Ordres annulés
        document.addEventListener('orderCancelled', this.handleOrderCancelled.bind(this));
        
        // Erreurs d'exécution
        document.addEventListener('orderFailed', this.handleOrderFailed.bind(this));
        
        // Positions fermées
        document.addEventListener('positionClosed', this.handlePositionClosed.bind(this));
        
        // Stop loss / Take profit atteints
        document.addEventListener('stopLossTriggered', this.handleStopLossTriggered.bind(this));
        document.addEventListener('takeProfitTriggered', this.handleTakeProfitTriggered.bind(this));
    }

    /**
     * Notifications liées au portefeuille
     */
    setupPortfolioNotifications() {
        // Performances importantes
        document.addEventListener('portfolioMilestone', this.handlePortfolioMilestone.bind(this));
        
        // Recommandations de rééquilibrage
        document.addEventListener('rebalanceRecommendation', this.handleRebalanceRecommendation.bind(this));
        
        // Allocation déséquilibrée
        document.addEventListener('allocationImbalance', this.handleAllocationImbalance.bind(this));
        
        // Nouvelle position ajoutée
        document.addEventListener('positionAdded', this.handlePositionAdded.bind(this));
    }

    /**
     * Notifications liées aux risques
     */
    setupRiskNotifications() {
        // Dépassement de VaR
        document.addEventListener('varExceeded', this.handleVarExceeded.bind(this));
        
        // Score de risque élevé
        document.addEventListener('highRiskScore', this.handleHighRiskScore.bind(this));
        
        // Corrélation élevée détectée
        document.addEventListener('highCorrelation', this.handleHighCorrelation.bind(this));
        
        // Stress test échoué
        document.addEventListener('stressTestFailed', this.handleStressTestFailed.bind(this));
    }

    /**
     * Notifications système
     */
    setupSystemNotifications() {
        // Mises à jour disponibles
        document.addEventListener('updateAvailable', this.handleUpdateAvailable.bind(this));
        
        // Erreurs système
        document.addEventListener('systemError', this.handleSystemError.bind(this));
        
        // Maintenance programmée
        document.addEventListener('maintenanceScheduled', this.handleMaintenanceScheduled.bind(this));
        
        // Statut de connexion
        document.addEventListener('connectionLost', this.handleConnectionLost.bind(this));
        document.addEventListener('connectionRestored', this.handleConnectionRestored.bind(this));
    }

    /**
     * Gestionnaires d'événements
     */
    
    handleAlertTriggered(event) {
        const { alert, triggerData } = event.detail;
        
        // L'alerte elle-même gère déjà les notifications
        // Ici on peut ajouter des actions supplémentaires
        console.log('Alerte déclenchée:', alert.name);
    }

    handleUserLogin(event) {
        const { user } = event.detail;
        
        this.notificationManager?.success(
            `Bienvenue, ${user.name} !`,
            'Connexion réussie'
        );
        
        // Charger les notifications en attente
        setTimeout(() => {
            this.loadPendingNotifications();
        }, 2000);
    }

    handleUserLogout(event) {
        this.notificationManager?.info(
            'Vous avez été déconnecté avec succès',
            'Déconnexion'
        );
    }

    handleSessionExpired(event) {
        this.notificationManager?.warning(
            'Votre session a expiré. Veuillez vous reconnecter.',
            'Session expirée',
            {
                persistent: true,
                actions: [
                    {
                        id: 'login',
                        label: 'Se reconnecter',
                        icon: 'fas fa-sign-in-alt',
                        callback: () => {
                            window.location.href = 'auth.html';
                        }
                    }
                ]
            }
        );
    }

    handleThemeChanged(event) {
        const { theme } = event.detail;
        const themeLabel = theme === 'dark' ? 'sombre' : 'clair';
        
        this.notificationManager?.info(
            `Thème ${themeLabel} activé`,
            'Thème modifié'
        );
    }

    handleMarketDataUpdate(event) {
        const { symbol, data, previousData } = event.detail;
        
        // Notification pour changements importants (>5%)
        if (previousData && data.price) {
            const changePercent = ((data.price - previousData.price) / previousData.price) * 100;
            
            if (Math.abs(changePercent) >= 5) {
                const isPositive = changePercent > 0;
                this.notificationManager?.show({
                    type: isPositive ? 'success' : 'warning',
                    title: `${symbol} ${isPositive ? '+' : ''}${changePercent.toFixed(1)}%`,
                    message: `Prix: ${data.price}€ (${isPositive ? '+' : ''}${(data.price - previousData.price).toFixed(2)}€)`,
                    icon: `fas fa-chart-${isPositive ? 'up' : 'down'}`,
                    autoClose: true,
                    autoCloseDelay: 8000
                });
            }
        }
    }

    handleTechnicalSignal(event) {
        const { symbol, signal, strength, indicator } = event.detail;
        
        const signalTypes = {
            'bullish': { type: 'success', icon: 'fas fa-arrow-up', label: 'Haussier' },
            'bearish': { type: 'warning', icon: 'fas fa-arrow-down', label: 'Baissier' },
            'neutral': { type: 'info', icon: 'fas fa-minus', label: 'Neutre' }
        };
        
        const config = signalTypes[signal] || signalTypes.neutral;
        
        this.notificationManager?.show({
            type: config.type,
            title: `Signal ${config.label} - ${symbol}`,
            message: `${indicator}: ${signal} (Force: ${strength}/5)`,
            icon: config.icon,
            autoClose: true,
            autoCloseDelay: 10000,
            actions: [
                {
                    id: 'view-chart',
                    label: 'Voir graphique',
                    icon: 'fas fa-chart-line',
                    callback: () => {
                        // Naviguer vers le graphique
                        const event = new CustomEvent('navigateToChart', { detail: { symbol } });
                        document.dispatchEvent(event);
                    }
                }
            ]
        });
    }

    handleOrderExecuted(event) {
        const { order, executionPrice } = event.detail;
        
        this.notificationManager?.success(
            `Ordre ${order.type} exécuté: ${order.quantity} ${order.symbol} à ${executionPrice}€`,
            'Ordre exécuté'
        );
    }

    handleOrderFailed(event) {
        const { order, error } = event.detail;
        
        this.notificationManager?.error(
            `Échec de l'ordre ${order.type} pour ${order.symbol}: ${error}`,
            'Erreur d\'exécution'
        );
    }

    handlePositionClosed(event) {
        const { position, pnl } = event.detail;
        const isProfitable = pnl > 0;
        
        this.notificationManager?.show({
            type: isProfitable ? 'success' : 'warning',
            title: 'Position fermée',
            message: `${position.symbol}: ${isProfitable ? '+' : ''}${pnl.toFixed(2)}€ (${isProfitable ? '+' : ''}${((pnl / position.cost) * 100).toFixed(1)}%)`,
            icon: `fas fa-${isProfitable ? 'arrow-up' : 'arrow-down'}`,
            autoClose: true,
            autoCloseDelay: 10000
        });
    }

    handleVarExceeded(event) {
        const { currentVar, limitVar, portfolioValue } = event.detail;
        
        this.notificationManager?.alert(
            `VaR dépassée: ${currentVar}€ (limite: ${limitVar}€)`,
            'Risque élevé détecté',
            {
                persistent: true,
                actions: [
                    {
                        id: 'view-risk',
                        label: 'Analyser les risques',
                        icon: 'fas fa-shield-alt',
                        callback: () => {
                            // Naviguer vers l'analyse des risques
                            const event = new CustomEvent('navigateToRisk');
                            document.dispatchEvent(event);
                        }
                    }
                ]
            }
        );
    }

    handleRebalanceRecommendation(event) {
        const { recommendations, currentAllocation } = event.detail;
        
        this.notificationManager?.info(
            `${recommendations.length} recommandation(s) de rééquilibrage disponible(s)`,
            'Rééquilibrage suggéré',
            {
                autoClose: false,
                actions: [
                    {
                        id: 'view-recommendations',
                        label: 'Voir recommandations',
                        icon: 'fas fa-balance-scale',
                        callback: () => {
                            // Naviguer vers les recommandations
                            const event = new CustomEvent('showRebalanceRecommendations', { detail: recommendations });
                            document.dispatchEvent(event);
                        }
                    }
                ]
            }
        );
    }

    handleConnectionLost(event) {
        this.notificationManager?.error(
            'Connexion au serveur perdue. Tentative de reconnexion...',
            'Connexion perdue',
            {
                persistent: true,
                id: 'connection-lost'
            }
        );
    }

    handleConnectionRestored(event) {
        // Supprimer la notification de perte de connexion
        this.notificationManager?.dismiss('connection-lost');
        
        this.notificationManager?.success(
            'Connexion rétablie',
            'Connexion restaurée'
        );
    }

    handleSystemError(event) {
        const { error, context } = event.detail;
        
        this.notificationManager?.error(
            `Erreur système: ${error.message}`,
            'Erreur',
            {
                persistent: true,
                actions: [
                    {
                        id: 'reload',
                        label: 'Recharger la page',
                        icon: 'fas fa-redo',
                        callback: () => {
                            window.location.reload();
                        }
                    }
                ]
            }
        );
    }

    /**
     * Notifications spéciales
     */
    
    showWelcomeNotifications() {
        // Notification de bienvenue uniquement lors du premier chargement
        const hasShownWelcome = localStorage.getItem('finagent_welcome_shown');
        
        if (!hasShownWelcome) {
            setTimeout(() => {
                this.notificationManager?.info(
                    'Bienvenue sur FinAgent ! Explorez vos données financières et créez vos premières alertes.',
                    'Bienvenue !',
                    {
                        autoClose: true,
                        autoCloseDelay: 8000,
                        actions: [
                            {
                                id: 'tour',
                                label: 'Visite guidée',
                                icon: 'fas fa-route',
                                callback: () => {
                                    this.startGuidedTour();
                                }
                            }
                        ]
                    }
                );
                
                localStorage.setItem('finagent_welcome_shown', 'true');
            }, 2000);
        }
        
        // Vérifier les nouvelles fonctionnalités
        this.checkForNewFeatures();
    }

    loadPendingNotifications() {
        // Simuler le chargement de notifications en attente
        const pendingNotifications = [
            {
                type: 'info',
                title: 'Rapport hebdomadaire disponible',
                message: 'Votre rapport de performance de la semaine est prêt',
                icon: 'fas fa-file-alt'
            },
            {
                type: 'warning',
                title: 'Maintenance programmée',
                message: 'Maintenance prévue dimanche à 2h00 (durée estimée: 1h)',
                icon: 'fas fa-tools'
            }
        ];
        
        pendingNotifications.forEach((notification, index) => {
            setTimeout(() => {
                this.notificationManager?.show(notification);
            }, index * 1000);
        });
    }

    checkForNewFeatures() {
        const lastVersion = localStorage.getItem('finagent_last_version');
        const currentVersion = '2.1.0'; // Version actuelle
        
        if (lastVersion && lastVersion !== currentVersion) {
            setTimeout(() => {
                this.notificationManager?.info(
                    'Nouvelles fonctionnalités disponibles ! Système de notifications et d\'alertes amélioré.',
                    'Mise à jour v2.1.0',
                    {
                        autoClose: false,
                        actions: [
                            {
                                id: 'changelog',
                                label: 'Voir les nouveautés',
                                icon: 'fas fa-star',
                                callback: () => {
                                    this.showChangelog();
                                }
                            }
                        ]
                    }
                );
            }, 5000);
        }
        
        localStorage.setItem('finagent_last_version', currentVersion);
    }

    startGuidedTour() {
        console.log('Démarrage de la visite guidée');
        // TODO: Implémenter la visite guidée
    }

    showChangelog() {
        console.log('Affichage du changelog');
        // TODO: Implémenter l'affichage du changelog
    }

    /**
     * API publique pour déclencher des notifications depuis d'autres modules
     */
    
    notifyTradingEvent(type, data) {
        const event = new CustomEvent(type, { detail: data });
        document.dispatchEvent(event);
    }

    notifyMarketEvent(type, data) {
        const event = new CustomEvent(type, { detail: data });
        document.dispatchEvent(event);
    }

    notifySystemEvent(type, data) {
        const event = new CustomEvent(type, { detail: data });
        document.dispatchEvent(event);
    }

    /**
     * Nettoyage
     */
    destroy() {
        this.eventHandlers.forEach((handler, event) => {
            document.removeEventListener(event, handler);
        });
        this.eventHandlers.clear();
        this.isInitialized = false;
    }
}

// Initialiser l'intégration des notifications
document.addEventListener('DOMContentLoaded', () => {
    window.notificationsIntegration = new NotificationsIntegration();
});

// Export pour usage dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationsIntegration;
}