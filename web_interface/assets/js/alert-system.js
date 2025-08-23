/**
 * Système d'alertes financières
 * Gestion des alertes de prix, volume, indicateurs techniques, etc.
 */

class AlertSystem {
    constructor() {
        this.alerts = [];
        this.activeAlerts = new Map();
        this.watchedSymbols = new Set();
        this.alertTypes = {
            PRICE_ABOVE: 'price_above',
            PRICE_BELOW: 'price_below',
            VOLUME_SPIKE: 'volume_spike',
            RSI_OVERSOLD: 'rsi_oversold',
            RSI_OVERBOUGHT: 'rsi_overbought',
            MACD_BULLISH: 'macd_bullish',
            MACD_BEARISH: 'macd_bearish',
            BOLLINGER_BREAKOUT: 'bollinger_breakout',
            SUPPORT_BREACH: 'support_breach',
            RESISTANCE_BREACH: 'resistance_breach',
            NEWS_SENTIMENT: 'news_sentiment',
            PORTFOLIO_RISK: 'portfolio_risk'
        };
        
        this.marketData = new Map();
        this.indicators = new Map();
        this.isMonitoring = false;
        this.monitoringInterval = null;
        
        this.init();
    }

    init() {
        this.loadAlerts();
        this.setupEventListeners();
        this.startMonitoring();
    }

    /**
     * Configuration des événements
     */
    setupEventListeners() {
        // Événements personnalisés
        document.addEventListener('marketDataUpdate', this.handleMarketDataUpdate.bind(this));
        document.addEventListener('indicatorUpdate', this.handleIndicatorUpdate.bind(this));
        document.addEventListener('portfolioUpdate', this.handlePortfolioUpdate.bind(this));
        document.addEventListener('newsUpdate', this.handleNewsUpdate.bind(this));
    }

    /**
     * Créer une nouvelle alerte
     */
    createAlert(alertConfig) {
        const alert = {
            id: this.generateId(),
            type: alertConfig.type,
            symbol: alertConfig.symbol,
            name: alertConfig.name || `Alerte ${alertConfig.symbol}`,
            condition: alertConfig.condition,
            value: alertConfig.value,
            enabled: true,
            triggered: false,
            triggerCount: 0,
            maxTriggers: alertConfig.maxTriggers || null,
            cooldown: alertConfig.cooldown || 300000, // 5 minutes par défaut
            lastTriggered: null,
            createdAt: Date.now(),
            notifications: {
                push: alertConfig.notifications?.push !== false,
                email: alertConfig.notifications?.email || false,
                sound: alertConfig.notifications?.sound !== false,
                desktop: alertConfig.notifications?.desktop !== false
            },
            actions: alertConfig.actions || [],
            metadata: alertConfig.metadata || {}
        };

        this.alerts.push(alert);
        this.watchedSymbols.add(alert.symbol);
        this.saveAlerts();

        // Notification de création
        if (window.notificationManager) {
            window.notificationManager.success(
                `Alerte créée pour ${alert.symbol}`,
                'Nouvelle alerte'
            );
        }

        return alert.id;
    }

    /**
     * Types d'alertes prédéfinies
     */
    createPriceAlert(symbol, condition, targetPrice, name) {
        const type = condition === 'above' ? this.alertTypes.PRICE_ABOVE : this.alertTypes.PRICE_BELOW;
        return this.createAlert({
            type,
            symbol,
            name: name || `Prix ${symbol} ${condition === 'above' ? '>' : '<'} ${targetPrice}`,
            condition,
            value: targetPrice,
            notifications: { push: true, sound: true, desktop: true }
        });
    }

    createVolumeAlert(symbol, multiplier = 2) {
        return this.createAlert({
            type: this.alertTypes.VOLUME_SPIKE,
            symbol,
            name: `Volume spike ${symbol} (${multiplier}x)`,
            condition: 'spike',
            value: multiplier,
            notifications: { push: true, sound: true }
        });
    }

