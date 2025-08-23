/**
 * Intégration des filtres pour la page Market
 * Exemple d'utilisation du système de filtres avancés
 */

class MarketFilters {
    constructor() {
        this.filters = null;
        this.marketData = [];
        this.filteredData = [];
        
        this.init();
    }

    init() {
        this.setupFilters();
        this.loadMarketData();
        this.setupEventListeners();
    }

    /**
     * Configuration des filtres pour la page Market
     */
    setupFilters() {
        // Créer l'instance de filtres avancés
        this.filters = new AdvancedFilters('market-filters', {
            showResetButton: true,
            showSaveButton: true,
            autoApply: false,
            position: 'top'
        });

        // Ajouter les filtres spécifiques au marché
        this.addMarketFilters();

        // Écouter les changements de filtres
        this.filters.onFilterChange(this.handleFilterChange.bind(this));
    }

    /**
     * Ajouter les filtres spécifiques au marché
     */
    addMarketFilters() {
        // Filtre par secteur
        this.filters.addFilter({
            id: 'sector',
            label: 'Secteur',
            type: 'multiselect',
            placeholder: 'Sélectionner des secteurs',
            options: [
                { value: 'tech', label: 'Technologie' },
                { value: 'finance', label: 'Finance' },
                { value: 'healthcare', label: 'Santé' },
                { value: 'energy', label: 'Énergie' },
                { value: 'consumer', label: 'Consommation' },
                { value: 'industrial', label: 'Industrie' },
                { value: 'materials', label: 'Matériaux' },
                { value: 'utilities', label: 'Services publics' },
                { value: 'real_estate', label: 'Immobilier' },
                { value: 'telecom', label: 'Télécommunications' }
            ]
        });

        // Filtre par capitalisation boursière
        this.filters.addFilter({
            id: 'market_cap',
            label: 'Capitalisation boursière',
            type: 'select',
            placeholder: 'Toutes les capitalisations',
            options: [
                { value: 'mega', label: 'Mega Cap (>200B)' },
                { value: 'large', label: 'Large Cap (10B-200B)' },
                { value: 'mid', label: 'Mid Cap (2B-10B)' },
                { value: 'small', label: 'Small Cap (300M-2B)' },
                { value: 'micro', label: 'Micro Cap (<300M)' }
            ]
        });

        // Filtre par plage de prix
        this.filters.addFilter({
            id: 'price_range',
            label: 'Plage de prix ($)',
            type: 'range',
            min: 0,
            max: 1000,
            step: 1
        });

        // Filtre par variation
        this.filters.addFilter({
            id: 'change_range',
            label: 'Variation (%)',
            type: 'range',
            min: -50,
            max: 50,
            step: 0.1
        });

        // Filtre par volume
        this.filters.addFilter({
            id: 'volume_range',
            label: 'Volume minimum',
            type: 'select',
            placeholder: 'Tout volume',
            options: [
                { value: '1000000', label: '> 1M' },
                { value: '5000000', label: '> 5M' },
                { value: '10000000', label: '> 10M' },
                { value: '50000000', label: '> 50M' },
                { value: '100000000', label: '> 100M' }
            ]
        });

        // Filtre par dividende
        this.filters.addFilter({
            id: 'dividend',
            label: 'Dividende',
            type: 'checkbox',
            placeholder: 'Uniquement les actions à dividendes'
        });

        // Filtre par région
        this.filters.addFilter({
            id: 'region',
            label: 'Région',
            type: 'select',
            placeholder: 'Toutes les régions',
            options: [
                { value: 'us', label: 'États-Unis' },
                { value: 'eu', label: 'Europe' },
                { value: 'asia', label: 'Asie' },
                { value: 'emerging', label: 'Marchés émergents' }
            ]
        });

        // Filtre par indicateurs techniques
        this.filters.addFilter({
            id: 'technical',
            label: 'Signaux techniques',
            type: 'multiselect',
            placeholder: 'Sélectionner des signaux',
            options: [
                { value: 'rsi_oversold', label: 'RSI Survendu (<30)' },
                { value: 'rsi_overbought', label: 'RSI Suracheté (>70)' },
                { value: 'macd_bullish', label: 'MACD Haussier' },
                { value: 'macd_bearish', label: 'MACD Baissier' },
                { value: 'bollinger_squeeze', label: 'Bollinger Squeeze' },
                { value: 'breakout', label: 'Cassure de résistance' },
                { value: 'support', label: 'Rebond sur support' }
            ]
        });
    }

