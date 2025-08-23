/**
 * Gestionnaire d'accessibilité pour FinAgent
 * Conforme aux directives WCAG 2.1 AA
 */

class AccessibilityManager {
    constructor() {
        this.focusHistory = [];
        this.currentFocusIndex = -1;
        this.isKeyboardNavigation = false;
        this.announcements = [];
        this.preferences = {
            highContrast: false,
            reducedMotion: false,
            largeText: false,
            screenReader: false
        };
        
        this.init();
    }
    
    init() {
        this.detectScreenReader();
        this.setupKeyboardNavigation();
        this.setupFocusManagement();
        this.setupLiveRegions();
        this.setupSkipLinks();
        this.setupARIAManagement();
        this.setupPreferences();
        this.setupFormValidation();
        this.setupModalAccessibility();
        this.setupTableAccessibility();
        this.setupTooltipAccessibility();
        
        // Détecter les préférences système
        this.detectSystemPreferences();
        
        // Initialiser les raccourcis clavier
        this.setupKeyboardShortcuts();
    }
    
    /**
     * Détecte la présence d'un lecteur d'écran
     */
    detectScreenReader() {
        // Détection basée sur les APIs disponibles
        this.preferences.screenReader = !!(
            window.speechSynthesis ||
            window.navigator.userAgent.includes('NVDA') ||
            window.navigator.userAgent.includes('JAWS') ||
            window.navigator.userAgent.includes('VoiceOver')
        );
        
        // Test avec un élément masqué
        const testElement = document.createElement('div');
        testElement.className = 'sr-only';
        testElement.textContent = 'Screen reader test';
        document.body.appendChild(testElement);
        
        setTimeout(() => {
            const computedStyle = window.getComputedStyle(testElement);
            if (computedStyle.position === 'absolute' && computedStyle.left === '-10000px') {
                this.preferences.screenReader = true;
            }
            document.body.removeChild(testElement);
        }, 100);
        
        if (this.preferences.screenReader) {
            document.body.classList.add('screen-reader-detected');
            this.announce('Lecteur d\'écran détecté. Navigation optimisée activée.');
        }
    }
    