    createRSIAlert(symbol, level, condition) {
        const type = condition === 'oversold' ? this.alertTypes.RSI_OVERSOLD : this.alertTypes.RSI_OVERBOUGHT;
        return this.createAlert({
            type,
            symbol,
            name: `RSI ${symbol} ${condition} (${level})`,
            condition,
            value: level,
            notifications: { push: true }
        });
    }

    createMACDAlert(symbol, signal) {
        const type = signal === 'bullish' ? this.alertTypes.MACD_BULLISH : this.alertTypes.MACD_BEARISH;
        return this.createAlert({
            type,
            symbol,
            name: `MACD ${symbol} signal ${signal}`,
            condition: signal,
            value: null,
            notifications: { push: true, sound: true }
        });
    }

    /**
     * Démarrer la surveillance
     */
    startMonitoring() {
        if (this.isMonitoring) return;
        
        this.isMonitoring = true;
        this.monitoringInterval = setInterval(() => {
            this.checkAlerts();
        }, 5000); // Vérification toutes les 5 secondes

        console.log('Surveillance des alertes démarrée');
    }

    /**
     * Arrêter la surveillance
     */
    stopMonitoring() {
        if (!this.isMonitoring) return;
        
        this.isMonitoring = false;
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }

        console.log('Surveillance des alertes arrêtée');
    }

    /**
     * Vérifier toutes les alertes
     */
    checkAlerts() {
        const activeAlerts = this.alerts.filter(alert => 
            alert.enabled && 
            !alert.triggered &&
            this.isAlertCooldownExpired(alert)
        );

        for (const alert of activeAlerts) {
            try {
                this.evaluateAlert(alert);
            } catch (error) {
                console.error(`Erreur lors de l'évaluation de l'alerte ${alert.id}:`, error);
            }
        }
    }

    /**
     * Évaluer une alerte spécifique
     */
    evaluateAlert(alert) {
        const currentData = this.marketData.get(alert.symbol);
        if (!currentData) return;

        let shouldTrigger = false;
        let triggerData = {};

        switch (alert.type) {
            case this.alertTypes.PRICE_ABOVE:
                shouldTrigger = currentData.price >= alert.value;
                triggerData = { currentPrice: currentData.price, targetPrice: alert.value };
                break;

            case this.alertTypes.PRICE_BELOW:
                shouldTrigger = currentData.price <= alert.value;
                triggerData = { currentPrice: currentData.price, targetPrice: alert.value };
                break;

            case this.alertTypes.VOLUME_SPIKE:
                const avgVolume = this.calculateAverageVolume(alert.symbol);
                shouldTrigger = currentData.volume >= (avgVolume * alert.value);
                triggerData = { 
                    currentVolume: currentData.volume, 
                    averageVolume: avgVolume,
                    multiplier: alert.value 
                };
                break;

            case this.alertTypes.RSI_OVERSOLD:
                const rsi = this.getIndicatorValue(alert.symbol, 'RSI');
                shouldTrigger = rsi && rsi <= alert.value;
                triggerData = { rsi, threshold: alert.value };
                break;

            case this.alertTypes.RSI_OVERBOUGHT:
                const rsiOB = this.getIndicatorValue(alert.symbol, 'RSI');
                shouldTrigger = rsiOB && rsiOB >= alert.value;
                triggerData = { rsi: rsiOB, threshold: alert.value };
                break;

            case this.alertTypes.MACD_BULLISH:
                shouldTrigger = this.checkMACDSignal(alert.symbol, 'bullish');
                triggerData = this.getMACDData(alert.symbol);
                break;

            case this.alertTypes.MACD_BEARISH:
                shouldTrigger = this.checkMACDSignal(alert.symbol, 'bearish');
                triggerData = this.getMACDData(alert.symbol);
                break;

            case this.alertTypes.BOLLINGER_BREAKOUT:
                shouldTrigger = this.checkBollingerBreakout(alert.symbol);
                triggerData = this.getBollingerData(alert.symbol);
                break;
        }

        if (shouldTrigger) {
            this.triggerAlert(alert, triggerData);
        }
    }

    /**
     * Déclencher une alerte
     */
    triggerAlert(alert, triggerData) {
        alert.triggered = true;
        alert.triggerCount++;
        alert.lastTriggered = Date.now();

        // Créer le message de notification
        const message = this.formatAlertMessage(alert, triggerData);
        
        // Envoyer la notification
        if (window.notificationManager && alert.notifications.push) {
            const notificationId = window.notificationManager.alert(
                message,
                alert.name,
                {
                    persistent: true,
                    actions: this.getAlertActions(alert),
                    data: {
                        alertId: alert.id,
                        symbol: alert.symbol,
                        triggerData
                    }
                }
            );
        }

        // Son personnalisé pour les alertes
        if (alert.notifications.sound) {
            this.playAlertSound(alert.type);
        }

        // Notification desktop
        if (alert.notifications.desktop && 'Notification' in window && Notification.permission === 'granted') {
            new Notification(alert.name, {
                body: message,
                icon: '/favicon.ico',
                tag: `alert-${alert.id}`
            });
        }

        // Exécuter les actions personnalisées
        this.executeAlertActions(alert, triggerData);

        // Désactiver si limite de déclenchements atteinte
        if (alert.maxTriggers && alert.triggerCount >= alert.maxTriggers) {
            alert.enabled = false;
        }

        this.saveAlerts();

        // Événement personnalisé
        document.dispatchEvent(new CustomEvent('alertTriggered', {
            detail: { alert, triggerData }
        }));

        console.log(`Alerte déclenchée: ${alert.name}`, triggerData);
    }

    /**
     * Formater le message d'alerte
     */
    formatAlertMessage(alert, triggerData) {
        switch (alert.type) {
            case this.alertTypes.PRICE_ABOVE:
                return `${alert.symbol} a dépassé ${triggerData.targetPrice}€ (${triggerData.currentPrice}€)`;
            
            case this.alertTypes.PRICE_BELOW:
                return `${alert.symbol} est descendu sous ${triggerData.targetPrice}€ (${triggerData.currentPrice}€)`;
            
            case this.alertTypes.VOLUME_SPIKE:
                return `Volume exceptionnel sur ${alert.symbol}: ${this.formatNumber(triggerData.currentVolume)} (${triggerData.multiplier}x la moyenne)`;
            
            case this.alertTypes.RSI_OVERSOLD:
                return `${alert.symbol} en zone de survente: RSI à ${triggerData.rsi.toFixed(1)}`;
            
            case this.alertTypes.RSI_OVERBOUGHT:
                return `${alert.symbol} en zone de surachat: RSI à ${triggerData.rsi.toFixed(1)}`;
            
            case this.alertTypes.MACD_BULLISH:
                return `Signal haussier MACD détecté sur ${alert.symbol}`;
            
            case this.alertTypes.MACD_BEARISH:
                return `Signal baissier MACD détecté sur ${alert.symbol}`;
            
            case this.alertTypes.BOLLINGER_BREAKOUT:
                return `Cassure des bandes de Bollinger sur ${alert.symbol}`;
            
            default:
                return `Alerte déclenchée pour ${alert.symbol}`;
        }
    }

    /**
     * Obtenir les actions d'alerte
     */
    getAlertActions(alert) {
        const actions = [
            {
                id: 'view-chart',
                label: 'Voir graphique',
                icon: 'fas fa-chart-line',
                callback: (notification) => {
                    this.openChart(alert.symbol);
                }
            },
            {
                id: 'disable-alert',
                label: 'Désactiver',
                icon: 'fas fa-bell-slash',
                callback: (notification) => {
                    this.disableAlert(alert.id);
                }
            }
        ];

        // Actions personnalisées
        if (alert.actions) {
            actions.push(...alert.actions);
        }

        return actions;
    }

    /**
     * Exécuter les actions d'alerte
     */
    executeAlertActions(alert, triggerData) {
        if (alert.actions) {
            alert.actions.forEach(action => {
                try {
                    if (typeof action.callback === 'function') {
                        action.callback(alert, triggerData);
                    }
                } catch (error) {
                    console.error(`Erreur lors de l'exécution de l'action ${action.id}:`, error);
                }
            });
        }
    }

    /**
     * Vérifier si le cooldown est expiré
     */
    isAlertCooldownExpired(alert) {
        if (!alert.lastTriggered) return true;
        return (Date.now() - alert.lastTriggered) >= alert.cooldown;
    }

    /**
     * Méthodes d'évaluation des indicateurs
     */
    checkMACDSignal(symbol, type) {
        const macd = this.getIndicatorValue(symbol, 'MACD');
        const signal = this.getIndicatorValue(symbol, 'MACD_Signal');
        const prevMACD = this.getPreviousIndicatorValue(symbol, 'MACD');
        const prevSignal = this.getPreviousIndicatorValue(symbol, 'MACD_Signal');

        if (!macd || !signal || !prevMACD || !prevSignal) return false;

        if (type === 'bullish') {
            return prevMACD <= prevSignal && macd > signal;
        } else {
            return prevMACD >= prevSignal && macd < signal;
        }
    }

    checkBollingerBreakout(symbol) {
        const price = this.marketData.get(symbol)?.price;
        const upperBand = this.getIndicatorValue(symbol, 'BB_Upper');
        const lowerBand = this.getIndicatorValue(symbol, 'BB_Lower');

        if (!price || !upperBand || !lowerBand) return false;

        return price > upperBand || price < lowerBand;
    }

    /**
     * Calculer le volume moyen
     */
    calculateAverageVolume(symbol, periods = 20) {
        // Simulation - en production, utiliser les données historiques
        const currentVolume = this.marketData.get(symbol)?.volume || 0;
        return currentVolume * 0.7; // Volume moyen simulé
    }

    /**
     * Obtenir la valeur d'un indicateur
     */
    getIndicatorValue(symbol, indicator) {
        return this.indicators.get(`${symbol}_${indicator}`);
    }

    getPreviousIndicatorValue(symbol, indicator) {
        // En production, accéder aux valeurs précédentes
        const current = this.getIndicatorValue(symbol, indicator);
        return current ? current * (0.98 + Math.random() * 0.04) : null;
    }

    getMACDData(symbol) {
        return {
            macd: this.getIndicatorValue(symbol, 'MACD'),
            signal: this.getIndicatorValue(symbol, 'MACD_Signal'),
            histogram: this.getIndicatorValue(symbol, 'MACD_Histogram')
        };
    }

    getBollingerData(symbol) {
        return {
            upper: this.getIndicatorValue(symbol, 'BB_Upper'),
            middle: this.getIndicatorValue(symbol, 'BB_Middle'),
            lower: this.getIndicatorValue(symbol, 'BB_Lower'),
            price: this.marketData.get(symbol)?.price
        };
    }

    /**
     * Gestionnaires d'événements
     */
    handleMarketDataUpdate(event) {
        const { symbol, data } = event.detail;
        this.marketData.set(symbol, data);
    }

    handleIndicatorUpdate(event) {
        const { symbol, indicator, value } = event.detail;
        this.indicators.set(`${symbol}_${indicator}`, value);
    }

    handlePortfolioUpdate(event) {
        // Vérifier les alertes de risque de portefeuille
        this.checkPortfolioRiskAlerts(event.detail);
    }

    handleNewsUpdate(event) {
        // Vérifier les alertes de sentiment
        this.checkNewsSentimentAlerts(event.detail);
    }

    /**
     * Méthodes de gestion des alertes
     */
    getAlert(id) {
        return this.alerts.find(alert => alert.id === id);
    }

    enableAlert(id) {
        const alert = this.getAlert(id);
        if (alert) {
            alert.enabled = true;
            alert.triggered = false;
            this.saveAlerts();
        }
    }

    disableAlert(id) {
        const alert = this.getAlert(id);
        if (alert) {
            alert.enabled = false;
            this.saveAlerts();
            
            if (window.notificationManager) {
                window.notificationManager.info(
                    `Alerte "${alert.name}" désactivée`,
                    'Alerte désactivée'
                );
            }
        }
    }

    deleteAlert(id) {
        const index = this.alerts.findIndex(alert => alert.id === id);
        if (index !== -1) {
            const alert = this.alerts[index];
            this.alerts.splice(index, 1);
            this.saveAlerts();
            
            // Retirer du suivi si plus d'alertes pour ce symbole
            const hasOtherAlerts = this.alerts.some(a => a.symbol === alert.symbol);
            if (!hasOtherAlerts) {
                this.watchedSymbols.delete(alert.symbol);
            }

            if (window.notificationManager) {
                window.notificationManager.info(
                    `Alerte "${alert.name}" supprimée`,
                    'Alerte supprimée'
                );
            }
        }
    }

    resetAlert(id) {
        const alert = this.getAlert(id);
        if (alert) {
            alert.triggered = false;
            alert.triggerCount = 0;
            alert.lastTriggered = null;
            this.saveAlerts();
        }
    }

    /**
     * Actions utilitaires
     */
    openChart(symbol) {
        // Naviguer vers la page de marché avec le symbole
        const marketPage = document.querySelector('.nav-link[data-page="market"]');
        if (marketPage) {
            marketPage.click();
            // Définir le symbole dans le graphique
            setTimeout(() => {
                const event = new CustomEvent('setActiveSymbol', { detail: symbol });
                document.dispatchEvent(event);
            }, 100);
        }
    }

    playAlertSound(type) {
        // Sons différents selon le type d'alerte
        const soundMap = {
            [this.alertTypes.PRICE_ABOVE]: 'notification-success',
            [this.alertTypes.PRICE_BELOW]: 'notification-warning',
            [this.alertTypes.VOLUME_SPIKE]: 'notification-info',
            [this.alertTypes.RSI_OVERSOLD]: 'notification-alert',
            [this.alertTypes.RSI_OVERBOUGHT]: 'notification-alert'
        };
        
        const soundType = soundMap[type] || 'notification-info';
        console.log(`Son d'alerte: ${soundType}`);
        // Implémenter la lecture audio
    }

    /**
     * Utilitaires
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    /**
     * Persistance
     */
    saveAlerts() {
        localStorage.setItem('finagent_alerts', JSON.stringify(this.alerts));
    }

    loadAlerts() {
        const saved = localStorage.getItem('finagent_alerts');
        if (saved) {
            try {
                this.alerts = JSON.parse(saved);
                // Reconstruire les symboles surveillés
                this.alerts.forEach(alert => {
                    this.watchedSymbols.add(alert.symbol);
                });
            } catch (error) {
                console.error('Erreur lors du chargement des alertes:', error);
                this.alerts = [];
            }
        }
    }

    /**
     * API publique
     */
    getActiveAlerts() {
        return this.alerts.filter(alert => alert.enabled);
    }

    getTriggeredAlerts() {
        return this.alerts.filter(alert => alert.triggered);
    }

    getAlertsBySymbol(symbol) {
        return this.alerts.filter(alert => alert.symbol === symbol);
    }

    getAlertStats() {
        return {
            total: this.alerts.length,
            active: this.alerts.filter(a => a.enabled).length,
            triggered: this.alerts.filter(a => a.triggered).length,
            watchedSymbols: this.watchedSymbols.size
        };
    }
}

// Initialiser le système d'alertes
document.addEventListener('DOMContentLoaded', () => {
    window.alertSystem = new AlertSystem();
    
    // Simuler des données de marché pour les tests
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        setTimeout(() => {
            // Données de test
            const testSymbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA'];
            testSymbols.forEach(symbol => {
                window.alertSystem.marketData.set(symbol, {
                    price: 100 + Math.random() * 100,
                    volume: 1000000 + Math.random() * 5000000,
                    change: -5 + Math.random() * 10
                });
                
                window.alertSystem.indicators.set(`${symbol}_RSI`, 30 + Math.random() * 40);
                window.alertSystem.indicators.set(`${symbol}_MACD`, -2 + Math.random() * 4);
                window.alertSystem.indicators.set(`${symbol}_MACD_Signal`, -2 + Math.random() * 4);
            });
        }, 1000);
    }
});

// Export pour usage dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AlertSystem;
}