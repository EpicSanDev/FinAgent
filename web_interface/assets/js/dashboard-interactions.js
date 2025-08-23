/**
 * Dashboard Interactions - Gestion des interactions pour le dashboard FinAgent
 * Gestion des widgets, mise à jour des données et interactions utilisateur
 */

class DashboardInteractions {
    constructor() {
        this.widgets = new Map();
        this.updateIntervals = new Map();
        this.isAutoRefreshEnabled = true;
        this.refreshInterval = 30000; // 30 secondes
        
        this.init();
    }

    /**
     * Initialisation des interactions du dashboard
     */
    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeInteractions());
        } else {
            this.initializeInteractions();
        }
    }

    /**
     * Initialiser toutes les interactions
     */
    initializeInteractions() {
        try {
            this.setupWidgetInteractions();
            this.setupPortfolioSummary();
            this.setupMarketOverview();
            this.setupWatchlist();
            this.setupNews();
            this.setupQuickActions();
            this.setupRefreshButton();
            this.startAutoRefresh();
            
            console.log('Interactions du dashboard initialisées avec succès');
        } catch (error) {
            console.error('Erreur lors de l\'initialisation des interactions:', error);
        }
    }

    /**
     * Configuration des interactions générales des widgets
     */
    setupWidgetInteractions() {
        // Gestion des actions de widgets
        document.addEventListener('click', (e) => {
            const widgetAction = e.target.closest('.widget-action');
            if (widgetAction) {
                e.preventDefault();
                this.handleWidgetAction(widgetAction);
            }
        });

        // Gestion du redimensionnement
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    /**
     * Gestion des actions sur les widgets
     */
    handleWidgetAction(actionElement) {
        const widget = actionElement.closest('.widget');
        if (!widget) return;

        const widgetId = widget.id || widget.querySelector('.widget-title')?.textContent?.trim();
        const icon = actionElement.querySelector('i');
        
        if (icon) {
            if (icon.classList.contains('fa-sync-alt')) {
                this.refreshWidget(widget);
            } else if (icon.classList.contains('fa-cog')) {
                this.openWidgetSettings(widget);
            } else if (icon.classList.contains('fa-expand')) {
                this.expandWidget(widget);
            } else if (icon.classList.contains('fa-plus')) {
                this.addToWidget(widget);
            }
        }
    }

    /**
     * Configuration du résumé de portefeuille
     */
    setupPortfolioSummary() {
        const portfolioMetrics = document.querySelectorAll('.portfolio-metric');
        portfolioMetrics.forEach(metric => {
            metric.addEventListener('click', () => {
                this.showPortfolioDetails(metric);
            });
        });

        // Mise à jour initiale des données
        this.updatePortfolioSummary();
    }

    /**
     * Configuration de l'aperçu du marché
     */
    setupMarketOverview() {
        const marketIndices = document.querySelectorAll('.market-index');
        marketIndices.forEach(index => {
            index.addEventListener('click', () => {
                this.showMarketDetails(index);
            });
        });

        // Mise à jour initiale
        this.updateMarketOverview();
    }

    /**
     * Configuration de la watchlist
     */
    setupWatchlist() {
        const searchInput = document.getElementById('watchlist-search');
        const watchlistItems = document.querySelectorAll('.watchlist-item');

        // Recherche dans la watchlist
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterWatchlist(e.target.value);
            });
        }

        // Clic sur les éléments de la watchlist
        watchlistItems.forEach(item => {
            item.addEventListener('click', () => {
                this.selectWatchlistItem(item);
            });
        });

        // Mise à jour des prix
        this.updateWatchlistPrices();
    }

    /**
     * Configuration des actualités
     */
    setupNews() {
        const newsItems = document.querySelectorAll('.news-item');
        newsItems.forEach(item => {
            item.addEventListener('click', () => {
                this.openNewsArticle(item);
            });
        });

        // Mise à jour des actualités
        this.updateNews();
    }

    /**
     * Configuration des actions rapides
     */
    setupQuickActions() {
        const quickActions = document.querySelectorAll('.quick-action');
        quickActions.forEach(action => {
            action.addEventListener('click', (e) => {
                e.preventDefault();
                const page = action.dataset.page;
                if (page && window.app) {
                    window.app.navigateTo(page);
                }
            });
        });
    }

    /**
     * Configuration du bouton d'actualisation
     */
    setupRefreshButton() {
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshAllData();
            });
        }

        const addWidgetBtn = document.getElementById('add-widget');
        if (addWidgetBtn) {
            addWidgetBtn.addEventListener('click', () => {
                this.showAddWidgetModal();
            });
        }
    }

    /**
     * Mise à jour du résumé de portefeuille
     */
    updatePortfolioSummary() {
        // Simulation de nouvelles données
        const portfolioData = this.generatePortfolioData();
        
        // Mise à jour des valeurs
        this.updateElement('total-value', this.formatCurrency(portfolioData.totalValue));
        this.updateElement('daily-pnl', this.formatCurrency(portfolioData.dailyPnL));
        this.updateElement('total-pnl', this.formatCurrency(portfolioData.totalPnL));
        this.updateElement('cash', this.formatCurrency(portfolioData.cash));
        this.updateElement('positions-count', portfolioData.positionsCount);

        // Mise à jour des changements
        this.updateChangeIndicator('total-value', portfolioData.totalValueChange);
        this.updateChangeIndicator('daily-pnl', portfolioData.dailyPnLChange);
        this.updateChangeIndicator('total-pnl', portfolioData.totalPnLChange);
    }

    /**
     * Mise à jour de l'aperçu du marché
     */
    updateMarketOverview() {
        const marketData = this.generateMarketData();
        
        const indices = document.querySelectorAll('.market-index');
        indices.forEach((index, i) => {
            if (marketData[i]) {
                const data = marketData[i];
                const valueEl = index.querySelector('.market-index-value');
                const changeEl = index.querySelector('.market-index-change');
                
                if (valueEl) valueEl.textContent = data.value;
                if (changeEl) {
                    changeEl.innerHTML = `
                        <i class="fas fa-arrow-${data.change >= 0 ? 'up' : 'down'}"></i>
                        ${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)}%
                    `;
                    changeEl.className = `market-index-change ${data.change >= 0 ? 'positive' : 'negative'}`;
                }
            }
        });
    }

    /**
     * Mise à jour des prix de la watchlist
     */
    updateWatchlistPrices() {
        const watchlistItems = document.querySelectorAll('.watchlist-item');
        watchlistItems.forEach(item => {
            const symbol = item.querySelector('.watchlist-symbol-name')?.textContent;
            if (symbol) {
                const priceData = this.generateStockPrice(symbol);
                
                const priceEl = item.querySelector('.watchlist-price-current');
                const changeEl = item.querySelector('.watchlist-price-change');
                
                if (priceEl) priceEl.textContent = priceData.price;
                if (changeEl) {
                    changeEl.innerHTML = `
                        <i class="fas fa-arrow-${priceData.change >= 0 ? 'up' : 'down'}"></i>
                        ${priceData.change >= 0 ? '+' : ''}${priceData.change.toFixed(2)}%
                    `;
                    changeEl.className = `watchlist-price-change ${priceData.change >= 0 ? 'positive' : 'negative'}`;
                }
            }
        });
    }

    /**
     * Mise à jour des actualités
     */
    updateNews() {
        // Simulation de nouvelles actualités
        console.log('Mise à jour des actualités...');
    }

    /**
     * Filtrage de la watchlist
     */
    filterWatchlist(query) {
        const items = document.querySelectorAll('.watchlist-item');
        const lowerQuery = query.toLowerCase();
        
        items.forEach(item => {
            const symbol = item.querySelector('.watchlist-symbol-name')?.textContent?.toLowerCase();
            const desc = item.querySelector('.watchlist-symbol-desc')?.textContent?.toLowerCase();
            
            const matches = symbol?.includes(lowerQuery) || desc?.includes(lowerQuery);
            item.style.display = matches ? 'flex' : 'none';
        });
    }

    /**
     * Actualisation de tous les données
     */
    refreshAllData() {
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            const icon = refreshBtn.querySelector('i');
            if (icon) {
                icon.classList.add('fa-spin');
                setTimeout(() => icon.classList.remove('fa-spin'), 1000);
            }
        }

        // Actualiser toutes les sections
        this.updatePortfolioSummary();
        this.updateMarketOverview();
        this.updateWatchlistPrices();
        this.updateNews();

        // Actualiser les graphiques
        if (window.dashboardCharts) {
            window.dashboardCharts.refreshAllCharts();
        }

        // Notification de succès
        if (window.app) {
            window.app.showNotification('Dashboard actualisé avec succès', 'success', 2000);
        }
    }

    /**
     * Auto-actualisation
     */
    startAutoRefresh() {
        if (this.isAutoRefreshEnabled) {
            this.autoRefreshInterval = setInterval(() => {
                this.refreshAllData();
            }, this.refreshInterval);
        }
    }

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }

    /**
     * Gestionnaires d'événements
     */
    handleResize() {
        // Redimensionner les graphiques
        if (window.dashboardCharts) {
            window.dashboardCharts.resizeAllCharts();
        }
    }

    refreshWidget(widget) {
        widget.classList.add('widget-loading');
        
        setTimeout(() => {
            widget.classList.remove('widget-loading');
            
            // Actualiser les données du widget spécifique
            const title = widget.querySelector('.widget-title')?.textContent?.trim();
            if (title?.includes('Portefeuille')) {
                this.updatePortfolioSummary();
            } else if (title?.includes('Marché')) {
                this.updateMarketOverview();
            } else if (title?.includes('Watchlist')) {
                this.updateWatchlistPrices();
            } else if (title?.includes('Actualités')) {
                this.updateNews();
            }
        }, 1000);
    }

    openWidgetSettings(widget) {
        console.log('Ouvrir les paramètres du widget:', widget);
        // Implémenter la modal de paramètres
    }

    expandWidget(widget) {
        console.log('Agrandir le widget:', widget);
        // Implémenter le mode plein écran
    }

    addToWidget(widget) {
        console.log('Ajouter à:', widget);
        // Implémenter l'ajout d'éléments
    }

    showPortfolioDetails(metric) {
        console.log('Afficher les détails du portefeuille:', metric);
        // Naviguer vers la page portefeuille
        if (window.app) {
            window.app.navigateTo('portfolio');
        }
    }

    showMarketDetails(index) {
        console.log('Afficher les détails du marché:', index);
        // Naviguer vers la page marché
        if (window.app) {
            window.app.navigateTo('market');
        }
    }

    selectWatchlistItem(item) {
        // Retirer la sélection précédente
        document.querySelectorAll('.watchlist-item').forEach(i => i.classList.remove('selected'));
        
        // Sélectionner l'élément
        item.classList.add('selected');
        
        const symbol = item.querySelector('.watchlist-symbol-name')?.textContent;
        console.log('Symbole sélectionné:', symbol);
    }

    openNewsArticle(item) {
        const title = item.querySelector('.news-title')?.textContent;
        console.log('Ouvrir l\'article:', title);
        // Implémenter l'ouverture d'article
    }

    showAddWidgetModal() {
        console.log('Afficher la modal d\'ajout de widget');
        // Implémenter la modal d'ajout de widget
    }

    /**
     * Générateurs de données simulées
     */
    generatePortfolioData() {
        return {
            totalValue: 125847.32 + (Math.random() - 0.5) * 1000,
            dailyPnL: 1247.83 + (Math.random() - 0.5) * 500,
            totalPnL: 12847.32 + (Math.random() - 0.5) * 1000,
            cash: 8924.67,
            positionsCount: 23,
            totalValueChange: (Math.random() - 0.3) * 3,
            dailyPnLChange: (Math.random() - 0.3) * 2,
            totalPnLChange: (Math.random() - 0.2) * 1.5
        };
    }

    generateMarketData() {
        return [
            { value: '7,234.56', change: (Math.random() - 0.4) * 2 },
            { value: '15,847.32', change: (Math.random() - 0.4) * 2 },
            { value: '4,387.21', change: (Math.random() - 0.5) * 2 },
            { value: '13,492.76', change: (Math.random() - 0.5) * 2 },
            { value: '1.0892', change: (Math.random() - 0.5) * 1 },
            { value: '42,847', change: (Math.random() - 0.3) * 5 }
        ];
    }

    generateStockPrice(symbol) {
        const basePrices = {
            'AAPL': 182.34,
            'MSFT': 374.56,
            'GOOGL': 142.87,
            'TSLA': 234.12,
            'NVDA': 487.93
        };
        
        const basePrice = basePrices[symbol] || 100;
        const change = (Math.random() - 0.4) * 3;
        const price = basePrice * (1 + change / 100);
        
        return {
            price: `$${price.toFixed(2)}`,
            change: change
        };
    }

    /**
     * Utilitaires
     */
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    updateChangeIndicator(baseId, changePercent) {
        const baseElement = document.getElementById(baseId);
        if (!baseElement) return;
        
        const changeElement = baseElement.closest('.portfolio-metric')?.querySelector('.portfolio-metric-change');
        if (changeElement) {
            const isPositive = changePercent >= 0;
            const isNeutral = Math.abs(changePercent) < 0.1;
            
            changeElement.className = `portfolio-metric-change ${isNeutral ? 'neutral' : isPositive ? 'positive' : 'negative'}`;
            changeElement.innerHTML = `
                <i class="fas fa-arrow-${isNeutral ? 'right' : isPositive ? 'up' : 'down'}"></i>
                ${isPositive ? '+' : ''}${changePercent.toFixed(2)}%
            `;
        }
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR'
        }).format(amount);
    }

    /**
     * Nettoyage
     */
    destroy() {
        this.stopAutoRefresh();
        this.updateIntervals.forEach(interval => clearInterval(interval));
        this.updateIntervals.clear();
        this.widgets.clear();
    }
}

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardInteractions;
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    if (typeof window !== 'undefined') {
        window.dashboardInteractions = new DashboardInteractions();
    }
});