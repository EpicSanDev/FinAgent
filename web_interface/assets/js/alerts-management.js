/**
 * Interface de gestion des alertes
 * Modal pour créer, modifier et gérer les alertes financières
 */

class AlertsManagement {
    constructor() {
        this.modal = null;
        this.currentAlert = null;
        this.alertTypes = {
            PRICE_ABOVE: { label: 'Prix au-dessus', icon: 'fas fa-arrow-up', color: 'success' },
            PRICE_BELOW: { label: 'Prix en-dessous', icon: 'fas fa-arrow-down', color: 'error' },
            VOLUME_SPIKE: { label: 'Pic de volume', icon: 'fas fa-chart-bar', color: 'info' },
            RSI_OVERSOLD: { label: 'RSI survente', icon: 'fas fa-chart-line', color: 'warning' },
            RSI_OVERBOUGHT: { label: 'RSI surachat', icon: 'fas fa-chart-line', color: 'warning' },
            MACD_BULLISH: { label: 'MACD haussier', icon: 'fas fa-trending-up', color: 'success' },
            MACD_BEARISH: { label: 'MACD baissier', icon: 'fas fa-trending-down', color: 'error' },
            BOLLINGER_BREAKOUT: { label: 'Cassure Bollinger', icon: 'fas fa-expand-arrows-alt', color: 'info' }
        };
        
        this.init();
    }

    init() {
        this.createModal();
        this.setupEventListeners();
    }