    /**
     * Charger les données de marché simulées
     */
    loadMarketData() {
        // Simulation de données de marché
        this.marketData = [
            {
                symbol: 'AAPL',
                name: 'Apple Inc.',
                price: 175.43,
                change: 1.2,
                volume: 52431000,
                marketCap: 'mega',
                sector: 'tech',
                region: 'us',
                dividend: true,
                technical: ['macd_bullish']
            },
            {
                symbol: 'MSFT',
                name: 'Microsoft Corporation',
                price: 378.85,
                change: 0.8,
                volume: 28945000,
                marketCap: 'mega',
                sector: 'tech',
                region: 'us',
                dividend: true,
                technical: ['rsi_overbought']
            },
            {
                symbol: 'GOOGL',
                name: 'Alphabet Inc.',
                price: 2840.12,
                change: -0.3,
                volume: 15642000,
                marketCap: 'mega',
                sector: 'tech',
                region: 'us',
                dividend: false,
                technical: ['bollinger_squeeze']
            },
            {
                symbol: 'TSLA',
                name: 'Tesla Inc.',
                price: 248.50,
                change: 2.1,
                volume: 89532000,
                marketCap: 'large',
                sector: 'consumer',
                region: 'us',
                dividend: false,
                technical: ['breakout', 'macd_bullish']
            },
            {
                symbol: 'JPM',
                name: 'JPMorgan Chase & Co.',
                price: 145.86,
                change: 0.5,
                volume: 12847000,
                marketCap: 'large',
                sector: 'finance',
                region: 'us',
                dividend: true,
                technical: ['support']
            },
            {
                symbol: 'NVDA',
                name: 'NVIDIA Corporation',
                price: 491.32,
                change: 3.8,
                volume: 67823000,
                marketCap: 'mega',
                sector: 'tech',
                region: 'us',
                dividend: false,
                technical: ['rsi_overbought', 'breakout']
            }
        ];

        this.filteredData = [...this.marketData];
        this.renderMarketData();
    }

    /**
     * Gestionnaire des changements de filtres
     */
    handleFilterChange(activeFilters) {
        console.log('Filtres actifs:', activeFilters);
        this.applyFilters(activeFilters);
        this.renderMarketData();
        this.updateFilterStats(activeFilters);
    }

    /**
     * Appliquer les filtres aux données
     */
    applyFilters(filters) {
        this.filteredData = this.marketData.filter(stock => {
            // Filtre par secteur
            if (filters.sector && filters.sector.length > 0) {
                if (!filters.sector.includes(stock.sector)) {
                    return false;
                }
            }

            // Filtre par capitalisation boursière
            if (filters.market_cap) {
                if (stock.marketCap !== filters.market_cap) {
                    return false;
                }
            }

            // Filtre par plage de prix
            if (filters.price_range) {
                const { min, max } = filters.price_range;
                if ((min !== null && stock.price < min) || 
                    (max !== null && stock.price > max)) {
                    return false;
                }
            }

            // Filtre par variation
            if (filters.change_range) {
                const { min, max } = filters.change_range;
                if ((min !== null && stock.change < min) || 
                    (max !== null && stock.change > max)) {
                    return false;
                }
            }

            // Filtre par volume
            if (filters.volume_range) {
                const minVolume = parseInt(filters.volume_range);
                if (stock.volume < minVolume) {
                    return false;
                }
            }

            // Filtre par dividende
            if (filters.dividend) {
                if (!stock.dividend) {
                    return false;
                }
            }

            // Filtre par région
            if (filters.region) {
                if (stock.region !== filters.region) {
                    return false;
                }
            }

            // Filtre par indicateurs techniques
            if (filters.technical && filters.technical.length > 0) {
                const hasSignal = filters.technical.some(signal => 
                    stock.technical.includes(signal)
                );
                if (!hasSignal) {
                    return false;
                }
            }

            return true;
        });
    }

    /**
     * Rendre les données de marché filtrées
     */
    renderMarketData() {
        const container = document.getElementById('market-data-table');
        if (!container) return;

        if (this.filteredData.length === 0) {
            container.innerHTML = `
                <div class="no-results-message">
                    <i class="fas fa-filter"></i>
                    <h3>Aucun résultat trouvé</h3>
                    <p>Essayez d'ajuster vos filtres pour voir plus de résultats</p>
                </div>
            `;
            return;
        }

        const tableHTML = `
            <div class="market-table-container">
                <table class="market-table">
                    <thead>
                        <tr>
                            <th>Symbole</th>
                            <th>Nom</th>
                            <th>Prix</th>
                            <th>Variation</th>
                            <th>Volume</th>
                            <th>Secteur</th>
                            <th>Signaux</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.filteredData.map(stock => `
                            <tr class="market-row" data-symbol="${stock.symbol}">
                                <td class="symbol-cell">
                                    <strong>${stock.symbol}</strong>
                                </td>
                                <td class="name-cell">${stock.name}</td>
                                <td class="price-cell">$${stock.price.toFixed(2)}</td>
                                <td class="change-cell ${stock.change >= 0 ? 'positive' : 'negative'}">
                                    ${stock.change >= 0 ? '+' : ''}${stock.change.toFixed(2)}%
                                </td>
                                <td class="volume-cell">${this.formatVolume(stock.volume)}</td>
                                <td class="sector-cell">
                                    <span class="sector-badge sector-${stock.sector}">${this.getSectorLabel(stock.sector)}</span>
                                </td>
                                <td class="signals-cell">
                                    ${stock.technical.map(signal => `
                                        <span class="technical-signal signal-${signal}">${this.getSignalLabel(signal)}</span>
                                    `).join('')}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = tableHTML;
    }

