/**
 * Gestionnaire de recherche et filtrage
 * Système de recherche globale avancé avec filtres et suggestions
 */

class SearchManager {
    constructor() {
        this.searchInput = null;
        this.searchResults = null;
        this.searchOverlay = null;
        this.currentQuery = '';
        this.searchHistory = [];
        this.searchFilters = {};
        this.searchData = new Map();
        this.searchDebounceTimer = null;
        this.isSearchActive = false;
        
        this.init();
    }

    init() {
        this.setupSearchInterface();
        this.loadSearchData();
        this.setupEventListeners();
        this.loadSearchHistory();
    }

    /**
     * Configuration de l'interface de recherche
     */
    setupSearchInterface() {
        this.searchInput = document.querySelector('.search-input');
        
        if (!this.searchInput) {
            console.warn('Input de recherche non trouvé');
            return;
        }

        // Améliorer l'input de recherche existant
        this.enhanceSearchInput();
        
        // Créer l'overlay de résultats
        this.createSearchOverlay();
    }

    /**
     * Améliorer l'input de recherche existant
     */
    enhanceSearchInput() {
        // Ajouter des attributs pour l'amélioration
        this.searchInput.setAttribute('autocomplete', 'off');
        this.searchInput.setAttribute('spellcheck', 'false');
        this.searchInput.placeholder = 'Rechercher des actions, portefeuilles, actualités...';

        // Créer le conteneur de suggestions
        const searchContainer = this.searchInput.closest('.search-container');
        if (searchContainer) {
            const suggestionsContainer = document.createElement('div');
            suggestionsContainer.className = 'search-suggestions';
            suggestionsContainer.id = 'search-suggestions';
            searchContainer.appendChild(suggestionsContainer);
        }
    }