    /**
     * Créer la modal de gestion des alertes
     */
    createModal() {
        this.modal = document.createElement('div');
        this.modal.className = 'alerts-management-modal';
        this.modal.innerHTML = `
            <div class="alerts-modal-overlay">
                <div class="alerts-modal-panel">
                    <div class="alerts-modal-header">
                        <h2 class="alerts-modal-title">
                            <i class="fas fa-exclamation-triangle"></i>
                            Gestion des Alertes
                        </h2>
                        <button class="alerts-modal-close" id="close-alerts-modal">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="alerts-modal-tabs">
                        <button class="alerts-tab active" data-tab="list">
                            <i class="fas fa-list"></i>
                            Mes Alertes
                        </button>
                        <button class="alerts-tab" data-tab="create">
                            <i class="fas fa-plus"></i>
                            Créer une Alerte
                        </button>
                        <button class="alerts-tab" data-tab="templates">
                            <i class="fas fa-copy"></i>
                            Modèles
                        </button>
                    </div>
                    
                    <div class="alerts-modal-content">
                        <!-- Onglet Liste des alertes -->
                        <div class="alerts-tab-content active" id="alerts-list-tab">
                            <div class="alerts-toolbar">
                                <div class="alerts-stats">
                                    <div class="alert-stat">
                                        <span class="stat-value" id="total-alerts">0</span>
                                        <span class="stat-label">Total</span>
                                    </div>
                                    <div class="alert-stat">
                                        <span class="stat-value" id="active-alerts">0</span>
                                        <span class="stat-label">Actives</span>
                                    </div>
                                    <div class="alert-stat">
                                        <span class="stat-value" id="triggered-alerts">0</span>
                                        <span class="stat-label">Déclenchées</span>
                                    </div>
                                </div>
                                <div class="alerts-actions">
                                    <button class="btn btn-outline" id="disable-all-alerts">
                                        <i class="fas fa-pause"></i>
                                        Tout désactiver
                                    </button>
                                    <button class="btn btn-outline" id="enable-all-alerts">
                                        <i class="fas fa-play"></i>
                                        Tout activer
                                    </button>
                                    <button class="btn btn-danger" id="clear-triggered-alerts">
                                        <i class="fas fa-trash"></i>
                                        Effacer déclenchées
                                    </button>
                                </div>
                            </div>
                            
                            <div class="alerts-filter">
                                <input type="text" placeholder="Rechercher une alerte..." class="alerts-search" id="alerts-search">
                                <select class="alerts-filter-select" id="alerts-type-filter">
                                    <option value="">Tous les types</option>
                                    <option value="PRICE_ABOVE">Prix au-dessus</option>
                                    <option value="PRICE_BELOW">Prix en-dessous</option>
                                    <option value="VOLUME_SPIKE">Pic de volume</option>
                                    <option value="RSI_OVERSOLD">RSI survente</option>
                                    <option value="RSI_OVERBOUGHT">RSI surachat</option>
                                    <option value="MACD_BULLISH">MACD haussier</option>
                                    <option value="MACD_BEARISH">MACD baissier</option>
                                </select>
                                <select class="alerts-filter-select" id="alerts-status-filter">
                                    <option value="">Tous les statuts</option>
                                    <option value="active">Actives</option>
                                    <option value="triggered">Déclenchées</option>
                                    <option value="disabled">Désactivées</option>
                                </select>
                            </div>
                            
                            <div class="alerts-list" id="alerts-list">
                                <!-- Liste des alertes générée dynamiquement -->
                            </div>
                        </div>
                        
                        <!-- Onglet Création d'alerte -->
                        <div class="alerts-tab-content" id="alerts-create-tab">
                            <form class="alerts-create-form" id="alerts-create-form">
                                <div class="form-section">
                                    <h3>Type d'alerte</h3>
                                    <div class="alert-types-grid">
                                        ${Object.entries(this.alertTypes).map(([key, type]) => `
                                            <label class="alert-type-card">
                                                <input type="radio" name="alertType" value="${key}" class="alert-type-radio">
                                                <div class="alert-type-content">
                                                    <i class="${type.icon} alert-type-icon alert-${type.color}"></i>
                                                    <span class="alert-type-label">${type.label}</span>
                                                </div>
                                            </label>
                                        `).join('')}
                                    </div>
                                </div>
                                
                                <div class="form-section">
                                    <h3>Configuration</h3>
                                    <div class="form-grid">
                                        <div class="form-group">
                                            <label for="alert-symbol">Symbole</label>
                                            <input type="text" id="alert-symbol" class="form-input" placeholder="AAPL, GOOGL, etc." required>
                                            <div class="symbol-suggestions" id="symbol-suggestions"></div>
                                        </div>
                                        
                                        <div class="form-group">
                                            <label for="alert-name">Nom de l'alerte</label>
                                            <input type="text" id="alert-name" class="form-input" placeholder="Nom personnalisé (optionnel)">
                                        </div>
                                        
                                        <div class="form-group" id="alert-value-group">
                                            <label for="alert-value">Valeur</label>
                                            <input type="number" id="alert-value" class="form-input" step="0.01" placeholder="Prix cible">
                                        </div>
                                        
                                        <div class="form-group">
                                            <label for="alert-cooldown">Délai entre alertes (minutes)</label>
                                            <select id="alert-cooldown" class="form-select">
                                                <option value="300000">5 minutes</option>
                                                <option value="900000">15 minutes</option>
                                                <option value="1800000">30 minutes</option>
                                                <option value="3600000">1 heure</option>
                                                <option value="21600000">6 heures</option>
                                                <option value="86400000">24 heures</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="form-section">
                                    <h3>Notifications</h3>
                                    <div class="notification-options">
                                        <label class="checkbox-option">
                                            <input type="checkbox" id="notif-push" checked>
                                            <span class="checkbox-custom"></span>
                                            <span class="checkbox-label">
                                                <i class="fas fa-bell"></i>
                                                Notification push
                                            </span>
                                        </label>
                                        <label class="checkbox-option">
                                            <input type="checkbox" id="notif-sound" checked>
                                            <span class="checkbox-custom"></span>
                                            <span class="checkbox-label">
                                                <i class="fas fa-volume-up"></i>
                                                Son d'alerte
                                            </span>
                                        </label>
                                        <label class="checkbox-option">
                                            <input type="checkbox" id="notif-desktop">
                                            <span class="checkbox-custom"></span>
                                            <span class="checkbox-label">
                                                <i class="fas fa-desktop"></i>
                                                Notification desktop
                                            </span>
                                        </label>
                                        <label class="checkbox-option">
                                            <input type="checkbox" id="notif-email">
                                            <span class="checkbox-custom"></span>
                                            <span class="checkbox-label">
                                                <i class="fas fa-envelope"></i>
                                                Email (Pro)
                                            </span>
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="form-section">
                                    <h3>Options avancées</h3>
                                    <div class="form-grid">
                                        <div class="form-group">
                                            <label for="alert-max-triggers">Nombre max de déclenchements</label>
                                            <select id="alert-max-triggers" class="form-select">
                                                <option value="">Illimité</option>
                                                <option value="1">1 fois</option>
                                                <option value="5">5 fois</option>
                                                <option value="10">10 fois</option>
                                                <option value="20">20 fois</option>
                                            </select>
                                        </div>
                                        
                                        <div class="form-group">
                                            <label>
                                                <input type="checkbox" id="alert-persistent">
                                                Alerte persistante
                                            </label>
                                            <small>L'alerte restera affichée jusqu'à action manuelle</small>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="form-actions">
                                    <button type="button" class="btn btn-outline" id="cancel-alert">
                                        Annuler
                                    </button>
                                    <button type="submit" class="btn btn-primary">
                                        <i class="fas fa-plus"></i>
                                        Créer l'alerte
                                    </button>
                                </div>
                            </form>
                        </div>
                        
                        <!-- Onglet Modèles -->
                        <div class="alerts-tab-content" id="alerts-templates-tab">
                            <div class="templates-grid">
                                <div class="template-card" data-template="price-breakout">
                                    <div class="template-icon">
                                        <i class="fas fa-chart-line"></i>
                                    </div>
                                    <h4>Cassure de prix</h4>
                                    <p>Alerte quand le prix dépasse un niveau de résistance ou support</p>
                                    <button class="btn btn-outline">Utiliser ce modèle</button>
                                </div>
                                
                                <div class="template-card" data-template="oversold-rsi">
                                    <div class="template-icon">
                                        <i class="fas fa-chart-area"></i>
                                    </div>
                                    <h4>RSI Survente</h4>
                                    <p>Opportunité d'achat quand RSI < 30</p>
                                    <button class="btn btn-outline">Utiliser ce modèle</button>
                                </div>
                                
                                <div class="template-card" data-template="volume-spike">
                                    <div class="template-icon">
                                        <i class="fas fa-chart-bar"></i>
                                    </div>
                                    <h4>Volume exceptionnel</h4>
                                    <p>Alerte sur un volume 3x supérieur à la moyenne</p>
                                    <button class="btn btn-outline">Utiliser ce modèle</button>
                                </div>
                                
                                <div class="template-card" data-template="macd-signal">
                                    <div class="template-icon">
                                        <i class="fas fa-wave-square"></i>
                                    </div>
                                    <h4>Signal MACD</h4>
                                    <p>Croisement MACD pour signaux d'entrée/sortie</p>
                                    <button class="btn btn-outline">Utiliser ce modèle</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.modal);
    }

    /**
     * Configuration des événements
     */
    setupEventListeners() {
        // Fermeture de la modal
        this.modal.querySelector('#close-alerts-modal').addEventListener('click', this.close.bind(this));
        this.modal.querySelector('.alerts-modal-overlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.close();
        });

        // Onglets
        this.modal.querySelectorAll('.alerts-tab').forEach(tab => {
            tab.addEventListener('click', this.switchTab.bind(this));
        });

        // Formulaire de création
        this.modal.querySelector('#alerts-create-form').addEventListener('submit', this.createAlert.bind(this));
        this.modal.querySelector('#cancel-alert').addEventListener('click', this.resetForm.bind(this));

        // Types d'alerte
        this.modal.querySelectorAll('.alert-type-radio').forEach(radio => {
            radio.addEventListener('change', this.updateFormForType.bind(this));
        });

        // Recherche de symboles
        this.modal.querySelector('#alert-symbol').addEventListener('input', this.searchSymbols.bind(this));

        // Actions de masse
        this.modal.querySelector('#disable-all-alerts').addEventListener('click', this.disableAllAlerts.bind(this));
        this.modal.querySelector('#enable-all-alerts').addEventListener('click', this.enableAllAlerts.bind(this));
        this.modal.querySelector('#clear-triggered-alerts').addEventListener('click', this.clearTriggeredAlerts.bind(this));

        // Filtres
        this.modal.querySelector('#alerts-search').addEventListener('input', this.filterAlerts.bind(this));
        this.modal.querySelector('#alerts-type-filter').addEventListener('change', this.filterAlerts.bind(this));
        this.modal.querySelector('#alerts-status-filter').addEventListener('change', this.filterAlerts.bind(this));

        // Modèles
        this.modal.querySelectorAll('.template-card button').forEach(btn => {
            btn.addEventListener('click', this.useTemplate.bind(this));
        });

        // Ouverture depuis le menu utilisateur
        document.getElementById('alerts-management-btn')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.open();
        });

        // Raccourci clavier
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'A') {
                e.preventDefault();
                this.open();
            }
        });
    }

    /**
     * Ouvrir la modal
     */
    open() {
        this.modal.classList.add('alerts-modal-open');
        document.body.style.overflow = 'hidden';
        this.loadAlerts();
        this.updateStats();
    }

    /**
     * Fermer la modal
     */
    close() {
        this.modal.classList.remove('alerts-modal-open');
        document.body.style.overflow = '';
        this.resetForm();
    }

    /**
     * Changer d'onglet
     */
    switchTab(e) {
        const tab = e.target.closest('.alerts-tab');
        const tabName = tab.dataset.tab;

        // Mettre à jour les onglets
        this.modal.querySelectorAll('.alerts-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Mettre à jour le contenu
        this.modal.querySelectorAll('.alerts-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        this.modal.querySelector(`#alerts-${tabName}-tab`).classList.add('active');

        // Actions spécifiques
        if (tabName === 'list') {
            this.loadAlerts();
        }
    }

