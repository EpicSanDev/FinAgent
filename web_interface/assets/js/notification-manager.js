/**
 * Gestionnaire de notifications
 * Système de notifications en temps réel avec différents types et actions
 */

class NotificationManager {
    constructor() {
        this.notifications = [];
        this.settings = {
            position: 'top-right', // top-right, top-left, bottom-right, bottom-left
            autoClose: true,
            autoCloseDelay: 5000,
            maxNotifications: 5,
            showProgress: true,
            enableSound: true,
            enableDesktop: false
        };
        
        this.container = null;
        this.centerContainer = null;
        this.soundEnabled = false;
        this.desktopEnabled = false;
        
        this.init();
    }

    init() {
        this.loadSettings();
        this.createContainers();
        this.setupEventListeners();
        this.requestPermissions();
        this.loadNotificationHistory();
    }

    /**
     * Créer les conteneurs de notifications
     */
    createContainers() {
        // Conteneur principal pour les notifications toast
        this.container = document.createElement('div');
        this.container.className = `notifications-container notifications-${this.settings.position}`;
        this.container.id = 'notifications-container';
        document.body.appendChild(this.container);

        // Conteneur pour le centre de notifications
        this.createNotificationCenter();
    }

    /**
     * Créer le centre de notifications
     */
    createNotificationCenter() {
        this.centerContainer = document.createElement('div');
        this.centerContainer.className = 'notification-center';
        this.centerContainer.innerHTML = `
            <div class="notification-center-overlay">
                <div class="notification-center-panel">
                    <div class="notification-center-header">
                        <h3 class="notification-center-title">
                            <i class="fas fa-bell"></i>
                            Notifications
                        </h3>
                        <div class="notification-center-actions">
                            <button class="notification-action-btn" id="mark-all-read">
                                <i class="fas fa-check-double"></i>
                                Tout marquer comme lu
                            </button>
                            <button class="notification-action-btn" id="clear-all-notifications">
                                <i class="fas fa-trash"></i>
                                Tout supprimer
                            </button>
                            <button class="notification-close-btn" id="close-notification-center">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>
                    <div class="notification-center-body">
                        <div class="notification-center-tabs">
                            <button class="notification-tab active" data-tab="all">
                                <i class="fas fa-list"></i>
                                Toutes (<span id="all-count">0</span>)
                            </button>
                            <button class="notification-tab" data-tab="unread">
                                <i class="fas fa-circle"></i>
                                Non lues (<span id="unread-count">0</span>)
                            </button>
                            <button class="notification-tab" data-tab="alerts">
                                <i class="fas fa-exclamation-triangle"></i>
                                Alertes (<span id="alerts-count">0</span>)
                            </button>
                        </div>
                        <div class="notification-center-content">
                            <div class="notification-list" id="notification-list"></div>
                        </div>
                    </div>
                    <div class="notification-center-footer">
                        <button class="notification-settings-btn" id="notification-settings">
                            <i class="fas fa-cog"></i>
                            Paramètres de notification
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(this.centerContainer);
    }

    /**
     * Configuration des événements
     */
    setupEventListeners() {
        // Bouton de notification dans le header
        const notificationBtn = document.getElementById('notifications-btn');
        if (notificationBtn) {
            notificationBtn.addEventListener('click', this.toggleNotificationCenter.bind(this));
        }

        // Actions du centre de notifications
        document.getElementById('close-notification-center')?.addEventListener('click', 
            this.closeNotificationCenter.bind(this));
        document.getElementById('mark-all-read')?.addEventListener('click', 
            this.markAllAsRead.bind(this));
        document.getElementById('clear-all-notifications')?.addEventListener('click', 
            this.clearAllNotifications.bind(this));
        document.getElementById('notification-settings')?.addEventListener('click', 
            this.showNotificationSettings.bind(this));

        // Onglets du centre de notifications
        const tabs = document.querySelectorAll('.notification-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', this.switchNotificationTab.bind(this));
        });

        // Fermer le centre en cliquant à l'extérieur
        this.centerContainer.addEventListener('click', (e) => {
            if (e.target === this.centerContainer || e.target.classList.contains('notification-center-overlay')) {
                this.closeNotificationCenter();
            }
        });

        // Raccourcis clavier
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
    }

    /**
     * Demander les permissions pour les notifications desktop
     */
    async requestPermissions() {
        if ('Notification' in window) {
            if (Notification.permission === 'default') {
                const permission = await Notification.requestPermission();
                this.desktopEnabled = permission === 'granted';
            } else {
                this.desktopEnabled = Notification.permission === 'granted';
            }
        }
    }

    /**
     * Afficher une notification
     */
    show(options) {
        const notification = {
            id: this.generateId(),
            type: options.type || 'info', // success, error, warning, info, alert
            title: options.title || '',
            message: options.message || '',
            icon: options.icon || this.getDefaultIcon(options.type),
            timestamp: Date.now(),
            read: false,
            persistent: options.persistent || false,
            actions: options.actions || [],
            data: options.data || {},
            autoClose: options.autoClose !== undefined ? options.autoClose : this.settings.autoClose,
            autoCloseDelay: options.autoCloseDelay || this.settings.autoCloseDelay
        };

        // Ajouter aux notifications
        this.notifications.unshift(notification);
        this.limitNotifications();

        // Créer la notification toast
        this.createToastNotification(notification);

        // Notification desktop si activée
        if (this.settings.enableDesktop && this.desktopEnabled && !document.hasFocus()) {
            this.showDesktopNotification(notification);
        }

        // Son si activé
        if (this.settings.enableSound && this.soundEnabled) {
            this.playNotificationSound(notification.type);
        }

        // Mettre à jour l'interface
        this.updateNotificationBadge();
        this.updateNotificationCenter();
        this.saveNotifications();

        // Événement personnalisé
        document.dispatchEvent(new CustomEvent('notificationShown', {
            detail: notification
        }));

        return notification.id;
    }

    /**
     * Créer une notification toast
     */
    createToastNotification(notification) {
        const toast = document.createElement('div');
        toast.className = `notification-toast notification-${notification.type}`;
        toast.dataset.notificationId = notification.id;

        toast.innerHTML = `
            <div class="notification-icon">
                <i class="${notification.icon}"></i>
            </div>
            <div class="notification-content">
                ${notification.title ? `<div class="notification-title">${notification.title}</div>` : ''}
                <div class="notification-message">${notification.message}</div>
                ${notification.actions.length > 0 ? `
                    <div class="notification-actions">
                        ${notification.actions.map(action => `
                            <button class="notification-action-btn" data-action="${action.id}">
                                ${action.icon ? `<i class="${action.icon}"></i>` : ''}
                                ${action.label}
                            </button>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
            <div class="notification-controls">
                ${this.settings.showProgress && notification.autoClose ? `
                    <div class="notification-progress">
                        <div class="notification-progress-bar"></div>
                    </div>
                ` : ''}
                <button class="notification-close" data-notification-id="${notification.id}">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Événements
        this.setupToastEvents(toast, notification);

        // Ajouter au conteneur
        this.container.appendChild(toast);

        // Animation d'entrée
        requestAnimationFrame(() => {
            toast.classList.add('notification-show');
        });

        // Auto-fermeture
        if (notification.autoClose && !notification.persistent) {
            this.scheduleAutoClose(notification.id, notification.autoCloseDelay);
        }
    }

    /**
     * Configuration des événements du toast
     */
    setupToastEvents(toast, notification) {
        // Bouton de fermeture
        const closeBtn = toast.querySelector('.notification-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.dismiss(notification.id);
            });
        }

