/**
 * Gestionnaire de filtres avancés
 * Système de filtrage sophistiqué pour toutes les sections de l'application
 */

class AdvancedFilters {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = {
            showResetButton: true,
            showSaveButton: true,
            autoApply: false,
            position: 'top', // top, bottom, sidebar
            ...options
        };
        
        this.filters = new Map();
        this.activeFilters = {};
        this.savedFilters = {};
        this.filterCallbacks = [];
        this.filterHistory = [];
        
        this.init();
    }

    init() {
        if (!this.container) {
            console.warn(`Container ${this.containerId} not found`);
            return;
        }
        
        this.loadSavedFilters();
        this.createFilterInterface();
        this.setupEventListeners();
    }

    /**
     * Créer l'interface de filtres
     */
    createFilterInterface() {
        const filterPanel = document.createElement('div');
        filterPanel.className = 'advanced-filters-panel';
        filterPanel.innerHTML = `
            <div class="filters-header">
                <h4 class="filters-title">
                    <i class="fas fa-filter"></i>
                    Filtres avancés
                </h4>
                <div class="filters-actions">
                    <button class="filter-btn filter-btn-secondary" id="${this.containerId}-toggle-filters">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </div>
            </div>
            <div class="filters-content" id="${this.containerId}-filters-content">
                <div class="filters-grid" id="${this.containerId}-filters-grid"></div>
                <div class="filters-footer">
                    ${this.options.showResetButton ? `
                        <button class="filter-btn filter-btn-outline" id="${this.containerId}-reset-filters">
                            <i class="fas fa-undo"></i>
                            Réinitialiser
                        </button>
                    ` : ''}
                    ${this.options.showSaveButton ? `
                        <button class="filter-btn filter-btn-outline" id="${this.containerId}-save-filters">
                            <i class="fas fa-bookmark"></i>
                            Sauvegarder
                        </button>
                    ` : ''}
                    <button class="filter-btn filter-btn-primary" id="${this.containerId}-apply-filters">
                        <i class="fas fa-check"></i>
                        Appliquer
                    </button>
                </div>
            </div>
        `;
        
        this.container.appendChild(filterPanel);
        
        // Références aux éléments
        this.filtersContent = document.getElementById(`${this.containerId}-filters-content`);
        this.filtersGrid = document.getElementById(`${this.containerId}-filters-grid`);
    }

    /**
     * Configuration des événements
     */
    setupEventListeners() {
        // Toggle filters panel
        const toggleBtn = document.getElementById(`${this.containerId}-toggle-filters`);
        if (toggleBtn) {
            toggleBtn.addEventListener('click', this.toggleFiltersPanel.bind(this));
        }

        // Reset filters
        const resetBtn = document.getElementById(`${this.containerId}-reset-filters`);
        if (resetBtn) {
            resetBtn.addEventListener('click', this.resetFilters.bind(this));
        }

        // Save filters
        const saveBtn = document.getElementById(`${this.containerId}-save-filters`);
        if (saveBtn) {
            saveBtn.addEventListener('click', this.showSaveFiltersModal.bind(this));
        }

        // Apply filters
        const applyBtn = document.getElementById(`${this.containerId}-apply-filters`);
        if (applyBtn) {
            applyBtn.addEventListener('click', this.applyFilters.bind(this));
        }
    }

    /**
     * Ajouter un filtre
     */
    addFilter(filterConfig) {
        const {
            id,
            label,
            type, // select, multiselect, range, date, daterange, text, checkbox
            options = [],
            defaultValue = null,
            placeholder = '',
            min = null,
            max = null,
            step = 1
        } = filterConfig;

        this.filters.set(id, {
            ...filterConfig,
            value: defaultValue
        });

        this.renderFilter(filterConfig);
    }

    /**
     * Rendre un filtre
     */
    renderFilter(filterConfig) {
        const { id, label, type, options, placeholder, min, max, step } = filterConfig;
        
        const filterItem = document.createElement('div');
        filterItem.className = 'filter-item';
        filterItem.dataset.filterId = id;

        let filterHTML = `
            <label class="filter-label" for="${id}">${label}</label>
            <div class="filter-control">
        `;

        switch (type) {
            case 'select':
                filterHTML += `
                    <select class="filter-select" id="${id}" data-filter-type="${type}">
                        <option value="">${placeholder || 'Sélectionner...'}</option>
                        ${options.map(option => `
                            <option value="${option.value}">${option.label}</option>
                        `).join('')}
                    </select>
                `;
                break;

            case 'multiselect':
                filterHTML += `
                    <div class="filter-multiselect" id="${id}" data-filter-type="${type}">
                        <div class="multiselect-trigger">
                            <span class="multiselect-placeholder">${placeholder || 'Sélectionner...'}</span>
                            <i class="fas fa-chevron-down"></i>
                        </div>
                        <div class="multiselect-dropdown">
                            ${options.map(option => `
                                <label class="multiselect-option">
                                    <input type="checkbox" value="${option.value}">
                                    <span>${option.label}</span>
                                </label>
                            `).join('')}
                        </div>
                    </div>
                `;
                break;

            case 'range':
                filterHTML += `
                    <div class="filter-range" data-filter-type="${type}">
                        <input type="number" id="${id}-min" placeholder="Min" min="${min}" max="${max}" step="${step}">
                        <span class="range-separator">-</span>
                        <input type="number" id="${id}-max" placeholder="Max" min="${min}" max="${max}" step="${step}">
                    </div>
                `;
                break;

            case 'date':
                filterHTML += `
                    <input type="date" class="filter-date" id="${id}" data-filter-type="${type}">
                `;
                break;

            case 'daterange':
                filterHTML += `
                    <div class="filter-daterange" data-filter-type="${type}">
                        <input type="date" id="${id}-start" placeholder="Date début">
                        <span class="range-separator">-</span>
                        <input type="date" id="${id}-end" placeholder="Date fin">
                    </div>
                `;
                break;

            case 'text':
                filterHTML += `
                    <input type="text" class="filter-text" id="${id}" placeholder="${placeholder}" data-filter-type="${type}">
                `;
                break;

            case 'checkbox':
                filterHTML += `
                    <label class="filter-checkbox" for="${id}">
                        <input type="checkbox" id="${id}" data-filter-type="${type}">
                        <span class="checkbox-mark"></span>
                        <span class="checkbox-label">${placeholder}</span>
                    </label>
                `;
                break;
        }

        filterHTML += `
            </div>
        `;

        filterItem.innerHTML = filterHTML;
        this.filtersGrid.appendChild(filterItem);

        // Ajouter les événements pour ce filtre
        this.setupFilterEvents(id, type);
    }

    /**
     * Configuration des événements pour un filtre spécifique
     */
    setupFilterEvents(filterId, filterType) {
        const filterElement = document.getElementById(filterId);
        if (!filterElement) return;

        switch (filterType) {
            case 'select':
            case 'date':
            case 'text':
            case 'checkbox':
                filterElement.addEventListener('change', () => {
                    this.updateFilterValue(filterId, filterElement.value, filterType);
                });
                break;

            case 'multiselect':
                this.setupMultiselectEvents(filterId);
                break;

            case 'range':
                const minInput = document.getElementById(`${filterId}-min`);
                const maxInput = document.getElementById(`${filterId}-max`);
                if (minInput && maxInput) {
                    [minInput, maxInput].forEach(input => {
                        input.addEventListener('change', () => {
                            this.updateRangeFilter(filterId);
                        });
                    });
                }
                break;

            case 'daterange':
                const startInput = document.getElementById(`${filterId}-start`);
                const endInput = document.getElementById(`${filterId}-end`);
                if (startInput && endInput) {
                    [startInput, endInput].forEach(input => {
                        input.addEventListener('change', () => {
                            this.updateDateRangeFilter(filterId);
                        });
                    });
                }
                break;
        }
    }

    /**
     * Configuration des événements multiselect
     */
    setupMultiselectEvents(filterId) {
        const multiselect = document.getElementById(filterId);
        const trigger = multiselect.querySelector('.multiselect-trigger');
        const dropdown = multiselect.querySelector('.multiselect-dropdown');
        const checkboxes = multiselect.querySelectorAll('input[type="checkbox"]');

        // Toggle dropdown
        trigger.addEventListener('click', () => {
            dropdown.classList.toggle('active');
        });

        // Close dropdown on outside click
        document.addEventListener('click', (e) => {
            if (!multiselect.contains(e.target)) {
                dropdown.classList.remove('active');
            }
        });

        // Handle checkbox changes
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateMultiselectFilter(filterId);
            });
        });
    }

    /**
     * Mettre à jour la valeur d'un filtre
     */
    updateFilterValue(filterId, value, type) {
        const filter = this.filters.get(filterId);
        if (!filter) return;

        filter.value = type === 'checkbox' ? document.getElementById(filterId).checked : value;
        
        if (this.options.autoApply) {
            this.applyFilters();
        }
    }

    /**
     * Mettre à jour un filtre de plage
     */
    updateRangeFilter(filterId) {
        const minInput = document.getElementById(`${filterId}-min`);
        const maxInput = document.getElementById(`${filterId}-max`);
        const filter = this.filters.get(filterId);
        
        if (!filter || !minInput || !maxInput) return;

        filter.value = {
            min: minInput.value ? parseFloat(minInput.value) : null,
            max: maxInput.value ? parseFloat(maxInput.value) : null
        };

        if (this.options.autoApply) {
            this.applyFilters();
        }
    }

    /**
     * Mettre à jour un filtre de plage de dates
     */
    updateDateRangeFilter(filterId) {
        const startInput = document.getElementById(`${filterId}-start`);
        const endInput = document.getElementById(`${filterId}-end`);
        const filter = this.filters.get(filterId);
        
        if (!filter || !startInput || !endInput) return;

        filter.value = {
            start: startInput.value || null,
            end: endInput.value || null
        };

        if (this.options.autoApply) {
            this.applyFilters();
        }
    }

    /**
     * Mettre à jour un filtre multiselect
     */
    updateMultiselectFilter(filterId) {
        const multiselect = document.getElementById(filterId);
        const checkboxes = multiselect.querySelectorAll('input[type="checkbox"]:checked');
        const trigger = multiselect.querySelector('.multiselect-placeholder');
        const filter = this.filters.get(filterId);
        
        if (!filter) return;

        const selectedValues = Array.from(checkboxes).map(cb => cb.value);
        filter.value = selectedValues;

        // Update placeholder text
        if (selectedValues.length === 0) {
            trigger.textContent = filter.placeholder || 'Sélectionner...';
        } else if (selectedValues.length === 1) {
            const option = filter.options.find(opt => opt.value === selectedValues[0]);
            trigger.textContent = option ? option.label : selectedValues[0];
        } else {
            trigger.textContent = `${selectedValues.length} sélectionnés`;
        }

        if (this.options.autoApply) {
            this.applyFilters();
        }
    }

    /**
     * Basculer le panneau de filtres
     */
    toggleFiltersPanel() {
        const icon = document.querySelector(`#${this.containerId}-toggle-filters i`);
        this.filtersContent.classList.toggle('collapsed');
        
        if (this.filtersContent.classList.contains('collapsed')) {
            icon.className = 'fas fa-chevron-right';
        } else {
            icon.className = 'fas fa-chevron-down';
        }
    }

    /**
     * Réinitialiser tous les filtres
     */
    resetFilters() {
        for (const [filterId, filter] of this.filters) {
            this.resetFilter(filterId, filter);
        }
        
        this.activeFilters = {};
        this.applyFilters();
    }

    /**
     * Réinitialiser un filtre spécifique
     */
    resetFilter(filterId, filter) {
        const element = document.getElementById(filterId);
        if (!element) return;

        switch (filter.type) {
            case 'select':
            case 'date':
            case 'text':
                element.value = filter.defaultValue || '';
                break;

            case 'checkbox':
                element.checked = filter.defaultValue || false;
                break;

            case 'multiselect':
                const checkboxes = element.querySelectorAll('input[type="checkbox"]');
                checkboxes.forEach(cb => cb.checked = false);
                this.updateMultiselectFilter(filterId);
                break;

            case 'range':
                document.getElementById(`${filterId}-min`).value = '';
                document.getElementById(`${filterId}-max`).value = '';
                break;

            case 'daterange':
                document.getElementById(`${filterId}-start`).value = '';
                document.getElementById(`${filterId}-end`).value = '';
                break;
        }

        filter.value = filter.defaultValue;
    }

    /**
     * Appliquer les filtres
     */
    applyFilters() {
        this.activeFilters = {};
        
        // Collecter les valeurs actives
        for (const [filterId, filter] of this.filters) {
            if (this.hasFilterValue(filter)) {
                this.activeFilters[filterId] = filter.value;
            }
        }

        // Exécuter les callbacks
        this.filterCallbacks.forEach(callback => {
            callback(this.activeFilters);
        });

        // Ajouter à l'historique
        this.addToHistory(this.activeFilters);

        // Événement personnalisé
        document.dispatchEvent(new CustomEvent('filtersApplied', {
            detail: {
                containerId: this.containerId,
                filters: this.activeFilters
            }
        }));
    }

    /**
     * Vérifier si un filtre a une valeur
     */
    hasFilterValue(filter) {
        if (filter.value === null || filter.value === undefined || filter.value === '') {
            return false;
        }

        if (Array.isArray(filter.value)) {
            return filter.value.length > 0;
        }

        if (typeof filter.value === 'object') {
            return Object.values(filter.value).some(v => v !== null && v !== undefined && v !== '');
        }

        return true;
    }

    /**
     * Ajouter un callback de filtre
     */
    onFilterChange(callback) {
        this.filterCallbacks.push(callback);
    }

    /**
     * Sauvegarder les filtres
     */
    showSaveFiltersModal() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Sauvegarder les filtres</h3>
                    <button class="modal-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label for="filter-name">Nom du filtre</label>
                        <input type="text" id="filter-name" placeholder="Mon filtre personnalisé">
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary modal-cancel">Annuler</button>
                    <button class="btn btn-primary modal-save">Sauvegarder</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Events
        modal.querySelector('.modal-close').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.querySelector('.modal-cancel').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.querySelector('.modal-save').addEventListener('click', () => {
            const name = modal.querySelector('#filter-name').value.trim();
            if (name) {
                this.saveFilters(name);
                document.body.removeChild(modal);
            }
        });
    }

    /**
     * Sauvegarder les filtres avec un nom
     */
    saveFilters(name) {
        this.savedFilters[name] = { ...this.activeFilters };
        localStorage.setItem(`finagent_filters_${this.containerId}`, JSON.stringify(this.savedFilters));
    }

    /**
     * Charger les filtres sauvegardés
     */
    loadSavedFilters() {
        const saved = localStorage.getItem(`finagent_filters_${this.containerId}`);
        if (saved) {
            try {
                this.savedFilters = JSON.parse(saved);
            } catch (e) {
                this.savedFilters = {};
            }
        }
    }

    /**
     * Ajouter à l'historique
     */
    addToHistory(filters) {
        this.filterHistory.unshift({ ...filters, timestamp: Date.now() });
        this.filterHistory = this.filterHistory.slice(0, 10); // Garder les 10 derniers
    }

    /**
     * Obtenir les filtres actifs
     */
    getActiveFilters() {
        return { ...this.activeFilters };
    }

    /**
     * Définir les filtres
     */
    setFilters(filters) {
        for (const [filterId, value] of Object.entries(filters)) {
            const filter = this.filters.get(filterId);
            if (filter) {
                filter.value = value;
                this.setFilterValue(filterId, value, filter.type);
            }
        }
        
        this.applyFilters();
    }

    /**
     * Définir la valeur d'un filtre dans l'interface
     */
    setFilterValue(filterId, value, type) {
        const element = document.getElementById(filterId);
        if (!element) return;

        switch (type) {
            case 'select':
            case 'date':
            case 'text':
                element.value = value;
                break;

            case 'checkbox':
                element.checked = value;
                break;

            case 'multiselect':
                const checkboxes = element.querySelectorAll('input[type="checkbox"]');
                checkboxes.forEach(cb => {
                    cb.checked = Array.isArray(value) && value.includes(cb.value);
                });
                this.updateMultiselectFilter(filterId);
                break;

            case 'range':
                if (value && typeof value === 'object') {
                    const minInput = document.getElementById(`${filterId}-min`);
                    const maxInput = document.getElementById(`${filterId}-max`);
                    if (minInput) minInput.value = value.min || '';
                    if (maxInput) maxInput.value = value.max || '';
                }
                break;

            case 'daterange':
                if (value && typeof value === 'object') {
                    const startInput = document.getElementById(`${filterId}-start`);
                    const endInput = document.getElementById(`${filterId}-end`);
                    if (startInput) startInput.value = value.start || '';
                    if (endInput) endInput.value = value.end || '';
                }
                break;
        }
    }
}

// Export pour usage dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdvancedFilters;
}