    /**
     * Créer l'overlay de résultats de recherche
     */
    createSearchOverlay() {
        this.searchOverlay = document.createElement('div');
        this.searchOverlay.className = 'search-overlay';
        this.searchOverlay.innerHTML = `
            <div class="search-modal">
                <div class="search-modal-header">
                    <div class="search-modal-input-container">
                        <i class="fas fa-search search-modal-icon"></i>
                        <input type="text" class="search-modal-input" placeholder="Recherche avancée...">
                        <button class="search-modal-close">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="search-filters">
                        <button class="search-filter active" data-category="all">
                            <i class="fas fa-globe"></i> Tout
                        </button>
                        <button class="search-filter" data-category="stocks">
                            <i class="fas fa-chart-line"></i> Actions
                        </button>
                        <button class="search-filter" data-category="portfolio">
                            <i class="fas fa-briefcase"></i> Portefeuille
                        </button>
                        <button class="search-filter" data-category="news">
                            <i class="fas fa-newspaper"></i> Actualités
                        </button>
                        <button class="search-filter" data-category="analysis">
                            <i class="fas fa-chart-bar"></i> Analyses
                        </button>
                    </div>
                </div>
                <div class="search-modal-body">
                    <div class="search-results-container">
                        <div class="search-results" id="search-results"></div>
                    </div>
                    <div class="search-sidebar">
                        <div class="search-history">
                            <h4><i class="fas fa-history"></i> Recherches récentes</h4>
                            <div class="search-history-list" id="search-history-list"></div>
                        </div>
                        <div class="search-shortcuts">
                            <h4><i class="fas fa-keyboard"></i> Raccourcis</h4>
                            <div class="shortcut-item">
                                <kbd>Ctrl</kbd> + <kbd>K</kbd> - Recherche rapide
                            </div>
                            <div class="shortcut-item">
                                <kbd>Échap</kbd> - Fermer
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.searchOverlay);
        
        // Références aux éléments de l'overlay
        this.searchModalInput = this.searchOverlay.querySelector('.search-modal-input');
        this.searchResults = this.searchOverlay.querySelector('#search-results');
    }

    /**
     * Configuration des événements
     */
    setupEventListeners() {
        // Recherche dans l'input principal
        if (this.searchInput) {
            this.searchInput.addEventListener('input', this.handleSearchInput.bind(this));
            this.searchInput.addEventListener('focus', this.handleSearchFocus.bind(this));
            this.searchInput.addEventListener('keydown', this.handleSearchKeydown.bind(this));
        }

        // Recherche dans l'overlay
        if (this.searchModalInput) {
            this.searchModalInput.addEventListener('input', this.handleModalSearchInput.bind(this));
            this.searchModalInput.addEventListener('keydown', this.handleModalKeydown.bind(this));
        }

        // Fermeture de l'overlay
        const closeButton = this.searchOverlay?.querySelector('.search-modal-close');
        if (closeButton) {
            closeButton.addEventListener('click', this.closeSearchModal.bind(this));
        }

        // Clic en dehors de l'overlay
        this.searchOverlay?.addEventListener('click', (e) => {
            if (e.target === this.searchOverlay) {
                this.closeSearchModal();
            }
        });

        // Filtres de catégorie
        const filters = this.searchOverlay?.querySelectorAll('.search-filter');
        filters?.forEach(filter => {
            filter.addEventListener('click', this.handleFilterClick.bind(this));
        });

        // Raccourcis clavier globaux
        document.addEventListener('keydown', this.handleGlobalKeydown.bind(this));

        // Clic sur les résultats
        this.searchResults?.addEventListener('click', this.handleResultClick.bind(this));
    }

    /**
     * Chargement des données de recherche
     */
    loadSearchData() {
        // Simulation de données de recherche
        this.searchData.set('stocks', [
            { id: 'AAPL', name: 'Apple Inc.', category: 'stocks', type: 'Action', price: '$175.43', change: '+1.2%' },
            { id: 'MSFT', name: 'Microsoft Corporation', category: 'stocks', type: 'Action', price: '$378.85', change: '+0.8%' },
            { id: 'GOOGL', name: 'Alphabet Inc.', category: 'stocks', type: 'Action', price: '$2,840.12', change: '-0.3%' },
            { id: 'TSLA', name: 'Tesla Inc.', category: 'stocks', type: 'Action', price: '$248.50', change: '+2.1%' },
            { id: 'AMZN', name: 'Amazon.com Inc.', category: 'stocks', type: 'Action', price: '$145.86', change: '+0.5%' }
        ]);

        this.searchData.set('portfolio', [
            { id: 'portfolio-1', name: 'Portefeuille Principal', category: 'portfolio', type: 'Portefeuille', value: '€125,847.32', performance: '+11.38%' },
            { id: 'portfolio-2', name: 'Portefeuille Croissance', category: 'portfolio', type: 'Portefeuille', value: '€48,392.15', performance: '+18.42%' },
            { id: 'portfolio-3', name: 'Portefeuille Dividendes', category: 'portfolio', type: 'Portefeuille', value: '€76,521.89', performance: '+6.73%' }
        ]);

        this.searchData.set('news', [
            { id: 'news-1', name: 'Fed maintient les taux directeurs', category: 'news', type: 'Actualité', date: '2024-01-15', source: 'Reuters' },
            { id: 'news-2', name: 'Apple dépasse les attentes trimestrielles', category: 'news', type: 'Actualité', date: '2024-01-14', source: 'Bloomberg' },
            { id: 'news-3', name: 'Tension géopolitique affecte les marchés', category: 'news', type: 'Actualité', date: '2024-01-13', source: 'Financial Times' }
        ]);

        this.searchData.set('analysis', [
            { id: 'analysis-1', name: 'Analyse technique AAPL', category: 'analysis', type: 'Analyse', indicator: 'RSI: 65.3', recommendation: 'Achat' },
            { id: 'analysis-2', name: 'Rapport sectoriel Tech', category: 'analysis', type: 'Rapport', date: '2024-01-15', rating: 'Surperformer' },
            { id: 'analysis-3', name: 'Stratégie allocation Q1', category: 'analysis', type: 'Stratégie', allocation: '60/40', risk: 'Modéré' }
        ]);
    }

    /**
     * Gestionnaire de saisie dans l'input principal
     */
    handleSearchInput(e) {
        const query = e.target.value.trim();
        
        if (query.length === 0) {
            this.clearSuggestions();
            return;
        }

        // Debounce pour éviter trop de requêtes
        clearTimeout(this.searchDebounceTimer);
        this.searchDebounceTimer = setTimeout(() => {
            this.showSuggestions(query);
        }, 300);
    }

    /**
     * Gestionnaire de focus sur l'input principal
     */
    handleSearchFocus(e) {
        if (e.target.value.trim().length > 0) {
            this.showSuggestions(e.target.value.trim());
        }
    }

    /**
     * Gestionnaire de touches sur l'input principal
     */
    handleSearchKeydown(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const query = e.target.value.trim();
            if (query) {
                this.performAdvancedSearch(query);
            }
        } else if (e.key === 'Escape') {
            this.clearSuggestions();
            e.target.blur();
        }
    }

    /**
     * Gestionnaire de saisie dans l'overlay
     */
    handleModalSearchInput(e) {
        const query = e.target.value.trim();
        this.currentQuery = query;
        
        clearTimeout(this.searchDebounceTimer);
        this.searchDebounceTimer = setTimeout(() => {
            this.performSearch(query);
        }, 200);
    }

    /**
     * Gestionnaire de touches dans l'overlay
     */
    handleModalKeydown(e) {
        if (e.key === 'Escape') {
            this.closeSearchModal();
        } else if (e.key === 'Enter') {
            e.preventDefault();
            // Sélectionner le premier résultat
            const firstResult = this.searchResults.querySelector('.search-result-item');
            if (firstResult) {
                firstResult.click();
            }
        }
    }

    /**
     * Gestionnaire de raccourcis clavier globaux
     */
    handleGlobalKeydown(e) {
        // Ctrl+K ou Cmd+K pour ouvrir la recherche
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            this.openSearchModal();
        }
        
        // Escape pour fermer la recherche
        if (e.key === 'Escape' && this.isSearchActive) {
            this.closeSearchModal();
        }
    }

    /**
     * Gestionnaire de clic sur les filtres
     */
    handleFilterClick(e) {
        const filter = e.currentTarget;
        const category = filter.dataset.category;
        
        // Mise à jour de l'état actif
        this.searchOverlay.querySelectorAll('.search-filter').forEach(f => {
            f.classList.remove('active');
        });
        filter.classList.add('active');
        
        // Mise à jour du filtre
        this.searchFilters.category = category;
        
        // Nouvelle recherche avec le filtre
        this.performSearch(this.currentQuery);
    }

    /**
     * Gestionnaire de clic sur les résultats
     */
    handleResultClick(e) {
        const resultItem = e.target.closest('.search-result-item');
        if (!resultItem) return;
        
        const resultId = resultItem.dataset.resultId;
        const category = resultItem.dataset.category;
        
        this.selectSearchResult(resultId, category);
        this.addToSearchHistory(this.currentQuery);
        this.closeSearchModal();
    }

    /**
     * Afficher les suggestions de recherche
     */
    showSuggestions(query) {
        const suggestions = this.generateSuggestions(query);
        const suggestionsContainer = document.getElementById('search-suggestions');
        
        if (!suggestionsContainer || suggestions.length === 0) {
            this.clearSuggestions();
            return;
        }

        suggestionsContainer.innerHTML = suggestions.map(suggestion => `
            <div class="search-suggestion" data-value="${suggestion.value}">
                <i class="${suggestion.icon}"></i>
                <span class="suggestion-text">${suggestion.text}</span>
                <span class="suggestion-category">${suggestion.category}</span>
            </div>
        `).join('');

        suggestionsContainer.classList.add('visible');

        // Gestionnaires pour les suggestions
        suggestionsContainer.querySelectorAll('.search-suggestion').forEach(suggestion => {
            suggestion.addEventListener('click', () => {
                this.searchInput.value = suggestion.dataset.value;
                this.performAdvancedSearch(suggestion.dataset.value);
                this.clearSuggestions();
            });
        });
    }

    /**
     * Générer les suggestions
     */
    generateSuggestions(query) {
        const suggestions = [];
        const lowercaseQuery = query.toLowerCase();

        // Rechercher dans toutes les catégories
        for (const [category, items] of this.searchData) {
            for (const item of items) {
                if (item.name.toLowerCase().includes(lowercaseQuery) || 
                    item.id.toLowerCase().includes(lowercaseQuery)) {
                    suggestions.push({
                        value: item.name,
                        text: item.name,
                        category: item.type,
                        icon: this.getCategoryIcon(category)
                    });
                }
            }
        }

        return suggestions.slice(0, 8); // Limiter à 8 suggestions
    }

    /**
     * Obtenir l'icône de catégorie
     */
    getCategoryIcon(category) {
        const icons = {
            stocks: 'fas fa-chart-line',
            portfolio: 'fas fa-briefcase',
            news: 'fas fa-newspaper',
            analysis: 'fas fa-chart-bar'
        };
        return icons[category] || 'fas fa-search';
    }

    /**
     * Nettoyer les suggestions
     */
    clearSuggestions() {
        const suggestionsContainer = document.getElementById('search-suggestions');
        if (suggestionsContainer) {
            suggestionsContainer.classList.remove('visible');
            suggestionsContainer.innerHTML = '';
        }
    }

    /**
     * Ouvrir la modal de recherche
     */
    openSearchModal() {
        this.searchOverlay.classList.add('active');
        this.isSearchActive = true;
        this.searchModalInput.focus();
        this.updateSearchHistory();
        document.body.style.overflow = 'hidden';
    }

    /**
     * Fermer la modal de recherche
     */
    closeSearchModal() {
        this.searchOverlay.classList.remove('active');
        this.isSearchActive = false;
        this.currentQuery = '';
        this.searchModalInput.value = '';
        this.searchResults.innerHTML = '';
        document.body.style.overflow = '';
    }

    /**
     * Effectuer une recherche avancée
     */
    performAdvancedSearch(query) {
        this.currentQuery = query;
        this.searchModalInput.value = query;
        this.openSearchModal();
        this.performSearch(query);
    }

    /**
     * Effectuer une recherche
     */
    performSearch(query) {
        if (!query.trim()) {
            this.searchResults.innerHTML = '<div class="no-results">Saisissez votre recherche...</div>';
            return;
        }

        const results = this.searchInData(query);
        this.displayResults(results, query);
    }

    /**
     * Rechercher dans les données
     */
    searchInData(query) {
        const results = [];
        const lowercaseQuery = query.toLowerCase();
        const activeCategory = this.searchFilters.category || 'all';

        for (const [category, items] of this.searchData) {
            if (activeCategory !== 'all' && category !== activeCategory) {
                continue;
            }

            for (const item of items) {
                let score = 0;
                
                // Calcul du score de pertinence
                if (item.name.toLowerCase().includes(lowercaseQuery)) {
                    score += item.name.toLowerCase().indexOf(lowercaseQuery) === 0 ? 10 : 5;
                }
                if (item.id.toLowerCase().includes(lowercaseQuery)) {
                    score += 3;
                }

                if (score > 0) {
                    results.push({ ...item, score });
                }
            }
        }

        // Trier par score de pertinence
        return results.sort((a, b) => b.score - a.score);
    }

    /**
     * Afficher les résultats
     */
    displayResults(results, query) {
        if (results.length === 0) {
            this.searchResults.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>Aucun résultat pour "<strong>${query}</strong>"</p>
                    <p>Essayez avec d'autres mots-clés</p>
                </div>
            `;
            return;
        }