    /**
     * Configure la navigation au clavier
     */
    setupKeyboardNavigation() {
        // Détecter l'utilisation du clavier
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab' || e.key === 'ArrowUp' || e.key === 'ArrowDown' || 
                e.key === 'ArrowLeft' || e.key === 'ArrowRight' || e.key === 'Enter' || e.key === ' ') {
                this.isKeyboardNavigation = true;
                document.body.classList.add('keyboard-navigation');
                document.body.classList.add('tab-navigation-visible');
            }
        });
        
        // Détecter l'utilisation de la souris
        document.addEventListener('mousedown', () => {
            this.isKeyboardNavigation = false;
            document.body.classList.remove('keyboard-navigation');
            document.body.classList.remove('tab-navigation-visible');
        });
        
        // Navigation par flèches dans les listes
        this.setupArrowNavigation();
        
        // Navigation par lettres (roving tabindex)
        this.setupRovingTabindex();
    }
    
    /**
     * Configure la navigation par flèches
     */
    setupArrowNavigation() {
        document.addEventListener('keydown', (e) => {
            const activeElement = document.activeElement;
            
            // Navigation dans les menus
            if (activeElement.closest('[role="menu"], [role="menubar"]')) {
                this.handleMenuNavigation(e);
            }
            
            // Navigation dans les listes
            if (activeElement.closest('[role="listbox"], [role="list"]')) {
                this.handleListNavigation(e);
            }
            
            // Navigation dans les onglets
            if (activeElement.closest('[role="tablist"]')) {
                this.handleTabNavigation(e);
            }
        });
    }
    
    /**
     * Gère la navigation dans les menus
     */
    handleMenuNavigation(e) {
        const menu = e.target.closest('[role="menu"], [role="menubar"]');
        const items = menu.querySelectorAll('[role="menuitem"], [role="menuitemcheckbox"], [role="menuitemradio"]');
        const currentIndex = Array.from(items).indexOf(e.target);
        
        let nextIndex = currentIndex;
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                nextIndex = (currentIndex + 1) % items.length;
                break;
            case 'ArrowUp':
                e.preventDefault();
                nextIndex = (currentIndex - 1 + items.length) % items.length;
                break;
            case 'Home':
                e.preventDefault();
                nextIndex = 0;
                break;
            case 'End':
                e.preventDefault();
                nextIndex = items.length - 1;
                break;
            case 'Escape':
                e.preventDefault();
                this.closeMenu(menu);
                return;
        }
        
        if (nextIndex !== currentIndex) {
            items[nextIndex].focus();
        }
    }
    
    /**
     * Gère la navigation dans les listes
     */
    handleListNavigation(e) {
        const list = e.target.closest('[role="listbox"], [role="list"]');
        const items = list.querySelectorAll('[role="option"], [role="listitem"]');
        const currentIndex = Array.from(items).indexOf(e.target);
        
        let nextIndex = currentIndex;
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                nextIndex = Math.min(currentIndex + 1, items.length - 1);
                break;
            case 'ArrowUp':
                e.preventDefault();
                nextIndex = Math.max(currentIndex - 1, 0);
                break;
            case 'Home':
                e.preventDefault();
                nextIndex = 0;
                break;
            case 'End':
                e.preventDefault();
                nextIndex = items.length - 1;
                break;
        }
        
        if (nextIndex !== currentIndex) {
            items[nextIndex].focus();
            
            // Sélection automatique dans les listbox
            if (list.getAttribute('role') === 'listbox') {
                items[currentIndex]?.setAttribute('aria-selected', 'false');
                items[nextIndex].setAttribute('aria-selected', 'true');
            }
        }
    }
    
    /**
     * Gère la navigation dans les onglets
     */
    handleTabNavigation(e) {
        const tablist = e.target.closest('[role="tablist"]');
        const tabs = tablist.querySelectorAll('[role="tab"]');
        const currentIndex = Array.from(tabs).indexOf(e.target);
        
        let nextIndex = currentIndex;
        
        switch (e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
                break;
            case 'ArrowRight':
                e.preventDefault();
                nextIndex = (currentIndex + 1) % tabs.length;
                break;
            case 'Home':
                e.preventDefault();
                nextIndex = 0;
                break;
            case 'End':
                e.preventDefault();
                nextIndex = tabs.length - 1;
                break;
        }
        
        if (nextIndex !== currentIndex) {
            tabs[currentIndex].setAttribute('aria-selected', 'false');
            tabs[currentIndex].setAttribute('tabindex', '-1');
            
            tabs[nextIndex].setAttribute('aria-selected', 'true');
            tabs[nextIndex].setAttribute('tabindex', '0');
            tabs[nextIndex].focus();
            
            // Activer automatiquement l'onglet
            tabs[nextIndex].click();
        }
    }
    
    /**
     * Configure le roving tabindex
     */
    setupRovingTabindex() {
        const containers = document.querySelectorAll('[data-roving-tabindex]');
        
        containers.forEach(container => {
            const items = container.querySelectorAll('[role="button"], [role="tab"], [role="menuitem"]');
            
            // Initialiser le premier élément comme focusable
            if (items.length > 0) {
                items[0].setAttribute('tabindex', '0');
                for (let i = 1; i < items.length; i++) {
                    items[i].setAttribute('tabindex', '-1');
                }
            }
            
            // Gérer les événements focus
            items.forEach((item, index) => {
                item.addEventListener('focus', () => {
                    items.forEach((otherItem, otherIndex) => {
                        otherItem.setAttribute('tabindex', index === otherIndex ? '0' : '-1');
                    });
                });
            });
        });
    }
    
    /**
     * Configure la gestion du focus
     */
    setupFocusManagement() {
        // Historique du focus
        document.addEventListener('focusin', (e) => {
            this.focusHistory.push(e.target);
            this.currentFocusIndex = this.focusHistory.length - 1;
            
            // Limiter l'historique
            if (this.focusHistory.length > 50) {
                this.focusHistory.shift();
                this.currentFocusIndex--;
            }
        });
        
        // Focus visible uniquement au clavier
        document.addEventListener('mousedown', (e) => {
            e.target.classList.add('mouse-focus');
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.querySelectorAll('.mouse-focus').forEach(el => {
                    el.classList.remove('mouse-focus');
                });
            }
        });
    }
    
    /**
     * Configure les régions live
     */
    setupLiveRegions() {
        // Créer les régions live si elles n'existent pas
        this.createLiveRegion('polite', 'aria-live-polite');
        this.createLiveRegion('assertive', 'aria-live-assertive');
        this.createLiveRegion('status', 'aria-live-status');
    }
    
    /**
     * Crée une région live
     */
    createLiveRegion(type, id) {
        if (!document.getElementById(id)) {
            const region = document.createElement('div');
            region.id = id;
            region.className = 'live-region sr-only';
            region.setAttribute('aria-live', type === 'status' ? 'polite' : type);
            region.setAttribute('aria-atomic', 'true');
            document.body.appendChild(region);
        }
    }
    
    /**
     * Annonce un message aux lecteurs d'écran
     */
    announce(message, priority = 'polite') {
        const regionId = priority === 'assertive' ? 'aria-live-assertive' : 
                        priority === 'status' ? 'aria-live-status' : 'aria-live-polite';
        
        const region = document.getElementById(regionId);
        if (region) {
            // Clear puis ajouter le message pour forcer la lecture
            region.textContent = '';
            setTimeout(() => {
                region.textContent = message;
            }, 10);
            
            // Log pour debug
            console.log(`[A11Y] ${priority.toUpperCase()}: ${message}`);
        }
        
        // Ajouter à l'historique
        this.announcements.push({
            message,
            priority,
            timestamp: new Date()
        });
        
        // Limiter l'historique
        if (this.announcements.length > 100) {
            this.announcements.shift();
        }
    }
    
    /**
     * Configure les liens de saut
     */
    setupSkipLinks() {
        // Créer les liens de saut si ils n'existent pas
        if (!document.querySelector('.skip-links')) {
            const skipLinks = document.createElement('div');
            skipLinks.className = 'skip-links';
            skipLinks.innerHTML = `
                <a href="#main-content" class="skip-link">Aller au contenu principal</a>
                <a href="#navigation" class="skip-link">Aller à la navigation</a>
                <a href="#search" class="skip-link">Aller à la recherche</a>
            `;
            document.body.insertBefore(skipLinks, document.body.firstChild);
        }
        
        // Gérer les clics sur les liens de saut
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('skip-link')) {
                e.preventDefault();
                const target = document.querySelector(e.target.getAttribute('href'));
                if (target) {
                    target.focus();
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    }
    
    /**
     * Configure la gestion ARIA
     */
    setupARIAManagement() {
        // Auto-générer les IDs pour les labels
        document.querySelectorAll('label[for=""]').forEach(label => {
            const input = label.nextElementSibling;
            if (input && (input.tagName === 'INPUT' || input.tagName === 'SELECT' || input.tagName === 'TEXTAREA')) {
                const id = 'input-' + Date.now() + Math.random().toString(36).substr(2, 9);
                input.id = id;
                label.setAttribute('for', id);
            }
        });
        
        // Auto-associer les descriptions d'erreur
        document.querySelectorAll('.form-error').forEach(error => {
            const formGroup = error.closest('.form-group');
            if (formGroup) {
                const input = formGroup.querySelector('input, select, textarea');
                if (input) {
                    const errorId = 'error-' + Date.now() + Math.random().toString(36).substr(2, 9);
                    error.id = errorId;
                    
                    const describedBy = input.getAttribute('aria-describedby');
                    input.setAttribute('aria-describedby', 
                        describedBy ? `${describedBy} ${errorId}` : errorId);
                }
            }
        });
        
        // Gérer les états expanded/collapsed
        document.addEventListener('click', (e) => {
            const button = e.target.closest('[aria-expanded]');
            if (button) {
                const isExpanded = button.getAttribute('aria-expanded') === 'true';
                button.setAttribute('aria-expanded', !isExpanded);
                
                const target = document.querySelector(button.getAttribute('aria-controls'));
                if (target) {
                    target.setAttribute('aria-hidden', isExpanded);
                }
            }
        });
    }
    
    /**
     * Configure les préférences d'accessibilité
     */
    setupPreferences() {
        // Charger les préférences sauvegardées
        const saved = localStorage.getItem('accessibility-preferences');
        if (saved) {
            this.preferences = { ...this.preferences, ...JSON.parse(saved) };
        }
        
        // Appliquer les préférences
        this.applyPreferences();
        
        // Créer le panneau de préférences
        this.createPreferencesPanel();
    }
    
    /**
     * Détecte les préférences système
     */
    detectSystemPreferences() {
        // Mouvement réduit
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            this.preferences.reducedMotion = true;
        }
        
        // Contraste élevé
        if (window.matchMedia('(prefers-contrast: high)').matches) {
            this.preferences.highContrast = true;
        }
        
        // Écouter les changements
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
            this.preferences.reducedMotion = e.matches;
            this.applyPreferences();
        });
        
        window.matchMedia('(prefers-contrast: high)').addEventListener('change', (e) => {
            this.preferences.highContrast = e.matches;
            this.applyPreferences();
        });
    }
    
    /**
     * Applique les préférences d'accessibilité
     */
    applyPreferences() {
        // Contraste élevé
        document.body.classList.toggle('high-contrast', this.preferences.highContrast);
        
        // Mouvement réduit
        document.body.classList.toggle('no-animations', this.preferences.reducedMotion);
        
        // Texte large
        document.body.classList.toggle('large-text', this.preferences.largeText);
        
        // Lecteur d'écran
        document.body.classList.toggle('screen-reader-mode', this.preferences.screenReader);
        
        // Sauvegarder
        localStorage.setItem('accessibility-preferences', JSON.stringify(this.preferences));
    }
    
    /**
     * Crée le panneau de préférences d'accessibilité
     */
    createPreferencesPanel() {
        const panel = document.createElement('div');
        panel.id = 'accessibility-preferences';
        panel.className = 'accessibility-panel';
        panel.setAttribute('role', 'dialog');
        panel.setAttribute('aria-labelledby', 'a11y-panel-title');
        panel.setAttribute('aria-modal', 'true');
        panel.innerHTML = `
            <div class="accessibility-panel-content">
                <div class="accessibility-panel-header">
                    <h2 id="a11y-panel-title">Préférences d'Accessibilité</h2>
                    <button class="btn-close" aria-label="Fermer le panneau">×</button>
                </div>
                <div class="accessibility-panel-body">
                    <div class="preference-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="pref-high-contrast" ${this.preferences.highContrast ? 'checked' : ''}>
                            <span class="checkmark"></span>
                            Contraste élevé
                        </label>
                        <p class="preference-description">Améliore la lisibilité avec des couleurs plus contrastées</p>
                    </div>
                    
                    <div class="preference-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="pref-reduced-motion" ${this.preferences.reducedMotion ? 'checked' : ''}>
                            <span class="checkmark"></span>
                            Réduire les animations
                        </label>
                        <p class="preference-description">Désactive ou réduit les animations et transitions</p>
                    </div>
                    
                    <div class="preference-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="pref-large-text" ${this.preferences.largeText ? 'checked' : ''}>
                            <span class="checkmark"></span>
                            Texte plus grand
                        </label>
                        <p class="preference-description">Augmente la taille du texte pour une meilleure lisibilité</p>
                    </div>
                    
                    <div class="preference-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="pref-screen-reader" ${this.preferences.screenReader ? 'checked' : ''}>
                            <span class="checkmark"></span>
                            Mode lecteur d'écran
                        </label>
                        <p class="preference-description">Optimise l'interface pour les lecteurs d'écran</p>
                    </div>
                </div>
                <div class="accessibility-panel-footer">
                    <button class="btn btn-primary" id="save-preferences">Sauvegarder</button>
                    <button class="btn btn-secondary" id="reset-preferences">Réinitialiser</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(panel);
        
        // Gérer les événements
        panel.querySelector('.btn-close').addEventListener('click', () => {
            this.closePreferencesPanel();
        });
        
        panel.querySelector('#save-preferences').addEventListener('click', () => {
            this.savePreferences();
        });
        
        panel.querySelector('#reset-preferences').addEventListener('click', () => {
            this.resetPreferences();
        });
        
        // Gérer les changements de préférences
        panel.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const prefName = e.target.id.replace('pref-', '').replace('-', '');
                const prefKey = prefName === 'highcontrast' ? 'highContrast' :
                               prefName === 'reducedmotion' ? 'reducedMotion' :
                               prefName === 'largetext' ? 'largeText' :
                               prefName === 'screenreader' ? 'screenReader' : prefName;
                
                this.preferences[prefKey] = e.target.checked;
                this.applyPreferences();
            });
        });
    }
    
    /**
     * Configure la validation de formulaire accessible
     */
    setupFormValidation() {
        document.addEventListener('invalid', (e) => {
            e.preventDefault();
            
            const input = e.target;
            const formGroup = input.closest('.form-group');
            
            if (formGroup) {
                // Marquer comme invalide
                input.classList.add('invalid');
                input.setAttribute('aria-invalid', 'true');
                
                // Créer ou mettre à jour le message d'erreur
                let errorElement = formGroup.querySelector('.form-error');
                if (!errorElement) {
                    errorElement = document.createElement('div');
                    errorElement.className = 'form-error';
                    errorElement.setAttribute('role', 'alert');
                    formGroup.appendChild(errorElement);
                }
                
                errorElement.textContent = input.validationMessage;
                
                // Associer l'erreur au champ
                const errorId = 'error-' + input.id || Date.now();
                errorElement.id = errorId;
                input.setAttribute('aria-describedby', errorId);
                
                // Annoncer l'erreur
                this.announce(`Erreur dans le champ ${input.labels[0]?.textContent || 'inconnu'}: ${input.validationMessage}`, 'assertive');
            }
        });
        
        document.addEventListener('input', (e) => {
            const input = e.target;
            if (input.validity.valid) {
                input.classList.remove('invalid');
                input.classList.add('valid');
                input.setAttribute('aria-invalid', 'false');
                
                const errorElement = input.closest('.form-group')?.querySelector('.form-error');
                if (errorElement) {
                    errorElement.remove();
                }
            }
        });
    }
    
    /**
     * Configure l'accessibilité des modales
     */
    setupModalAccessibility() {
        document.addEventListener('modalOpen', (e) => {
            const modal = e.detail.modal;
            this.setupModalFocusTrap(modal);
            this.announce('Boîte de dialogue ouverte', 'assertive');
        });
        
        document.addEventListener('modalClose', (e) => {
            this.announce('Boîte de dialogue fermée', 'assertive');
        });
    }
    
    /**
     * Configure le focus trap pour les modales
     */
    setupModalFocusTrap(modal) {
        const focusableElements = modal.querySelectorAll(
            'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        // Focus sur le premier élément
        if (firstElement) {
            firstElement.focus();
        }
        
        // Gérer Tab et Shift+Tab
        const handleKeyDown = (e) => {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            }
        };
        
        modal.addEventListener('keydown', handleKeyDown);
        
        // Nettoyer quand la modale se ferme
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && 
                    mutation.attributeName === 'aria-hidden' &&
                    modal.getAttribute('aria-hidden') === 'true') {
                    modal.removeEventListener('keydown', handleKeyDown);
                    observer.disconnect();
                }
            });
        });
        
        observer.observe(modal, { attributes: true });
    }
    
    /**
     * Configure l'accessibilité des tableaux
     */
    setupTableAccessibility() {
        document.querySelectorAll('table').forEach(table => {
            // Ajouter le rôle table si absent
            if (!table.getAttribute('role')) {
                table.setAttribute('role', 'table');
            }
            
            // Configurer les en-têtes
            const headers = table.querySelectorAll('th');
            headers.forEach((header, index) => {
                if (!header.id) {
                    header.id = `header-${table.id || 'table'}-${index}`;
                }
                
                // Ajouter les contrôles de tri
                if (header.classList.contains('sortable')) {
                    header.setAttribute('aria-sort', 'none');
                    header.setAttribute('tabindex', '0');
                    header.setAttribute('role', 'columnheader');
                    
                    header.addEventListener('click', () => {
                        this.handleTableSort(header);
                    });
                    
                    header.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            this.handleTableSort(header);
                        }
                    });
                }
            });
            
            // Associer les cellules aux en-têtes
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                cells.forEach((cell, index) => {
                    const header = headers[index];
                    if (header) {
                        cell.setAttribute('headers', header.id);
                    }
                });
            });
        });
    }
    
    /**
     * Gère le tri des tableaux
     */
    handleTableSort(header) {
        const currentSort = header.getAttribute('aria-sort');
        const newSort = currentSort === 'ascending' ? 'descending' : 'ascending';
        
        // Reset autres en-têtes
        header.closest('table').querySelectorAll('th[aria-sort]').forEach(th => {
            if (th !== header) {
                th.setAttribute('aria-sort', 'none');
            }
        });
        
        header.setAttribute('aria-sort', newSort);
        
        this.announce(`Tableau trié par ${header.textContent} en ordre ${newSort === 'ascending' ? 'croissant' : 'décroissant'}`, 'polite');
    }
    
    /**
     * Configure l'accessibilité des tooltips
     */
    setupTooltipAccessibility() {
        document.querySelectorAll('[data-tooltip], [title]').forEach(element => {
            const tooltipText = element.dataset.tooltip || element.title;
            
            if (tooltipText) {
                // Créer un ID unique pour le tooltip
                const tooltipId = 'tooltip-' + Date.now() + Math.random().toString(36).substr(2, 9);
                
                // Créer l'élément tooltip
                const tooltip = document.createElement('div');
                tooltip.id = tooltipId;
                tooltip.className = 'tooltip sr-only';
                tooltip.setAttribute('role', 'tooltip');
                tooltip.textContent = tooltipText;
                document.body.appendChild(tooltip);
                
                // Associer l'élément au tooltip
                element.setAttribute('aria-describedby', tooltipId);
                element.removeAttribute('title'); // Éviter le tooltip natif
                
                // Gérer l'affichage au focus
                element.addEventListener('focus', () => {
                    tooltip.classList.remove('sr-only');
                    this.announce(tooltipText, 'polite');
                });
                
                element.addEventListener('blur', () => {
                    tooltip.classList.add('sr-only');
                });
            }
        });
    }
    
    /**
     * Configure les raccourcis clavier
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Alt + A : Panneau d'accessibilité
            if (e.altKey && e.key === 'a') {
                e.preventDefault();
                this.togglePreferencesPanel();
            }
            
            // Alt + 1 : Aller au contenu principal
            if (e.altKey && e.key === '1') {
                e.preventDefault();
                const main = document.querySelector('#main-content, main');
                if (main) {
                    main.focus();
                    main.scrollIntoView({ behavior: 'smooth' });
                }
            }
            
            // Alt + 2 : Aller à la navigation
            if (e.altKey && e.key === '2') {
                e.preventDefault();
                const nav = document.querySelector('#navigation, nav');
                if (nav) {
                    nav.focus();
                    nav.scrollIntoView({ behavior: 'smooth' });
                }
            }
            
            // Alt + S : Aller à la recherche
            if (e.altKey && e.key === 's') {
                e.preventDefault();
                const search = document.querySelector('#search, [role="search"] input');
                if (search) {
                    search.focus();
                }
            }
        });
    }
    
    /**
     * Ouvre/ferme le panneau de préférences
     */
    togglePreferencesPanel() {
        const panel = document.getElementById('accessibility-preferences');
        const isOpen = panel.classList.contains('open');
        
        if (isOpen) {
            this.closePreferencesPanel();
        } else {
            this.openPreferencesPanel();
        }
    }
    
    /**
     * Ouvre le panneau de préférences
     */
    openPreferencesPanel() {
        const panel = document.getElementById('accessibility-preferences');
        panel.classList.add('open');
        panel.setAttribute('aria-hidden', 'false');
        
        // Focus sur le premier élément
        const firstFocusable = panel.querySelector('button, input');
        if (firstFocusable) {
            firstFocusable.focus();
        }
        
        this.announce('Panneau de préférences d\'accessibilité ouvert', 'assertive');
    }
    
    /**
     * Ferme le panneau de préférences
     */
    closePreferencesPanel() {
        const panel = document.getElementById('accessibility-preferences');
        panel.classList.remove('open');
        panel.setAttribute('aria-hidden', 'true');
        
        this.announce('Panneau de préférences fermé', 'assertive');
    }
    
    /**
     * Sauvegarde les préférences
     */
    savePreferences() {
        localStorage.setItem('accessibility-preferences', JSON.stringify(this.preferences));
        this.announce('Préférences sauvegardées', 'status');
    }
    
    /**
     * Réinitialise les préférences
     */
    resetPreferences() {
        this.preferences = {
            highContrast: false,
            reducedMotion: false,
            largeText: false,
            screenReader: false
        };
        
        this.applyPreferences();
        
        // Mettre à jour les checkboxes
        const panel = document.getElementById('accessibility-preferences');
        panel.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        this.announce('Préférences réinitialisées', 'status');
    }
    
    /**
     * Ferme un menu
     */
    closeMenu(menu) {
        menu.setAttribute('aria-expanded', 'false');
        const trigger = document.querySelector(`[aria-controls="${menu.id}"]`);
        if (trigger) {
            trigger.focus();
        }
    }
    
    /**
     * Utilitaires publics
     */
    
    // Focus sur un élément avec annonce
    focusWithAnnouncement(element, message) {
        element.focus();
        if (message) {
            this.announce(message, 'polite');
        }
    }
    
    // Ajouter un élément focusable
    makeFocusable(element, tabindex = 0) {
        element.setAttribute('tabindex', tabindex);
        element.classList.add('focusable');
    }
    
    // Retirer la focusabilité
    makeUnfocusable(element) {
        element.setAttribute('tabindex', '-1');
        element.classList.remove('focusable');
    }
    
    // Vérifier si un élément est visible pour les lecteurs d'écran
    isVisibleToScreenReaders(element) {
        const style = window.getComputedStyle(element);
        return !(
            style.display === 'none' ||
            style.visibility === 'hidden' ||
            style.opacity === '0' ||
            element.getAttribute('aria-hidden') === 'true' ||
            element.offsetParent === null
        );
    }
    
    // Obtenir tous les éléments focusables dans un conteneur
    getFocusableElements(container) {
        return container.querySelectorAll(
            'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
    }
}

// CSS pour le panneau d'accessibilité
const accessibilityPanelCSS = `
.accessibility-panel {
    position: fixed;
    top: 0;
    right: -400px;
    width: 400px;
    height: 100vh;
    background: var(--surface-color);
    border-left: 1px solid var(--border-color);
    box-shadow: var(--shadow-xl);
    z-index: 10000;
    transition: right 0.3s ease;
    overflow-y: auto;
}

.accessibility-panel.open {
    right: 0;
}

.accessibility-panel-content {
    padding: var(--space-6);
}

.accessibility-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-6);
    padding-bottom: var(--space-4);
    border-bottom: 1px solid var(--border-color);
}

.accessibility-panel-header h2 {
    margin: 0;
    font-size: var(--font-size-lg);
    color: var(--text-primary);
}

.preference-group {
    margin-bottom: var(--space-6);
}

.preference-description {
    font-size: var(--font-size-sm);
    color: var(--text-secondary);
    margin: var(--space-2) 0 0 0;
}

.accessibility-panel-footer {
    display: flex;
    gap: var(--space-3);
    margin-top: var(--space-6);
    padding-top: var(--space-4);
    border-top: 1px solid var(--border-color);
}

@media (max-width: 767.98px) {
    .accessibility-panel {
        width: 100%;
        right: -100%;
    }
}

@media (prefers-reduced-motion: reduce) {
    .accessibility-panel {
        transition: none;
    }
}
`;

// Injecter le CSS
const accessibilityStyle = document.createElement('style');
accessibilityStyle.textContent = accessibilityPanelCSS;
document.head.appendChild(accessibilityStyle);

// Initialiser le gestionnaire d'accessibilité
const accessibilityManager = new AccessibilityManager();

// Export pour utilisation externe
window.AccessibilityManager = AccessibilityManager;
window.accessibilityManager = accessibilityManager;