    /**
     * Charger et afficher les alertes
     */
    loadAlerts() {
        if (!window.alertSystem) return;

        const alerts = window.alertSystem.alerts;
        const container = this.modal.querySelector('#alerts-list');

        if (alerts.length === 0) {
            container.innerHTML = `
                <div class="alerts-empty">
                    <i class="fas fa-bell-slash"></i>
                    <h3>Aucune alerte configurée</h3>
                    <p>Créez votre première alerte pour être notifié des opportunités de marché</p>
                    <button class="btn btn-primary" onclick="document.querySelector('[data-tab=\"create\"]').click()">
                        <i class="fas fa-plus"></i>
                        Créer une alerte
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = alerts.map(alert => this.renderAlertItem(alert)).join('');
    }

    /**
     * Rendre un élément d'alerte
     */
    renderAlertItem(alert) {
        const type = this.alertTypes[alert.type] || { label: alert.type, icon: 'fas fa-bell', color: 'info' };
        const status = alert.enabled ? (alert.triggered ? 'triggered' : 'active') : 'disabled';
        
        return `
            <div class="alert-item alert-${status}" data-alert-id="${alert.id}">
                <div class="alert-info">
                    <div class="alert-header">
                        <div class="alert-type">
                            <i class="${type.icon} alert-type-icon alert-${type.color}"></i>
                            <span class="alert-type-label">${type.label}</span>
                        </div>
                        <div class="alert-status">
                            <span class="status-badge status-${status}">${this.getStatusLabel(status)}</span>
                        </div>
                    </div>
                    
                    <div class="alert-details">
                        <h4 class="alert-name">${alert.name}</h4>
                        <div class="alert-config">
                            <span class="alert-symbol">${alert.symbol}</span>
                            ${alert.value ? `<span class="alert-value">${alert.value}</span>` : ''}
                        </div>
                        <div class="alert-meta">
                            <span>Créée ${this.formatDate(alert.createdAt)}</span>
                            ${alert.lastTriggered ? `• Déclenchée ${this.formatDate(alert.lastTriggered)}` : ''}
                            ${alert.triggerCount > 0 ? `• ${alert.triggerCount} déclenchement(s)` : ''}
                        </div>
                    </div>
                </div>
                
                <div class="alert-actions">
                    <button class="alert-action-btn" onclick="alertsManagement.toggleAlert('${alert.id}')" title="${alert.enabled ? 'Désactiver' : 'Activer'}">
                        <i class="fas fa-${alert.enabled ? 'pause' : 'play'}"></i>
                    </button>
                    <button class="alert-action-btn" onclick="alertsManagement.editAlert('${alert.id}')" title="Modifier">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="alert-action-btn" onclick="alertsManagement.duplicateAlert('${alert.id}')" title="Dupliquer">
                        <i class="fas fa-copy"></i>
                    </button>
                    <button class="alert-action-btn danger" onclick="alertsManagement.deleteAlert('${alert.id}')" title="Supprimer">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Créer une nouvelle alerte
     */
    createAlert(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const alertConfig = {
            type: formData.get('alertType'),
            symbol: this.modal.querySelector('#alert-symbol').value.toUpperCase(),
            name: this.modal.querySelector('#alert-name').value,
            value: parseFloat(this.modal.querySelector('#alert-value').value) || null,
            cooldown: parseInt(this.modal.querySelector('#alert-cooldown').value),
            maxTriggers: parseInt(this.modal.querySelector('#alert-max-triggers').value) || null,
            notifications: {
                push: this.modal.querySelector('#notif-push').checked,
                sound: this.modal.querySelector('#notif-sound').checked,
                desktop: this.modal.querySelector('#notif-desktop').checked,
                email: this.modal.querySelector('#notif-email').checked
            },
            persistent: this.modal.querySelector('#alert-persistent').checked
        };

        // Validation
        if (!alertConfig.type || !alertConfig.symbol) {
            window.notificationManager?.error('Veuillez remplir tous les champs obligatoires');
            return;
        }

        // Créer l'alerte
        if (window.alertSystem) {
            const alertId = window.alertSystem.createAlert(alertConfig);
            if (alertId) {
                this.resetForm();
                this.switchTab({ target: { closest: () => ({ dataset: { tab: 'list' } }) } });
                this.loadAlerts();
                this.updateStats();
            }
        }
    }

    /**
     * Actions sur les alertes
     */
    toggleAlert(alertId) {
        if (!window.alertSystem) return;
        
        const alert = window.alertSystem.getAlert(alertId);
        if (alert.enabled) {
            window.alertSystem.disableAlert(alertId);
        } else {
            window.alertSystem.enableAlert(alertId);
        }
        
        this.loadAlerts();
        this.updateStats();
    }

    deleteAlert(alertId) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer cette alerte ?')) return;
        
        if (window.alertSystem) {
            window.alertSystem.deleteAlert(alertId);
            this.loadAlerts();
            this.updateStats();
        }
    }

    editAlert(alertId) {
        // TODO: Implémenter l'édition d'alerte
        console.log('Édition d\'alerte:', alertId);
    }

    duplicateAlert(alertId) {
        if (!window.alertSystem) return;
        
        const alert = window.alertSystem.getAlert(alertId);
        if (alert) {
            const newConfig = { ...alert };
            delete newConfig.id;
            newConfig.name = `${alert.name} (copie)`;
            newConfig.enabled = true;
            newConfig.triggered = false;
            newConfig.triggerCount = 0;
            newConfig.lastTriggered = null;
            
            window.alertSystem.createAlert(newConfig);
            this.loadAlerts();
            this.updateStats();
        }
    }

    /**
     * Mettre à jour les statistiques
     */
    updateStats() {
        if (!window.alertSystem) return;
        
        const stats = window.alertSystem.getAlertStats();
        
        this.modal.querySelector('#total-alerts').textContent = stats.total;
        this.modal.querySelector('#active-alerts').textContent = stats.active;
        this.modal.querySelector('#triggered-alerts').textContent = stats.triggered;
    }

    /**
     * Actions de masse
     */
    disableAllAlerts() {
        if (!window.alertSystem) return;
        
        window.alertSystem.alerts.forEach(alert => {
            if (alert.enabled) {
                window.alertSystem.disableAlert(alert.id);
            }
        });
        
        this.loadAlerts();
        this.updateStats();
        window.notificationManager?.info('Toutes les alertes ont été désactivées');
    }

    enableAllAlerts() {
        if (!window.alertSystem) return;
        
        window.alertSystem.alerts.forEach(alert => {
            if (!alert.enabled) {
                window.alertSystem.enableAlert(alert.id);
            }
        });
        
        this.loadAlerts();
        this.updateStats();
        window.notificationManager?.info('Toutes les alertes ont été activées');
    }

    clearTriggeredAlerts() {
        if (!window.alertSystem) return;
        
        const triggeredAlerts = window.alertSystem.alerts.filter(a => a.triggered);
        if (triggeredAlerts.length === 0) {
            window.notificationManager?.info('Aucune alerte déclenchée à effacer');
            return;
        }
        
        if (!confirm(`Supprimer ${triggeredAlerts.length} alerte(s) déclenchée(s) ?`)) return;
        
        triggeredAlerts.forEach(alert => {
            window.alertSystem.deleteAlert(alert.id);
        });
        
        this.loadAlerts();
        this.updateStats();
        window.notificationManager?.success(`${triggeredAlerts.length} alerte(s) supprimée(s)`);
    }

    /**
     * Filtrer les alertes
     */
    filterAlerts() {
        // TODO: Implémenter le filtrage
        console.log('Filtrage des alertes');
    }

    /**
     * Utiliser un modèle
     */
    useTemplate(e) {
        const template = e.target.closest('.template-card').dataset.template;
        this.switchTab({ target: { closest: () => ({ dataset: { tab: 'create' } }) } });
        
        // Pré-remplir selon le modèle
        switch (template) {
            case 'price-breakout':
                this.modal.querySelector('[value="PRICE_ABOVE"]').checked = true;
                break;
            case 'oversold-rsi':
                this.modal.querySelector('[value="RSI_OVERSOLD"]').checked = true;
                this.modal.querySelector('#alert-value').value = '30';
                break;
            case 'volume-spike':
                this.modal.querySelector('[value="VOLUME_SPIKE"]').checked = true;
                this.modal.querySelector('#alert-value').value = '3';
                break;
            case 'macd-signal':
                this.modal.querySelector('[value="MACD_BULLISH"]').checked = true;
                break;
        }
        
        this.updateFormForType();
    }

    /**
     * Utilitaires
     */
    updateFormForType() {
        const selectedType = this.modal.querySelector('input[name="alertType"]:checked')?.value;
        const valueGroup = this.modal.querySelector('#alert-value-group');
        const valueInput = this.modal.querySelector('#alert-value');
        const valueLabel = valueGroup.querySelector('label');
        
        if (!selectedType) return;
        
        switch (selectedType) {
            case 'PRICE_ABOVE':
            case 'PRICE_BELOW':
                valueGroup.style.display = 'block';
                valueLabel.textContent = 'Prix cible';
                valueInput.placeholder = 'Prix en €';
                valueInput.step = '0.01';
                break;
            case 'VOLUME_SPIKE':
                valueGroup.style.display = 'block';
                valueLabel.textContent = 'Multiplicateur de volume';
                valueInput.placeholder = 'Ex: 2 pour 2x le volume moyen';
                valueInput.step = '0.1';
                break;
            case 'RSI_OVERSOLD':
                valueGroup.style.display = 'block';
                valueLabel.textContent = 'Seuil RSI';
                valueInput.placeholder = '30';
                valueInput.step = '1';
                break;
            case 'RSI_OVERBOUGHT':
                valueGroup.style.display = 'block';
                valueLabel.textContent = 'Seuil RSI';
                valueInput.placeholder = '70';
                valueInput.step = '1';
                break;
            default:
                valueGroup.style.display = 'none';
                break;
        }
    }

    searchSymbols() {
        // TODO: Implémenter la recherche de symboles
        console.log('Recherche de symboles');
    }

    resetForm() {
        this.modal.querySelector('#alerts-create-form').reset();
        this.modal.querySelectorAll('.alert-type-radio').forEach(radio => radio.checked = false);
        this.updateFormForType();
    }

    getStatusLabel(status) {
        const labels = {
            active: 'Active',
            triggered: 'Déclenchée',
            disabled: 'Désactivée'
        };
        return labels[status] || status;
    }

    formatDate(timestamp) {
        return new Date(timestamp).toLocaleDateString('fr-FR', {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// Initialiser la gestion des alertes
document.addEventListener('DOMContentLoaded', () => {
    window.alertsManagement = new AlertsManagement();
});

// Export pour usage dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AlertsManagement;
}