        this.searchResults.innerHTML = `
            <div class="search-results-header">
                <span class="results-count">${results.length} résultat${results.length > 1 ? 's' : ''} pour "<strong>${query}</strong>"</span>
            </div>
            <div class="search-results-list">
                ${results.map(result => this.renderSearchResult(result)).join('')}
            </div>
        `;
    }

    /**
     * Rendre un résultat de recherche
     */
    renderSearchResult(result) {
        const icon = this.getCategoryIcon(result.category);
        
        return `
            <div class="search-result-item" data-result-id="${result.id}" data-category="${result.category}">
                <div class="result-icon">
                    <i class="${icon}"></i>
                </div>
                <div class="result-content">
                    <div class="result-title">${result.name}</div>
                    <div class="result-metadata">
                        ${this.renderResultMetadata(result)}
                    </div>
                </div>
                <div class="result-actions">
                    <i class="fas fa-arrow-right"></i>
                </div>
            </div>
        `;
    }

    /**
     * Rendre les métadonnées du résultat
     */
    renderResultMetadata(result) {
        switch (result.category) {
            case 'stocks':
                return `<span class="result-price">${result.price}</span><span class="result-change ${result.change.startsWith('+') ? 'positive' : 'negative'}">${result.change}</span>`;
            case 'portfolio':
                return `<span class="result-value">${result.value}</span><span class="result-performance ${result.performance.startsWith('+') ? 'positive' : 'negative'}">${result.performance}</span>`;
            case 'news':
                return `<span class="result-date">${result.date}</span><span class="result-source">${result.source}</span>`;
            case 'analysis':
                return `<span class="result-indicator">${result.indicator || result.rating || result.allocation}</span>`;
            default:
                return `<span class="result-type">${result.type}</span>`;
        }
    }

    /**
     * Sélectionner un résultat de recherche
     */
    selectSearchResult(resultId, category) {
        // Navigation vers la page/section appropriée
        switch (category) {
            case 'stocks':
                this.navigateToStock(resultId);
                break;
            case 'portfolio':
                this.navigateToPortfolio(resultId);
                break;
            case 'news':
                this.navigateToNews(resultId);
                break;
            case 'analysis':
                this.navigateToAnalysis(resultId);
                break;
        }
    }

    /**
     * Navigation vers une action
     */
    navigateToStock(stockId) {
        // Basculer vers la page Market et filtrer par l'action
        const marketTab = document.querySelector('[data-page="market"]');
        if (marketTab) {
            marketTab.click();
            // TODO: Filtrer par l'action spécifique
        }
        console.log('Naviguer vers l\'action:', stockId);
    }

    /**
     * Navigation vers un portefeuille
     */
    navigateToPortfolio(portfolioId) {
        const portfolioTab = document.querySelector('[data-page="portfolio"]');
        if (portfolioTab) {
            portfolioTab.click();
        }
        console.log('Naviguer vers le portefeuille:', portfolioId);
    }

    /**
     * Navigation vers une actualité
     */
    navigateToNews(newsId) {
        // TODO: Implémenter la navigation vers les actualités
        console.log('Naviguer vers l\'actualité:', newsId);
    }

    /**
     * Navigation vers une analyse
     */
    navigateToAnalysis(analysisId) {
        // TODO: Implémenter la navigation vers les analyses
        console.log('Naviguer vers l\'analyse:', analysisId);
    }

    /**
     * Ajouter à l'historique de recherche
     */
    addToSearchHistory(query) {
        if (!query.trim() || this.searchHistory.includes(query)) return;
        
        this.searchHistory.unshift(query);
        this.searchHistory = this.searchHistory.slice(0, 10); // Garder les 10 dernières
        this.saveSearchHistory();
    }

    /**
     * Charger l'historique de recherche
     */
    loadSearchHistory() {
        const saved = localStorage.getItem('finagent_search_history');
        if (saved) {
            try {
                this.searchHistory = JSON.parse(saved);
            } catch (e) {
                this.searchHistory = [];
            }
        }
    }

    /**
     * Sauvegarder l'historique de recherche
     */
    saveSearchHistory() {
        localStorage.setItem('finagent_search_history', JSON.stringify(this.searchHistory));
    }

    /**
     * Mettre à jour l'affichage de l'historique
     */
    updateSearchHistory() {
        const historyList = document.getElementById('search-history-list');
        if (!historyList) return;

        if (this.searchHistory.length === 0) {
            historyList.innerHTML = '<div class="no-history">Aucune recherche récente</div>';
            return;
        }

        historyList.innerHTML = this.searchHistory.map(query => `
            <div class="search-history-item" data-query="${query}">
                <i class="fas fa-history"></i>
                <span class="history-query">${query}</span>
                <button class="history-remove" data-query="${query}">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');

        // Gestionnaires pour l'historique
        historyList.querySelectorAll('.search-history-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.history-remove')) {
                    const query = e.target.closest('.history-remove').dataset.query;
                    this.removeFromSearchHistory(query);
                } else {
                    const query = item.dataset.query;
                    this.searchModalInput.value = query;
                    this.performSearch(query);
                }
            });
        });
    }

    /**
     * Supprimer de l'historique de recherche
     */
    removeFromSearchHistory(query) {
        this.searchHistory = this.searchHistory.filter(q => q !== query);
        this.saveSearchHistory();
        this.updateSearchHistory();
    }
}

// Initialiser le gestionnaire de recherche
document.addEventListener('DOMContentLoaded', () => {
    window.searchManager = new SearchManager();
});

// Exporter pour usage dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SearchManager;
}