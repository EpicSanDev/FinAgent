/**
 * Gestionnaire de widgets personnalisables
 * Permet la personnalisation du dashboard avec drag-and-drop
 */

class WidgetManager {
    constructor() {
        this.widgets = new Map();
        this.widgetContainer = null;
        this.availableWidgets = [];
        this.draggedWidget = null;
        this.dropZones = [];
        this.storageKey = 'finagent_dashboard_layout';
        
        this.init();
    }

    init() {
        this.setupAvailableWidgets();
        this.loadSavedLayout();
        this.setupDragAndDrop();
        this.setupWidgetControls();
    }

    /**
     * Configuration des widgets disponibles
     */
    setupAvailableWidgets() {
        this.availableWidgets = [
            {
                id: 'portfolio-summary',
                title: 'Résumé Portefeuille',
                icon: 'fas fa-wallet',
                description: 'Vue d\'ensemble de votre portefeuille',
                size: 'md',
                category: 'portfolio',
                component: 'PortfolioSummaryWidget'
            },
            {
                id: 'market-overview',
                title: 'Vue du Marché',
                icon: 'fas fa-chart-line',
                description: 'Indices principaux et performances',
                size: 'lg',
                category: 'market',
                component: 'MarketOverviewWidget'
            },
            {
                id: 'watchlist',
                title: 'Liste de Surveillance',
                icon: 'fas fa-eye',
                description: 'Vos actifs surveillés',
                size: 'md',
                category: 'market',
                component: 'WatchlistWidget'
            },
            {
                id: 'performance-chart',
                title: 'Performance',
                icon: 'fas fa-chart-area',
                description: 'Graphique de performance du portefeuille',
                size: 'lg',
                category: 'portfolio',
                component: 'PerformanceChartWidget'
            },
            {
                id: 'news-feed',
                title: 'Actualités',
                icon: 'fas fa-newspaper',
                description: 'Dernières nouvelles financières',
                size: 'md',
                category: 'news',
                component: 'NewsFeedWidget'
            },
            {
                id: 'economic-calendar',
                title: 'Calendrier Économique',
                icon: 'fas fa-calendar-alt',
                description: 'Événements économiques importants',
                size: 'md',
                category: 'market',
                component: 'EconomicCalendarWidget'
            },
            {
                id: 'risk-meter',
                title: 'Indicateur de Risque',
                icon: 'fas fa-tachometer-alt',
                description: 'Niveau de risque actuel',
                size: 'sm',
                category: 'risk',
                component: 'RiskMeterWidget'
            },
            {
                id: 'top-movers',
                title: 'Plus Gros Mouvements',
                icon: 'fas fa-arrow-up',
                description: 'Actions avec les plus gros mouvements',
                size: 'md',
                category: 'market',
                component: 'TopMoversWidget'
            },
            {
                id: 'trading-signals',
                title: 'Signaux Trading',
                icon: 'fas fa-signal',
                description: 'Signaux d\'achat/vente automatiques',
                size: 'md',
                category: 'trading',
                component: 'TradingSignalsWidget'
            },
            {
                id: 'currency-rates',
                title: 'Taux de Change',
                icon: 'fas fa-coins',
                description: 'Principales paires de devises',
                size: 'sm',
                category: 'market',
                component: 'CurrencyRatesWidget'
            }
        ];
    }

    /**
     * Configuration du drag-and-drop
     */
    setupDragAndDrop() {
        this.widgetContainer = document.querySelector('.dashboard-widgets');
        
        if (!this.widgetContainer) {
            console.warn('Container de widgets non trouvé');
            return;
        }

        // Rendre les widgets existants draggables
        this.makeDraggable();
        
        // Setup des zones de drop
        this.setupDropZones();
    }

    /**
     * Rendre les widgets draggables
     */
    makeDraggable() {
        const widgets = this.widgetContainer.querySelectorAll('.widget');
        
        widgets.forEach(widget => {
            widget.draggable = true;
            widget.addEventListener('dragstart', this.handleDragStart.bind(this));
            widget.addEventListener('dragend', this.handleDragEnd.bind(this));
        });
    }

    /**
     * Configuration des zones de drop
     */
    setupDropZones() {
        // Créer des zones de drop entre les widgets
        this.createDropZones();
        
        // Événements pour les zones de drop
        document.addEventListener('dragover', this.handleDragOver.bind(this));
        document.addEventListener('drop', this.handleDrop.bind(this));
    }