    /**
     * Mettre à jour les statistiques des filtres
     */
    updateFilterStats(filters) {
        const statsContainer = document.getElementById('filter-stats');
        if (!statsContainer) return;

        const activeFilterCount = Object.keys(filters).length;
        const resultCount = this.filteredData.length;
        const totalCount = this.marketData.length;

        statsContainer.innerHTML = `
            <div class="filter-stats-content">
                <span class="results-count">
                    ${resultCount} résultat${resultCount > 1 ? 's' : ''} sur ${totalCount}
                </span>
                ${activeFilterCount > 0 ? `
                    <span class="active-filters-count">
                        ${activeFilterCount} filtre${activeFilterCount > 1 ? 's' : ''} actif${activeFilterCount > 1 ? 's' : ''}
                    </span>
                ` : ''}
            </div>
        `;
    }

    /**
     * Formatage du volume
     */
    formatVolume(volume) {
        if (volume >= 1000000) {
            return (volume / 1000000).toFixed(1) + 'M';
        } else if (volume >= 1000) {
            return (volume / 1000).toFixed(1) + 'K';
        }
        return volume.toString();
    }

    /**
     * Obtenir le libellé du secteur
     */
    getSectorLabel(sector) {
        const labels = {
            tech: 'Tech',
            finance: 'Finance',
            healthcare: 'Santé',
            energy: 'Énergie',
            consumer: 'Consommation',
            industrial: 'Industrie',
            materials: 'Matériaux',
            utilities: 'Services publics',
            real_estate: 'Immobilier',
            telecom: 'Télécommunications'
        };
        return labels[sector] || sector;
    }

    /**
     * Obtenir le libellé du signal technique
     */
    getSignalLabel(signal) {
        const labels = {
            rsi_oversold: 'RSI-',
            rsi_overbought: 'RSI+',
            macd_bullish: 'MACD↑',
            macd_bearish: 'MACD↓',
            bollinger_squeeze: 'BB Squeeze',
            breakout: 'Breakout',
            support: 'Support'
        };
        return labels[signal] || signal;
    }

    /**
     * Configuration des événements
     */
    setupEventListeners() {
        // Écouter les changements de filtres globaux
        document.addEventListener('filtersApplied', (e) => {
            if (e.detail.containerId === 'market-filters') {
                console.log('Filtres market appliqués:', e.detail.filters);
            }
        });

        // Gérer les clics sur les lignes du tableau
        document.addEventListener('click', (e) => {
            const row = e.target.closest('.market-row');
            if (row) {
                const symbol = row.dataset.symbol;
                this.showStockDetails(symbol);
            }
        });
    }

    /**
     * Afficher les détails d'une action
     */
    showStockDetails(symbol) {
        const stock = this.marketData.find(s => s.symbol === symbol);
        if (stock) {
            console.log('Afficher les détails pour:', stock);
            // TODO: Implémenter la modal de détails
        }
    }

    /**
     * Exporter les données filtrées
     */
    exportFilteredData(format = 'csv') {
        const data = this.filteredData;
        if (format === 'csv') {
            this.exportToCSV(data);
        } else if (format === 'json') {
            this.exportToJSON(data);
        }
    }

    /**
     * Exporter en CSV
     */
    exportToCSV(data) {
        const headers = ['Symbol', 'Name', 'Price', 'Change', 'Volume', 'Sector'];
        const csvContent = [
            headers.join(','),
            ...data.map(stock => [
                stock.symbol,
                `"${stock.name}"`,
                stock.price,
                stock.change,
                stock.volume,
                stock.sector
            ].join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'market-data-filtered.csv';
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Exporter en JSON
     */
    exportToJSON(data) {
        const jsonContent = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonContent], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'market-data-filtered.json';
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Initialiser les filtres de marché quand la page Market est active
document.addEventListener('DOMContentLoaded', () => {
    // Attendre que la page Market soit chargée
    const marketPage = document.getElementById('market-page');
    if (marketPage) {
        window.marketFilters = new MarketFilters();
    }
});

// Export pour usage dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MarketFilters;
}