        // Actions personnalisées
        const actionBtns = toast.querySelectorAll('.notification-action-btn');
        actionBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const actionId = e.target.closest('[data-action]').dataset.action;
                const action = notification.actions.find(a => a.id === actionId);
                if (action && action.callback) {
                    action.callback(notification);
                }
                if (action && action.dismissOnClick !== false) {
                    this.dismiss(notification.id);
                }
            });
        });

        // Clic sur la notification
        toast.addEventListener('click', (e) => {
            if (!e.target.closest('.notification-controls') && !e.target.closest('.notification-actions')) {
                this.markAsRead(notification.id);
                if (notification.data.onClick) {
                    notification.data.onClick(notification);
                }
            }
        });

        // Hover pour pause auto-close
        toast.addEventListener('mouseenter', () => {
            this.pauseAutoClose(notification.id);
        });

        toast.addEventListener('mouseleave', () => {
            this.resumeAutoClose(notification.id);
        });
    }

    /**
     * Programmer la fermeture automatique
     */
    scheduleAutoClose(notificationId, delay) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (!notification) return;

        const toast = document.querySelector(`[data-notification-id="${notificationId}"]`);
        const progressBar = toast?.querySelector('.notification-progress-bar');

        if (progressBar) {
            progressBar.style.animationDuration = `${delay}ms`;
            progressBar.classList.add('notification-progress-active');
        }

        notification.autoCloseTimer = setTimeout(() => {
            this.dismiss(notificationId);
        }, delay);
    }

    /**
     * Mettre en pause la fermeture automatique
     */
    pauseAutoClose(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification && notification.autoCloseTimer) {
            clearTimeout(notification.autoCloseTimer);
            const toast = document.querySelector(`[data-notification-id="${notificationId}"]`);
            const progressBar = toast?.querySelector('.notification-progress-bar');
            if (progressBar) {
                progressBar.style.animationPlayState = 'paused';
            }
        }
    }

    /**
     * Reprendre la fermeture automatique
     */
    resumeAutoClose(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification && notification.autoClose) {
            const toast = document.querySelector(`[data-notification-id="${notificationId}"]`);
            const progressBar = toast?.querySelector('.notification-progress-bar');
            if (progressBar) {
                progressBar.style.animationPlayState = 'running';
                // Calculer le temps restant basé sur la progression
                const remainingTime = notification.autoCloseDelay * 0.7; // Approximation
                this.scheduleAutoClose(notificationId, remainingTime);
            }
        }
    }

    /**
     * Fermer une notification
     */
    dismiss(notificationId) {
        const toast = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (toast) {
            toast.classList.add('notification-hide');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }

        // Supprimer le timer si existant
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification && notification.autoCloseTimer) {
            clearTimeout(notification.autoCloseTimer);
        }

        // Événement personnalisé
        document.dispatchEvent(new CustomEvent('notificationDismissed', {
            detail: { notificationId }
        }));
    }

    /**
     * Marquer comme lu
     */
    markAsRead(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification && !notification.read) {
            notification.read = true;
            this.updateNotificationBadge();
            this.updateNotificationCenter();
            this.saveNotifications();
        }
    }

    /**
     * Marquer toutes comme lues
     */
    markAllAsRead() {
        this.notifications.forEach(notification => {
            notification.read = true;
        });
        this.updateNotificationBadge();
        this.updateNotificationCenter();
        this.saveNotifications();
    }

    /**
     * Supprimer toutes les notifications
     */
    clearAllNotifications() {
        this.notifications = [];
        this.updateNotificationBadge();
        this.updateNotificationCenter();
        this.saveNotifications();
        
        // Supprimer tous les toasts
        const toasts = document.querySelectorAll('.notification-toast');
        toasts.forEach(toast => {
            toast.classList.add('notification-hide');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        });
    }

    /**
     * Basculer le centre de notifications
     */
    toggleNotificationCenter() {
        if (this.centerContainer.classList.contains('notification-center-open')) {
            this.closeNotificationCenter();
        } else {
            this.openNotificationCenter();
        }
    }

    /**
     * Ouvrir le centre de notifications
     */
    openNotificationCenter() {
        this.centerContainer.classList.add('notification-center-open');
        this.updateNotificationCenter();
        document.body.style.overflow = 'hidden';
    }

    /**
     * Fermer le centre de notifications
     */
    closeNotificationCenter() {
        this.centerContainer.classList.remove('notification-center-open');
        document.body.style.overflow = '';
    }

    /**
     * Changer d'onglet dans le centre
     */
    switchNotificationTab(e) {
        const tab = e.target.closest('.notification-tab');
        if (!tab) return;

        // Mettre à jour l'état actif
        document.querySelectorAll('.notification-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Filtrer et afficher les notifications
        const tabType = tab.dataset.tab;
        this.renderNotificationList(tabType);
    }

    /**
     * Rendre la liste des notifications
     */
    renderNotificationList(filter = 'all') {
        const listContainer = document.getElementById('notification-list');
        if (!listContainer) return;

        let filteredNotifications = this.notifications;

        switch (filter) {
            case 'unread':
                filteredNotifications = this.notifications.filter(n => !n.read);
                break;
            case 'alerts':
                filteredNotifications = this.notifications.filter(n => n.type === 'alert' || n.type === 'error');
                break;
        }

        if (filteredNotifications.length === 0) {
            listContainer.innerHTML = `
                <div class="notification-list-empty">
                    <i class="fas fa-bell-slash"></i>
                    <p>Aucune notification</p>
                </div>
            `;
            return;
        }

        listContainer.innerHTML = filteredNotifications.map(notification => `
            <div class="notification-list-item ${notification.read ? 'read' : 'unread'}" data-notification-id="${notification.id}">
                <div class="notification-list-icon notification-${notification.type}">
                    <i class="${notification.icon}"></i>
                </div>
                <div class="notification-list-content">
                    ${notification.title ? `<div class="notification-list-title">${notification.title}</div>` : ''}
                    <div class="notification-list-message">${notification.message}</div>
                    <div class="notification-list-time">${this.formatTime(notification.timestamp)}</div>
                </div>
                <div class="notification-list-actions">
                    ${!notification.read ? `
                        <button class="notification-list-action" data-action="mark-read" title="Marquer comme lu">
                            <i class="fas fa-check"></i>
                        </button>
                    ` : ''}
                    <button class="notification-list-action" data-action="delete" title="Supprimer">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');

        // Ajouter les événements
        this.setupNotificationListEvents();
    }

    /**
     * Configuration des événements de la liste
     */
    setupNotificationListEvents() {
        const listItems = document.querySelectorAll('.notification-list-item');
        listItems.forEach(item => {
            const notificationId = item.dataset.notificationId;
            
            // Clic sur l'item
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.notification-list-actions')) {
                    this.markAsRead(notificationId);
                    const notification = this.notifications.find(n => n.id === notificationId);
                    if (notification && notification.data.onClick) {
                        notification.data.onClick(notification);
                        this.closeNotificationCenter();
                    }
                }
            });

            // Actions
            const actions = item.querySelectorAll('.notification-list-action');
            actions.forEach(action => {
                action.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const actionType = action.dataset.action;
                    
                    if (actionType === 'mark-read') {
                        this.markAsRead(notificationId);
                    } else if (actionType === 'delete') {
                        this.deleteNotification(notificationId);
                    }
                });
            });
        });
    }

    /**
     * Supprimer une notification
     */
    deleteNotification(notificationId) {
        this.notifications = this.notifications.filter(n => n.id !== notificationId);
        this.updateNotificationBadge();
        this.updateNotificationCenter();
        this.saveNotifications();
        this.dismiss(notificationId);
    }

    /**
     * Mettre à jour le badge de notification
     */
    updateNotificationBadge() {
        const badge = document.getElementById('notification-count');
        if (!badge) return;

        const unreadCount = this.notifications.filter(n => !n.read).length;
        
        if (unreadCount > 0) {
            badge.textContent = unreadCount > 99 ? '99+' : unreadCount.toString();
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    }

    /**
     * Mettre à jour le centre de notifications
     */
    updateNotificationCenter() {
        // Mettre à jour les compteurs
        const allCount = document.getElementById('all-count');
        const unreadCount = document.getElementById('unread-count');
        const alertsCount = document.getElementById('alerts-count');

        if (allCount) allCount.textContent = this.notifications.length;
        if (unreadCount) unreadCount.textContent = this.notifications.filter(n => !n.read).length;
        if (alertsCount) alertsCount.textContent = this.notifications.filter(n => n.type === 'alert' || n.type === 'error').length;

        // Recharger la liste active
        const activeTab = document.querySelector('.notification-tab.active');
        if (activeTab) {
            this.renderNotificationList(activeTab.dataset.tab);
        }
    }

    /**
     * Afficher les paramètres de notification
     */
    showNotificationSettings() {
        // TODO: Implémenter la modal de paramètres
        console.log('Paramètres de notification');
    }

    /**
     * Raccourcis clavier
     */
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + Shift + N pour ouvrir le centre
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'N') {
            e.preventDefault();
            this.toggleNotificationCenter();
        }
        
        // Escape pour fermer le centre
        if (e.key === 'Escape' && this.centerContainer.classList.contains('notification-center-open')) {
            this.closeNotificationCenter();
        }
    }

    /**
     * Notification desktop
     */
    showDesktopNotification(notification) {
        if (!this.desktopEnabled) return;

        const desktopNotification = new Notification(notification.title || 'FinAgent', {
            body: notification.message,
            icon: '/favicon.ico',
            tag: notification.id,
            requireInteraction: notification.persistent
        });

        desktopNotification.onclick = () => {
            window.focus();
            this.markAsRead(notification.id);
            if (notification.data.onClick) {
                notification.data.onClick(notification);
            }
            desktopNotification.close();
        };
    }

    /**
     * Jouer un son de notification
     */
    playNotificationSound(type) {
        // Implémenter les sons selon le type
        console.log(`Son de notification: ${type}`);
    }

    /**
     * Méthodes utilitaires
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    getDefaultIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle',
            alert: 'fas fa-bell'
        };
        return icons[type] || icons.info;
    }

    formatTime(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;
        
        if (diff < 60000) return 'À l\'instant';
        if (diff < 3600000) return `${Math.floor(diff / 60000)} min`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)} h`;
        return new Date(timestamp).toLocaleDateString('fr-FR');
    }

    limitNotifications() {
        if (this.notifications.length > this.settings.maxNotifications * 2) {
            this.notifications = this.notifications.slice(0, this.settings.maxNotifications * 2);
        }
    }

    /**
     * Persistance
     */
    saveNotifications() {
        localStorage.setItem('finagent_notifications', JSON.stringify(this.notifications.slice(0, 50)));
    }

    loadNotificationHistory() {
        const saved = localStorage.getItem('finagent_notifications');
        if (saved) {
            try {
                this.notifications = JSON.parse(saved);
                this.updateNotificationBadge();
            } catch (e) {
                this.notifications = [];
            }
        }
    }

    saveSettings() {
        localStorage.setItem('finagent_notification_settings', JSON.stringify(this.settings));
    }

    loadSettings() {
        const saved = localStorage.getItem('finagent_notification_settings');
        if (saved) {
            try {
                this.settings = { ...this.settings, ...JSON.parse(saved) };
            } catch (e) {
                // Utiliser les paramètres par défaut
            }
        }
    }

    /**
     * API publique pour les notifications rapides
     */
    success(message, title = 'Succès') {
        return this.show({ type: 'success', title, message });
    }

    error(message, title = 'Erreur') {
        return this.show({ type: 'error', title, message, persistent: true });
    }

    warning(message, title = 'Attention') {
        return this.show({ type: 'warning', title, message });
    }

    info(message, title = 'Information') {
        return this.show({ type: 'info', title, message });
    }

    alert(message, title = 'Alerte') {
        return this.show({ type: 'alert', title, message, persistent: true });
    }
}

// Initialiser le gestionnaire de notifications
document.addEventListener('DOMContentLoaded', () => {
    window.notificationManager = new NotificationManager();
});

// Export pour usage dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationManager;
}