    /**
     * Créer les zones de drop visuelles
     */
    createDropZones() {
        const widgets = this.widgetContainer.querySelectorAll('.widget');
        
        widgets.forEach((widget, index) => {
            // Zone de drop avant le widget
            const dropZone = document.createElement('div');
            dropZone.className = 'widget-drop-zone';
            dropZone.dataset.position = index;
            widget.parentNode.insertBefore(dropZone, widget);
        });

        // Zone de drop à la fin
        const lastDropZone = document.createElement('div');
        lastDropZone.className = 'widget-drop-zone';
        lastDropZone.dataset.position = widgets.length;
        this.widgetContainer.appendChild(lastDropZone);
    }

    /**
     * Gestionnaire de début de drag
     */
    handleDragStart(e) {
        this.draggedWidget = e.target.closest('.widget');
        this.draggedWidget.classList.add('dragging');
        
        // Afficher les zones de drop
        this.showDropZones();
        
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', this.draggedWidget.outerHTML);
    }

    /**
     * Gestionnaire de fin de drag
     */
    handleDragEnd(e) {
        if (this.draggedWidget) {
            this.draggedWidget.classList.remove('dragging');
            this.draggedWidget = null;
        }
        
        // Masquer les zones de drop
        this.hideDropZones();
    }

    /**
     * Gestionnaire de drag over
     */
    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        
        const dropZone = e.target.closest('.widget-drop-zone');
        if (dropZone) {
            dropZone.classList.add('drop-zone-active');
        }
    }

    /**
     * Gestionnaire de drop
     */
    handleDrop(e) {
        e.preventDefault();
        
        const dropZone = e.target.closest('.widget-drop-zone');
        if (dropZone && this.draggedWidget) {
            const position = parseInt(dropZone.dataset.position);
            this.moveWidget(this.draggedWidget, position);
            this.saveLayout();
        }
        
        // Nettoyer les classes CSS
        document.querySelectorAll('.drop-zone-active').forEach(zone => {
            zone.classList.remove('drop-zone-active');
        });
    }

    /**
     * Déplacer un widget à une position spécifique
     */
    moveWidget(widget, position) {
        const widgets = Array.from(this.widgetContainer.querySelectorAll('.widget'));
        const currentIndex = widgets.indexOf(widget);
        
        if (currentIndex === -1) return;
        
        // Retirer le widget de sa position actuelle
        widget.remove();
        
        // L'insérer à la nouvelle position
        if (position >= widgets.length) {
            this.widgetContainer.appendChild(widget);
        } else {
            const targetWidget = widgets[position];
            this.widgetContainer.insertBefore(widget, targetWidget);
        }
        
        // Recréer les zones de drop
        this.clearDropZones();
        this.createDropZones();
    }

    /**
     * Afficher les zones de drop
     */
    showDropZones() {
        document.querySelectorAll('.widget-drop-zone').forEach(zone => {
            zone.classList.add('visible');
        });
    }

    /**
     * Masquer les zones de drop
     */
    hideDropZones() {
        document.querySelectorAll('.widget-drop-zone').forEach(zone => {
            zone.classList.remove('visible', 'drop-zone-active');
        });
    }

    /**
     * Nettoyer les zones de drop existantes
     */
    clearDropZones() {
        document.querySelectorAll('.widget-drop-zone').forEach(zone => {
            zone.remove();
        });
    }

    /**
     * Configuration des contrôles de widgets
     */
    setupWidgetControls() {
        // Bouton pour ouvrir le panel de personnalisation
        this.createCustomizeButton();
        
        // Gestionnaire des actions sur les widgets
        document.addEventListener('click', this.handleWidgetAction.bind(this));
    }

    /**
     * Créer le bouton de personnalisation
     */
    createCustomizeButton() {
        const header = document.querySelector('.header-right');
        if (!header) return;

        const customizeButton = document.createElement('button');
        customizeButton.className = 'header-btn customize-dashboard-btn';
        customizeButton.title = 'Personnaliser le dashboard';
        customizeButton.innerHTML = '<i class="fas fa-cogs"></i>';
        customizeButton.addEventListener('click', this.toggleCustomizePanel.bind(this));

        // Insérer avant le bouton de thème
        const themeButton = header.querySelector('.theme-toggle');
        if (themeButton) {
            header.insertBefore(customizeButton, themeButton);
        } else {
            header.appendChild(customizeButton);
        }
    }

    /**
     * Basculer le panel de personnalisation
     */
    toggleCustomizePanel() {
        let panel = document.getElementById('customize-panel');
        
        if (!panel) {
            this.createCustomizePanel();
        } else {
            panel.classList.toggle('open');
        }
    }

    /**
     * Créer le panel de personnalisation
     */
    createCustomizePanel() {
        const panel = document.createElement('div');
        panel.id = 'customize-panel';
        panel.className = 'customize-panel';
        
        panel.innerHTML = `
            <div class="customize-header">
                <h3><i class="fas fa-cogs"></i> Personnaliser le Dashboard</h3>
                <button class="btn-close" onclick="this.closest('.customize-panel').classList.remove('open')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <div class="customize-body">
                <div class="customize-section">
                    <h4>Widgets Disponibles</h4>
                    <div class="available-widgets" id="available-widgets">
                        ${this.renderAvailableWidgets()}
                    </div>
                </div>
                
                <div class="customize-section">
                    <h4>Actions</h4>
                    <div class="customize-actions">
                        <button class="btn btn-sm btn-outline" onclick="widgetManager.resetLayout()">
                            <i class="fas fa-undo"></i> Réinitialiser
                        </button>
                        <button class="btn btn-sm btn-primary" onclick="widgetManager.saveLayout()">
                            <i class="fas fa-save"></i> Sauvegarder
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(panel);
        
        // Ouvrir le panel
        requestAnimationFrame(() => {
            panel.classList.add('open');
        });
    }

    /**
     * Rendre les widgets disponibles
     */
    renderAvailableWidgets() {
        return this.availableWidgets.map(widget => `
            <div class="available-widget" data-widget-id="${widget.id}">
                <div class="widget-icon">
                    <i class="${widget.icon}"></i>
                </div>
                <div class="widget-info">
                    <div class="widget-title">${widget.title}</div>
                    <div class="widget-description">${widget.description}</div>
                </div>
                <div class="widget-actions">
                    <button class="btn btn-xs btn-primary add-widget-btn" data-widget-id="${widget.id}">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    /**
     * Gestionnaire des actions sur les widgets
     */
    handleWidgetAction(e) {
        const action = e.target.closest('[data-action]');
        if (!action) return;

        const actionType = action.dataset.action;
        const widgetElement = action.closest('.widget');
        
        switch (actionType) {
            case 'remove':
                this.removeWidget(widgetElement);
                break;
            case 'configure':
                this.configureWidget(widgetElement);
                break;
            case 'minimize':
                this.toggleWidget(widgetElement);
                break;
        }
    }

    /**
     * Supprimer un widget
     */
    removeWidget(widgetElement) {
        if (confirm('Êtes-vous sûr de vouloir supprimer ce widget ?')) {
            widgetElement.remove();
            this.clearDropZones();
            this.createDropZones();
            this.saveLayout();
        }
    }

    /**
     * Configurer un widget
     */
    configureWidget(widgetElement) {
        // TODO: Implémenter la configuration des widgets
        console.log('Configuration du widget:', widgetElement.dataset.widgetId);
    }

    /**
     * Minimiser/maximiser un widget
     */
    toggleWidget(widgetElement) {
        widgetElement.classList.toggle('minimized');
        this.saveLayout();
    }

    /**
     * Sauvegarder la disposition
     */
    saveLayout() {
        const layout = Array.from(this.widgetContainer.querySelectorAll('.widget')).map(widget => ({
            id: widget.dataset.widgetId,
            minimized: widget.classList.contains('minimized')
        }));
        
        localStorage.setItem(this.storageKey, JSON.stringify(layout));
        this.showNotification('Disposition sauvegardée', 'success');
    }

    /**
     * Charger la disposition sauvegardée
     */
    loadSavedLayout() {
        const saved = localStorage.getItem(this.storageKey);
        if (!saved) return;

        try {
            const layout = JSON.parse(saved);
            this.applyLayout(layout);
        } catch (e) {
            console.error('Erreur lors du chargement de la disposition:', e);
        }
    }

    /**
     * Appliquer une disposition
     */
    applyLayout(layout) {
        // TODO: Implémenter l'application de la disposition
        console.log('Application de la disposition:', layout);
    }

    /**
     * Réinitialiser la disposition
     */
    resetLayout() {
        if (confirm('Êtes-vous sûr de vouloir réinitialiser la disposition ?')) {
            localStorage.removeItem(this.storageKey);
            window.location.reload();
        }
    }

    /**
     * Afficher une notification
     */
    showNotification(message, type = 'info') {
        // Utiliser le système de notification existant
        if (window.userMenuManager && window.userMenuManager.showNotification) {
            window.userMenuManager.showNotification(message, type);
        }
    }
}

// Initialiser le gestionnaire de widgets
document.addEventListener('DOMContentLoaded', () => {
    window.widgetManager = new WidgetManager();
});

// Exporter pour usage dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WidgetManager;
}