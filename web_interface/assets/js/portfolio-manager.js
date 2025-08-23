/**
 * Portfolio Management System
 * Système complet de gestion de portefeuille
 */

class PortfolioManager {
    constructor() {
        this.portfolios = new Map();
        this.currentPortfolio = null;
        this.positions = new Map();
        this.transactions = new Map();
        this.settings = {
            currency: 'USD',
            defaultCommission: 0.01, // 1%
            riskFreeRate: 0.02, // 2%
            updateInterval: 30000 // 30 secondes
        };
        this.charts = new Map();
        this.updateTimer = null;
        this.init();
    }

    /**
     * Initialisation du gestionnaire de portefeuille
     */
    init() {
        this.setupPortfolioInterface();
        this.bindEvents();
        this.loadSampleData();
        this.startRealTimeUpdates();
    }

    /**
     * Configuration de l'interface de portefeuille
     */
    setupPortfolioInterface() {
        const portfolioContainer = document.getElementById('portfolio-content');
        if (!portfolioContainer) return;

        portfolioContainer.innerHTML = `
            <div class="portfolio-layout">
                <!-- Portfolio Header -->
                <div class="portfolio-header">
                    <div class="portfolio-selector">
                        <select id="portfolio-select" class="form-select">
                            <option value="">Sélectionner un portefeuille...</option>
                        </select>
                        <button class="btn btn-primary" id="create-portfolio">
                            <i class="fas fa-plus"></i> Nouveau Portefeuille
                        </button>
                    </div>
                    <div class="portfolio-actions">
                        <button class="btn btn-outline" id="import-portfolio">
                            <i class="fas fa-upload"></i> Importer
                        </button>
                        <button class="btn btn-outline" id="export-portfolio">
                            <i class="fas fa-download"></i> Exporter
                        </button>
                        <button class="btn btn-outline" id="portfolio-settings">
                            <i class="fas fa-cog"></i> Paramètres
                        </button>
                    </div>
                </div>

                <!-- Portfolio Overview -->
                <div class="portfolio-overview" id="portfolio-overview">
                    <!-- Overview content will be loaded here -->
                </div>

                <!-- Portfolio Tabs -->
                <div class="portfolio-tabs">
                    <div class="tabs-nav">
                        <button class="tab-btn active" data-tab="positions">
                            <i class="fas fa-list"></i> Positions
                        </button>
                        <button class="tab-btn" data-tab="transactions">
                            <i class="fas fa-exchange-alt"></i> Transactions
                        </button>
                        <button class="tab-btn" data-tab="performance">
                            <i class="fas fa-chart-line"></i> Performance
                        </button>
                        <button class="tab-btn" data-tab="allocation">
                            <i class="fas fa-pie-chart"></i> Allocation
                        </button>
                        <button class="tab-btn" data-tab="analysis">
                            <i class="fas fa-calculator"></i> Analyse
                        </button>
                    </div>
                    <div class="tabs-content">
                        <div class="tab-pane active" id="positions-tab">
                            <!-- Positions content -->
                        </div>
                        <div class="tab-pane" id="transactions-tab">
                            <!-- Transactions content -->
                        </div>
                        <div class="tab-pane" id="performance-tab">
                            <!-- Performance content -->
                        </div>
                        <div class="tab-pane" id="allocation-tab">
                            <!-- Allocation content -->
                        </div>
                        <div class="tab-pane" id="analysis-tab">
                            <!-- Analysis content -->
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.setupTabs();
        this.setupPositionsTable();
        this.setupTransactionsTable();
        this.setupPerformanceCharts();
        this.setupAllocationChart();
        this.setupAnalysisTools();
    }

    /**
     * Configuration des onglets
     */
    setupTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabPanes = document.querySelectorAll('.tab-pane');

        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.dataset.tab;
                
                // Désactiver tous les onglets
                tabBtns.forEach(b => b.classList.remove('active'));
                tabPanes.forEach(p => p.classList.remove('active'));
                
                // Activer l'onglet sélectionné
                btn.classList.add('active');
                document.getElementById(`${targetTab}-tab`).classList.add('active');
                
                // Charger le contenu de l'onglet
                this.loadTabContent(targetTab);
            });
        });
    }

    /**
     * Configuration du tableau des positions
     */
    setupPositionsTable() {
        const positionsTab = document.getElementById('positions-tab');
        positionsTab.innerHTML = `
            <div class="positions-toolbar">
                <div class="toolbar-left">
                    <button class="btn btn-primary" id="add-position">
                        <i class="fas fa-plus"></i> Ajouter Position
                    </button>
                    <button class="btn btn-outline" id="rebalance-portfolio">
                        <i class="fas fa-balance-scale"></i> Rééquilibrer
                    </button>
                </div>
                <div class="toolbar-right">
                    <div class="search-box">
                        <input type="text" id="positions-search" placeholder="Rechercher..." class="form-control">
                        <i class="fas fa-search"></i>
                    </div>
                    <select id="positions-filter" class="form-select">
                        <option value="all">Toutes les positions</option>
                        <option value="profitable">Profitables</option>
                        <option value="losing">En perte</option>
                        <option value="large">Grandes positions (&gt;5%)</option>
                    </select>
                </div>
            </div>
            <div class="positions-table-container">
                <table class="positions-table" id="positions-table">
                    <thead>
                        <tr>
                            <th class="sortable" data-sort="symbol">
                                Symbole <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="quantity">
                                Quantité <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="averageCost">
                                Prix Moyen <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="currentPrice">
                                Prix Actuel <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="marketValue">
                                Valeur <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="weight">
                                Poids <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="pnl">
                                P&L <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="return">
                                Rendement <i class="fas fa-sort"></i>
                            </th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="positions-tbody">
                        <!-- Positions will be loaded here -->
                    </tbody>
                </table>
            </div>
            <div class="positions-summary" id="positions-summary">
                <!-- Summary will be loaded here -->
            </div>
        `;
    }

    /**
     * Configuration du tableau des transactions
     */
    setupTransactionsTable() {
        const transactionsTab = document.getElementById('transactions-tab');
        transactionsTab.innerHTML = `
            <div class="transactions-toolbar">
                <div class="toolbar-left">
                    <button class="btn btn-primary" id="add-transaction">
                        <i class="fas fa-plus"></i> Nouvelle Transaction
                    </button>
                    <button class="btn btn-outline" id="import-transactions">
                        <i class="fas fa-upload"></i> Importer
                    </button>
                </div>
                <div class="toolbar-right">
                    <div class="date-range-picker">
                        <input type="date" id="transactions-start-date" class="form-control">
                        <span>à</span>
                        <input type="date" id="transactions-end-date" class="form-control">
                    </div>
                    <select id="transactions-filter" class="form-select">
                        <option value="all">Toutes</option>
                        <option value="buy">Achats</option>
                        <option value="sell">Ventes</option>
                        <option value="dividend">Dividendes</option>
                    </select>
                </div>
            </div>
            <div class="transactions-table-container">
                <table class="transactions-table" id="transactions-table">
                    <thead>
                        <tr>
                            <th class="sortable" data-sort="date">
                                Date <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="symbol">
                                Symbole <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="type">
                                Type <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="quantity">
                                Quantité <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="price">
                                Prix <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="amount">
                                Montant <i class="fas fa-sort"></i>
                            </th>
                            <th class="sortable" data-sort="fees">
                                Frais <i class="fas fa-sort"></i>
                            </th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="transactions-tbody">
                        <!-- Transactions will be loaded here -->
                    </tbody>
                </table>
            </div>
        `;
    }

    /**
     * Configuration des graphiques de performance
     */
    setupPerformanceCharts() {
        const performanceTab = document.getElementById('performance-tab');
        performanceTab.innerHTML = `
            <div class="performance-layout">
                <div class="performance-metrics">
                    <div class="metric-card">
                        <div class="metric-label">Rendement Total</div>
                        <div class="metric-value" id="total-return">-</div>
                        <div class="metric-change" id="total-return-change">-</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Rendement Annualisé</div>
                        <div class="metric-value" id="annualized-return">-</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Volatilité</div>
                        <div class="metric-value" id="volatility">-</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Ratio de Sharpe</div>
                        <div class="metric-value" id="sharpe-ratio">-</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Drawdown Max</div>
                        <div class="metric-value" id="max-drawdown">-</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Beta</div>
                        <div class="metric-value" id="beta">-</div>
                    </div>
                </div>
                <div class="performance-charts">
                    <div class="chart-container">
                        <div class="chart-header">
                            <h3>Évolution de la Valeur du Portefeuille</h3>
                            <div class="chart-controls">
                                <div class="btn-group">
                                    <button class="btn btn-sm btn-outline active" data-period="1M">1M</button>
                                    <button class="btn btn-sm btn-outline" data-period="3M">3M</button>
                                    <button class="btn btn-sm btn-outline" data-period="6M">6M</button>
                                    <button class="btn btn-sm btn-outline" data-period="1Y">1A</button>
                                    <button class="btn btn-sm btn-outline" data-period="ALL">Tout</button>
                                </div>
                            </div>
                        </div>
                        <canvas id="portfolio-value-chart" class="chart-canvas"></canvas>
                    </div>
                    <div class="chart-container">
                        <div class="chart-header">
                            <h3>Drawdown du Portefeuille</h3>
                        </div>
                        <canvas id="drawdown-chart" class="chart-canvas"></canvas>
                    </div>
                </div>
                <div class="performance-comparison">
                    <div class="chart-container">
                        <div class="chart-header">
                            <h3>Comparaison avec Benchmarks</h3>
                            <select id="benchmark-select" class="form-select">
                                <option value="SPY">S&P 500 (SPY)</option>
                                <option value="QQQ">NASDAQ (QQQ)</option>
                                <option value="VTI">Total Stock Market (VTI)</option>
                                <option value="CUSTOM">Benchmark Personnalisé</option>
                            </select>
                        </div>
                        <canvas id="benchmark-comparison-chart" class="chart-canvas"></canvas>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Configuration du graphique d'allocation
     */
    setupAllocationChart() {
        const allocationTab = document.getElementById('allocation-tab');
        allocationTab.innerHTML = `
            <div class="allocation-layout">
                <div class="allocation-overview">
                    <div class="allocation-section">
                        <h3>Allocation Actuelle</h3>
                        <div class="allocation-chart-container">
                            <canvas id="current-allocation-chart"></canvas>
                        </div>
                    </div>
                    <div class="allocation-section">
                        <h3>Allocation Cible</h3>
                        <div class="allocation-chart-container">
                            <canvas id="target-allocation-chart"></canvas>
                        </div>
                        <button class="btn btn-primary" id="set-target-allocation">
                            <i class="fas fa-target"></i> Définir Allocation Cible
                        </button>
                    </div>
                </div>
                <div class="allocation-details">
                    <div class="allocation-tabs">
                        <button class="allocation-tab-btn active" data-view="securities">Titres</button>
                        <button class="allocation-tab-btn" data-view="sectors">Secteurs</button>
                        <button class="allocation-tab-btn" data-view="geography">Géographie</button>
                        <button class="allocation-tab-btn" data-view="asset-class">Classes d'Actifs</button>
                    </div>
                    <div class="allocation-content" id="allocation-details-content">
                        <!-- Allocation details will be loaded here -->
                    </div>
                </div>
                <div class="rebalancing-recommendations" id="rebalancing-recommendations">
                    <!-- Rebalancing recommendations will be loaded here -->
                </div>
            </div>
        `;
    }

    /**
     * Configuration des outils d'analyse
     */
    setupAnalysisTools() {
        const analysisTab = document.getElementById('analysis-tab');
        analysisTab.innerHTML = `
            <div class="analysis-layout">
                <div class="analysis-tools">
                    <div class="tool-section">
                        <h3>Analyse de Risque</h3>
                        <div class="tool-grid">
                            <button class="tool-btn" id="var-analysis">
                                <i class="fas fa-exclamation-triangle"></i>
                                <span>Value at Risk</span>
                            </button>
                            <button class="tool-btn" id="correlation-analysis">
                                <i class="fas fa-project-diagram"></i>
                                <span>Matrice de Corrélation</span>
                            </button>
                            <button class="tool-btn" id="stress-test">
                                <i class="fas fa-dumbbell"></i>
                                <span>Test de Stress</span>
                            </button>
                            <button class="tool-btn" id="monte-carlo">
                                <i class="fas fa-dice"></i>
                                <span>Simulation Monte Carlo</span>
                            </button>
                        </div>
                    </div>
                    <div class="tool-section">
                        <h3>Optimisation</h3>
                        <div class="tool-grid">
                            <button class="tool-btn" id="efficient-frontier">
                                <i class="fas fa-chart-area"></i>
                                <span>Frontière Efficiente</span>
                            </button>
                            <button class="tool-btn" id="portfolio-optimizer">
                                <i class="fas fa-magic"></i>
                                <span>Optimiseur de Portefeuille</span>
                            </button>
                            <button class="tool-btn" id="factor-analysis">
                                <i class="fas fa-microscope"></i>
                                <span>Analyse Factorielle</span>
                            </button>
                            <button class="tool-btn" id="scenario-analysis">
                                <i class="fas fa-theater-masks"></i>
                                <span>Analyse de Scénarios</span>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="analysis-results" id="analysis-results">
                    <!-- Analysis results will be displayed here -->
                </div>
            </div>
        `;
    }

    /**
     * Liaison des événements
     */
    bindEvents() {
        // Portfolio selector
        document.getElementById('portfolio-select')?.addEventListener('change', (e) => {
            if (e.target.value) {
                this.loadPortfolio(e.target.value);
            }
        });

        // Create portfolio
        document.getElementById('create-portfolio')?.addEventListener('click', () => {
            this.showCreatePortfolioModal();
        });

        // Add position
        document.getElementById('add-position')?.addEventListener('click', () => {
            this.showAddPositionModal();
        });

        // Add transaction
        document.getElementById('add-transaction')?.addEventListener('click', () => {
            this.showAddTransactionModal();
        });

        // Positions search and filter
        document.getElementById('positions-search')?.addEventListener('input', (e) => {
            this.filterPositions(e.target.value);
        });

        document.getElementById('positions-filter')?.addEventListener('change', (e) => {
            this.filterPositions(null, e.target.value);
        });

        // Transactions filter
        document.getElementById('transactions-filter')?.addEventListener('change', (e) => {
            this.filterTransactions(e.target.value);
        });

        // Performance period buttons
        document.querySelectorAll('[data-period]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('[data-period]').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.updatePerformanceChart(e.target.dataset.period);
            });
        });

        // Analysis tools
        document.getElementById('var-analysis')?.addEventListener('click', () => {
            this.performVaRAnalysis();
        });

        document.getElementById('correlation-analysis')?.addEventListener('click', () => {
            this.showCorrelationMatrix();
        });

        // Sorting
        document.querySelectorAll('.sortable').forEach(header => {
            header.addEventListener('click', () => {
                this.sortTable(header.dataset.sort);
            });
        });
    }

    /**
     * Chargement de données d'exemple
     */
    loadSampleData() {
        // Créer un portefeuille d'exemple
        const samplePortfolio = {
            id: 'portfolio-1',
            name: 'Portfolio Principal',
            description: 'Portfolio diversifié d\'actions et ETF',
            totalValue: 125000,
            cashBalance: 15000,
            investedAmount: 110000,
            availableCash: 15000,
            totalPnL: 12500,
            unrealizedPnL: 8000,
            realizedPnL: 4500,
            createdAt: '2024-01-01',
            positions: [
                {
                    symbol: 'AAPL',
                    quantity: 50,
                    averageCost: 180.50,
                    currentPrice: 195.20,
                    marketValue: 9760,
                    weight: 7.8,
                    pnl: 735,
                    sector: 'Technology',
                    industry: 'Consumer Electronics'
                },
                {
                    symbol: 'MSFT',
                    quantity: 30,
                    averageCost: 340.00,
                    currentPrice: 365.80,
                    marketValue: 10974,
                    weight: 8.8,
                    pnl: 774,
                    sector: 'Technology',
                    industry: 'Software'
                },
                {
                    symbol: 'GOOGL',
                    quantity: 15,
                    averageCost: 145.20,
                    currentPrice: 152.30,
                    marketValue: 2284.50,
                    weight: 1.8,
                    pnl: 106.50,
                    sector: 'Technology',
                    industry: 'Internet Services'
                },
                {
                    symbol: 'SPY',
                    quantity: 100,
                    averageCost: 420.00,
                    currentPrice: 445.60,
                    marketValue: 44560,
                    weight: 35.6,
                    pnl: 2560,
                    sector: 'ETF',
                    industry: 'Broad Market ETF'
                },
                {
                    symbol: 'QQQ',
                    quantity: 80,
                    averageCost: 380.00,
                    currentPrice: 395.25,
                    marketValue: 31620,
                    weight: 25.3,
                    pnl: 1220,
                    sector: 'ETF',
                    industry: 'Technology ETF'
                }
            ],
            transactions: [
                {
                    id: 'tx-1',
                    date: '2024-01-15',
                    symbol: 'AAPL',
                    type: 'BUY',
                    quantity: 50,
                    price: 180.50,
                    amount: 9025,
                    fees: 10,
                    status: 'EXECUTED'
                },
                {
                    id: 'tx-2',
                    date: '2024-01-20',
                    symbol: 'MSFT',
                    type: 'BUY',
                    quantity: 30,
                    price: 340.00,
                    amount: 10200,
                    fees: 12,
                    status: 'EXECUTED'
                },
                {
                    id: 'tx-3',
                    date: '2024-02-01',
                    symbol: 'SPY',
                    type: 'BUY',
                    quantity: 100,
                    price: 420.00,
                    amount: 42000,
                    fees: 20,
                    status: 'EXECUTED'
                }
            ]
        };

        this.portfolios.set(samplePortfolio.id, samplePortfolio);
        this.updatePortfolioSelector();
        
        // Charger le premier portefeuille
        this.loadPortfolio(samplePortfolio.id);
    }

    /**
     * Mise à jour du sélecteur de portefeuille
     */
    updatePortfolioSelector() {
        const selector = document.getElementById('portfolio-select');
        if (!selector) return;

        // Vider les options existantes
        selector.innerHTML = '<option value="">Sélectionner un portefeuille...</option>';

        // Ajouter les portefeuilles
        this.portfolios.forEach((portfolio, id) => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = portfolio.name;
            selector.appendChild(option);
        });
    }

    /**
     * Chargement d'un portefeuille
     */
    loadPortfolio(portfolioId) {
        const portfolio = this.portfolios.get(portfolioId);
        if (!portfolio) return;

        this.currentPortfolio = portfolio;
        
        // Mettre à jour l'overview
        this.updatePortfolioOverview(portfolio);
        
        // Charger le contenu de l'onglet actif
        const activeTab = document.querySelector('.tab-btn.active');
        if (activeTab) {
            this.loadTabContent(activeTab.dataset.tab);
        }
    }

    /**
     * Mise à jour de l'aperçu du portefeuille
     */
    updatePortfolioOverview(portfolio) {
        const overviewContainer = document.getElementById('portfolio-overview');
        if (!overviewContainer) return;

        const totalReturn = ((portfolio.totalPnL / (portfolio.totalValue - portfolio.totalPnL)) * 100).toFixed(2);
        const dayChange = 1.24; // Simulation
        const dayChangePercent = 0.99;

        overviewContainer.innerHTML = `
            <div class="portfolio-summary">
                <div class="summary-card main-card">
                    <div class="card-header">
                        <h2>${portfolio.name}</h2>
                        <div class="portfolio-meta">
                            <span class="portfolio-id">ID: ${portfolio.id}</span>
                            <span class="last-update">Dernière mise à jour: ${new Date().toLocaleString('fr-FR')}</span>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="main-value">
                            <span class="currency">${this.settings.currency}</span>
                            <span class="amount">${this.formatNumber(portfolio.totalValue)}</span>
                        </div>
                        <div class="change-info">
                            <div class="daily-change ${dayChange >= 0 ? 'positive' : 'negative'}">
                                <i class="fas fa-${dayChange >= 0 ? 'arrow-up' : 'arrow-down'}"></i>
                                ${this.formatNumber(Math.abs(dayChange))} (${dayChangePercent.toFixed(2)}%)
                            </div>
                            <div class="total-return ${portfolio.totalPnL >= 0 ? 'positive' : 'negative'}">
                                Total: ${totalReturn}% (${this.formatNumber(portfolio.totalPnL)})
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="summary-cards-grid">
                    <div class="summary-card">
                        <div class="card-label">Investissements</div>
                        <div class="card-value">${this.formatNumber(portfolio.investedAmount)}</div>
                        <div class="card-percentage">${((portfolio.investedAmount / portfolio.totalValue) * 100).toFixed(1)}%</div>
                    </div>
                    <div class="summary-card">
                        <div class="card-label">Liquidités</div>
                        <div class="card-value">${this.formatNumber(portfolio.cashBalance)}</div>
                        <div class="card-percentage">${((portfolio.cashBalance / portfolio.totalValue) * 100).toFixed(1)}%</div>
                    </div>
                    <div class="summary-card">
                        <div class="card-label">P&L Non Réalisé</div>
                        <div class="card-value ${portfolio.unrealizedPnL >= 0 ? 'positive' : 'negative'}">
                            ${this.formatNumber(portfolio.unrealizedPnL)}
                        </div>
                    </div>
                    <div class="summary-card">
                        <div class="card-label">P&L Réalisé</div>
                        <div class="card-value ${portfolio.realizedPnL >= 0 ? 'positive' : 'negative'}">
                            ${this.formatNumber(portfolio.realizedPnL)}
                        </div>
                    </div>
                    <div class="summary-card">
                        <div class="card-label">Nombre de Positions</div>
                        <div class="card-value">${portfolio.positions.length}</div>
                    </div>
                    <div class="summary-card">
                        <div class="card-label">Plus Grande Position</div>
                        <div class="card-value">${this.getLargestPosition(portfolio).toFixed(1)}%</div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Chargement du contenu d'un onglet
     */
    loadTabContent(tabName) {
        switch (tabName) {
            case 'positions':
                this.loadPositionsData();
                break;
            case 'transactions':
                this.loadTransactionsData();
                break;
            case 'performance':
                this.loadPerformanceData();
                break;
            case 'allocation':
                this.loadAllocationData();
                break;
            case 'analysis':
                this.loadAnalysisData();
                break;
        }
    }

    /**
     * Chargement des données de positions
     */
    loadPositionsData() {
        if (!this.currentPortfolio) return;

        const tbody = document.getElementById('positions-tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        this.currentPortfolio.positions.forEach(position => {
            const returnPercent = ((position.pnl / (position.averageCost * position.quantity)) * 100).toFixed(2);
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="symbol-cell">
                        <strong>${position.symbol}</strong>
                        <small>${position.industry}</small>
                    </div>
                </td>
                <td>${this.formatNumber(position.quantity, 0)}</td>
                <td>${this.formatCurrency(position.averageCost)}</td>
                <td>${this.formatCurrency(position.currentPrice)}</td>
                <td>${this.formatCurrency(position.marketValue)}</td>
                <td>
                    <div class="weight-cell">
                        ${position.weight.toFixed(1)}%
                        <div class="weight-bar">
                            <div class="weight-fill" style="width: ${position.weight}%"></div>
                        </div>
                    </div>
                </td>
                <td class="${position.pnl >= 0 ? 'positive' : 'negative'}">
                    ${this.formatCurrency(position.pnl)}
                </td>
                <td class="${returnPercent >= 0 ? 'positive' : 'negative'}">
                    ${returnPercent}%
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-outline" onclick="portfolioManager.editPosition('${position.symbol}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline" onclick="portfolioManager.sellPosition('${position.symbol}')">
                            <i class="fas fa-minus"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="portfolioManager.closePosition('${position.symbol}')">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });

        this.updatePositionsSummary();
    }

    /**
     * Mise à jour du résumé des positions
     */
    updatePositionsSummary() {
        if (!this.currentPortfolio) return;

        const summary = document.getElementById('positions-summary');
        if (!summary) return;

        const totalPositions = this.currentPortfolio.positions.length;
        const profitablePositions = this.currentPortfolio.positions.filter(p => p.pnl > 0).length;
        const largePositions = this.currentPortfolio.positions.filter(p => p.weight > 5).length;

        summary.innerHTML = `
            <div class="summary-stats">
                <div class="stat-item">
                    <span class="stat-label">Positions Totales:</span>
                    <span class="stat-value">${totalPositions}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Positions Profitables:</span>
                    <span class="stat-value positive">${profitablePositions} (${((profitablePositions/totalPositions)*100).toFixed(0)}%)</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Grandes Positions (&gt;5%):</span>
                    <span class="stat-value">${largePositions}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Concentration Top 3:</span>
                    <span class="stat-value">${this.getTopConcentration(3).toFixed(1)}%</span>
                </div>
            </div>
        `;
    }

    /**
     * Chargement des données de transactions
     */
    loadTransactionsData() {
        if (!this.currentPortfolio) return;

        const tbody = document.getElementById('transactions-tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        // Trier les transactions par date (plus récentes en premier)
        const sortedTransactions = [...this.currentPortfolio.transactions].sort(
            (a, b) => new Date(b.date) - new Date(a.date)
        );

        sortedTransactions.forEach(transaction => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${new Date(transaction.date).toLocaleDateString('fr-FR')}</td>
                <td><strong>${transaction.symbol}</strong></td>
                <td>
                    <span class="transaction-type ${transaction.type.toLowerCase()}">
                        ${this.getTransactionTypeLabel(transaction.type)}
                    </span>
                </td>
                <td>${this.formatNumber(transaction.quantity, 0)}</td>
                <td>${this.formatCurrency(transaction.price)}</td>
                <td>${this.formatCurrency(transaction.amount)}</td>
                <td>${this.formatCurrency(transaction.fees)}</td>
                <td>
                    <span class="status ${transaction.status.toLowerCase()}">
                        ${this.getStatusLabel(transaction.status)}
                    </span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-outline" onclick="portfolioManager.editTransaction('${transaction.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="portfolioManager.deleteTransaction('${transaction.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    /**
     * Utilitaires de formatage
     */
    formatNumber(number, decimals = 2) {
        return new Intl.NumberFormat('fr-FR', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(number);
    }

    formatCurrency(amount, currency = this.settings.currency) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }

    getTransactionTypeLabel(type) {
        const labels = {
            'BUY': 'Achat',
            'SELL': 'Vente',
            'DIVIDEND': 'Dividende',
            'SPLIT': 'Split',
            'MERGER': 'Fusion',
            'SPIN_OFF': 'Spin-off'
        };
        return labels[type] || type;
    }

    getStatusLabel(status) {
        const labels = {
            'PENDING': 'En attente',
            'EXECUTED': 'Exécuté',
            'CANCELLED': 'Annulé',
            'FAILED': 'Échoué',
            'PARTIAL': 'Partiel'
        };
        return labels[status] || status;
    }

    getLargestPosition(portfolio) {
        if (!portfolio.positions.length) return 0;
        return Math.max(...portfolio.positions.map(p => p.weight));
    }

    getTopConcentration(topN) {
        if (!this.currentPortfolio) return 0;
        const sortedPositions = [...this.currentPortfolio.positions]
            .sort((a, b) => b.weight - a.weight)
            .slice(0, topN);
        return sortedPositions.reduce((sum, p) => sum + p.weight, 0);
    }

    /**
     * Démarrage des mises à jour en temps réel
     */
    startRealTimeUpdates() {
        this.updateTimer = setInterval(() => {
            if (this.currentPortfolio) {
                this.updateMarketPrices();
            }
        }, this.settings.updateInterval);
    }

    /**
     * Mise à jour des prix de marché (simulation)
     */
    updateMarketPrices() {
        if (!this.currentPortfolio) return;

        // Simulation de variations de prix
        this.currentPortfolio.positions.forEach(position => {
            const variation = (Math.random() - 0.5) * 0.02; // ±1%
            position.currentPrice *= (1 + variation);
            position.marketValue = position.quantity * position.currentPrice;
            position.pnl = position.marketValue - (position.quantity * position.averageCost);
        });

        // Recalculer les métriques du portefeuille
        this.recalculatePortfolioMetrics();

        // Mettre à jour l'affichage si on est sur l'onglet positions
        const activeTab = document.querySelector('.tab-btn.active');
        if (activeTab && activeTab.dataset.tab === 'positions') {
            this.loadPositionsData();
            this.updatePortfolioOverview(this.currentPortfolio);
        }
    }

    /**
     * Recalcul des métriques du portefeuille
     */
    recalculatePortfolioMetrics() {
        if (!this.currentPortfolio) return;

        const totalMarketValue = this.currentPortfolio.positions.reduce(
            (sum, p) => sum + p.marketValue, 0
        );

        this.currentPortfolio.investedAmount = totalMarketValue;
        this.currentPortfolio.totalValue = totalMarketValue + this.currentPortfolio.cashBalance;
        this.currentPortfolio.unrealizedPnL = this.currentPortfolio.positions.reduce(
            (sum, p) => sum + p.pnl, 0
        );
        this.currentPortfolio.totalPnL = this.currentPortfolio.unrealizedPnL + this.currentPortfolio.realizedPnL;

        // Recalculer les poids
        this.currentPortfolio.positions.forEach(position => {
            position.weight = (position.marketValue / this.currentPortfolio.totalValue) * 100;
        });
    }

    /**
     * Méthodes de modal (à implémenter)
     */
    showCreatePortfolioModal() {
        // TODO: Implémenter la modal de création de portefeuille
        console.log('Create portfolio modal');
    }

    showAddPositionModal() {
        // TODO: Implémenter la modal d'ajout de position
        console.log('Add position modal');
    }

    showAddTransactionModal() {
        // TODO: Implémenter la modal d'ajout de transaction
        console.log('Add transaction modal');
    }

    // Méthodes d'action sur les positions
    editPosition(symbol) {
        console.log('Edit position:', symbol);
    }

    sellPosition(symbol) {
        console.log('Sell position:', symbol);
    }

    closePosition(symbol) {
        console.log('Close position:', symbol);
    }

    // Méthodes d'action sur les transactions
    editTransaction(id) {
        console.log('Edit transaction:', id);
    }

    deleteTransaction(id) {
        console.log('Delete transaction:', id);
    }

    // Méthodes de filtrage et tri
    filterPositions(searchTerm, filterType = 'all') {
        // TODO: Implémenter le filtrage des positions
        console.log('Filter positions:', searchTerm, filterType);
    }

    filterTransactions(filterType) {
        // TODO: Implémenter le filtrage des transactions
        console.log('Filter transactions:', filterType);
    }

    sortTable(sortBy) {
        // TODO: Implémenter le tri des tableaux
        console.log('Sort table by:', sortBy);
    }

    // Méthodes d'analyse et de performance
    loadPerformanceData() {
        if (!this.currentPortfolio || !window.portfolioCharts) return;

        // Créer les graphiques de performance
        this.createPerformanceCharts();
        
        // Mettre à jour les métriques de performance
        this.updatePerformanceMetrics();
    }

    loadAllocationData() {
        if (!this.currentPortfolio || !window.portfolioCharts) return;

        // Créer les graphiques d'allocation
        this.createAllocationCharts();
        
        // Charger les détails d'allocation
        this.loadAllocationDetails();
        
        // Générer les recommandations de rééquilibrage
        this.generateRebalancingRecommendations();
    }

    loadAnalysisData() {
        if (!this.currentPortfolio) return;

        // Afficher les outils d'analyse disponibles
        this.displayAnalysisTools();
    }

    createPerformanceCharts() {
        // Graphique d'évolution de la valeur du portefeuille
        window.portfolioCharts.createPortfolioValueChart(
            'portfolio-value-chart',
            this.currentPortfolio,
            '1M'
        );
        
        // Graphique de drawdown
        window.portfolioCharts.createDrawdownChart(
            'drawdown-chart',
            '1M'
        );
        
        // Graphique de comparaison avec benchmark
        window.portfolioCharts.createBenchmarkComparisonChart(
            'benchmark-comparison-chart',
            'SPY',
            '1M'
        );
    }

    createAllocationCharts() {
        // Graphique d'allocation actuelle
        window.portfolioCharts.createCurrentAllocationChart(
            'current-allocation-chart',
            this.currentPortfolio.positions
        );
        
        // Graphique d'allocation cible (simulé)
        const targetAllocation = this.generateTargetAllocation();
        window.portfolioCharts.createTargetAllocationChart(
            'target-allocation-chart',
            targetAllocation
        );
    }

    updatePerformanceMetrics() {
        if (!this.currentPortfolio) return;

        const metrics = this.calculatePortfolioMetrics();
        
        // Mettre à jour les métriques affichées
        this.updateMetricDisplay('total-return', metrics.totalReturn, '%');
        this.updateMetricDisplay('annualized-return', metrics.annualizedReturn, '%');
        this.updateMetricDisplay('volatility', metrics.volatility, '%');
        this.updateMetricDisplay('sharpe-ratio', metrics.sharpeRatio, '');
        this.updateMetricDisplay('max-drawdown', metrics.maxDrawdown, '%');
        this.updateMetricDisplay('beta', metrics.beta, '');
    }

    calculatePortfolioMetrics() {
        if (!this.currentPortfolio) return {};

        const totalReturn = ((this.currentPortfolio.totalPnL /
            (this.currentPortfolio.totalValue - this.currentPortfolio.totalPnL)) * 100);
        
        // Métriques simulées (dans un vrai système, ces valeurs viendraient de calculs historiques)
        return {
            totalReturn: totalReturn.toFixed(2),
            annualizedReturn: (totalReturn * 1.2).toFixed(2), // Simulation
            volatility: (Math.random() * 10 + 5).toFixed(2), // 5-15%
            sharpeRatio: (Math.random() * 1.5 + 0.5).toFixed(2), // 0.5-2.0
            maxDrawdown: (-(Math.random() * 10 + 2)).toFixed(2), // -2% à -12%
            beta: (Math.random() * 0.4 + 0.8).toFixed(2) // 0.8-1.2
        };
    }

    updateMetricDisplay(elementId, value, suffix) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value + suffix;
            
            // Ajouter des classes pour la couleur selon la valeur
            if (elementId === 'total-return' || elementId === 'annualized-return') {
                element.className = parseFloat(value) >= 0 ? 'positive' : 'negative';
            }
        }
    }

    generateTargetAllocation() {
        // Allocation cible simulée basée sur les positions actuelles
        return this.currentPortfolio.positions.map(position => ({
            symbol: position.symbol,
            target: Math.random() * 30 + 5 // 5-35% par position
        })).sort((a, b) => b.target - a.target);
    }

    loadAllocationDetails() {
        const activeView = document.querySelector('.allocation-tab-btn.active');
        const view = activeView ? activeView.dataset.view : 'securities';
        
        this.displayAllocationDetails(view);
    }

    displayAllocationDetails(view) {
        const content = document.getElementById('allocation-details-content');
        if (!content) return;

        switch (view) {
            case 'securities':
                content.innerHTML = this.generateSecuritiesAllocationTable();
                break;
            case 'sectors':
                content.innerHTML = this.generateSectorsAllocationTable();
                break;
            case 'geography':
                content.innerHTML = this.generateGeographyAllocationTable();
                break;
            case 'asset-class':
                content.innerHTML = this.generateAssetClassAllocationTable();
                break;
        }
    }

    generateSecuritiesAllocationTable() {
        const positions = this.currentPortfolio.positions;
        
        let html = `
            <table class="allocation-table">
                <thead>
                    <tr>
                        <th>Titre</th>
                        <th>Allocation Actuelle</th>
                        <th>Allocation Cible</th>
                        <th>Écart</th>
                        <th>Valeur</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        positions.forEach(position => {
            const targetWeight = Math.random() * 30 + 5; // Simulation
            const difference = position.weight - targetWeight;
            
            html += `
                <tr>
                    <td>
                        <strong>${position.symbol}</strong>
                        <br><small>${position.industry}</small>
                    </td>
                    <td>${position.weight.toFixed(1)}%</td>
                    <td>${targetWeight.toFixed(1)}%</td>
                    <td class="${difference >= 0 ? 'positive' : 'negative'}">
                        ${difference >= 0 ? '+' : ''}${difference.toFixed(1)}%
                    </td>
                    <td>${this.formatCurrency(position.marketValue)}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
        return html;
    }

    generateSectorsAllocationTable() {
        const sectorAllocation = this.calculateSectorAllocation();
        
        let html = `
            <table class="allocation-table">
                <thead>
                    <tr>
                        <th>Secteur</th>
                        <th>Allocation</th>
                        <th>Nombre de Titres</th>
                        <th>Valeur</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        Object.entries(sectorAllocation).forEach(([sector, data]) => {
            html += `
                <tr>
                    <td><strong>${sector}</strong></td>
                    <td>${data.percentage.toFixed(1)}%</td>
                    <td>${data.count}</td>
                    <td>${this.formatCurrency(data.value)}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
        return html;
    }

    calculateSectorAllocation() {
        const sectorAllocation = {};
        
        this.currentPortfolio.positions.forEach(position => {
            const sector = position.sector || 'Autres';
            
            if (!sectorAllocation[sector]) {
                sectorAllocation[sector] = {
                    count: 0,
                    value: 0,
                    percentage: 0
                };
            }
            
            sectorAllocation[sector].count++;
            sectorAllocation[sector].value += position.marketValue;
        });
        
        // Calculer les pourcentages
        Object.keys(sectorAllocation).forEach(sector => {
            sectorAllocation[sector].percentage =
                (sectorAllocation[sector].value / this.currentPortfolio.investedAmount) * 100;
        });
        
        return sectorAllocation;
    }

    displayAnalysisTools() {
        // Les outils d'analyse sont déjà affichés dans le HTML
        // Cette méthode pourrait être utilisée pour activer/désactiver certains outils
        console.log('Analysis tools displayed');
    }

    performVaRAnalysis() {
        const resultsContainer = document.getElementById('analysis-results');
        if (!resultsContainer) return;

        const varResults = this.calculateVaR();
        
        resultsContainer.innerHTML = `
            <div class="analysis-result">
                <h3><i class="fas fa-exclamation-triangle"></i> Analyse Value at Risk (VaR)</h3>
                <div class="var-metrics">
                    <div class="var-item">
                        <label>VaR 1 jour (95%):</label>
                        <span class="var-value negative">${this.formatCurrency(varResults.var1d95)}</span>
                    </div>
                    <div class="var-item">
                        <label>VaR 1 jour (99%):</label>
                        <span class="var-value negative">${this.formatCurrency(varResults.var1d99)}</span>
                    </div>
                    <div class="var-item">
                        <label>VaR 10 jours (95%):</label>
                        <span class="var-value negative">${this.formatCurrency(varResults.var10d95)}</span>
                    </div>
                    <div class="var-item">
                        <label>Expected Shortfall (95%):</label>
                        <span class="var-value negative">${this.formatCurrency(varResults.expectedShortfall)}</span>
                    </div>
                </div>
                <div class="var-interpretation">
                    <h4>Interprétation:</h4>
                    <p>Il y a 95% de chances que les pertes ne dépassent pas ${this.formatCurrency(Math.abs(varResults.var1d95))} sur 1 jour.</p>
                    <p>Dans le pire cas (5% des scénarios), les pertes moyennes seraient de ${this.formatCurrency(Math.abs(varResults.expectedShortfall))}.</p>
                </div>
            </div>
        `;
    }

    calculateVaR() {
        // Simulation de calcul VaR (dans un vrai système, cela serait basé sur les données historiques)
        const portfolioValue = this.currentPortfolio.totalValue;
        const dailyVolatility = 0.015; // 1.5% de volatilité quotidienne
        
        return {
            var1d95: -portfolioValue * dailyVolatility * 1.645, // Z-score pour 95%
            var1d99: -portfolioValue * dailyVolatility * 2.326, // Z-score pour 99%
            var10d95: -portfolioValue * dailyVolatility * 1.645 * Math.sqrt(10), // VaR 10 jours
            expectedShortfall: -portfolioValue * dailyVolatility * 2.063 // Expected Shortfall approximatif
        };
    }

    showCorrelationMatrix() {
        const resultsContainer = document.getElementById('analysis-results');
        if (!resultsContainer || !window.portfolioCharts) return;

        resultsContainer.innerHTML = `
            <div class="analysis-result">
                <h3><i class="fas fa-project-diagram"></i> Matrice de Corrélation</h3>
                <div id="correlation-matrix-container"></div>
                <div class="correlation-legend">
                    <h4>Légende:</h4>
                    <div class="legend-items">
                        <div class="legend-item">
                            <span class="correlation-color correlation-high"></span>
                            Corrélation forte (≥ 0.7)
                        </div>
                        <div class="legend-item">
                            <span class="correlation-color correlation-medium"></span>
                            Corrélation modérée (0.3 - 0.7)
                        </div>
                        <div class="legend-item">
                            <span class="correlation-color correlation-low"></span>
                            Corrélation faible (-0.3 - 0.3)
                        </div>
                        <div class="legend-item">
                            <span class="correlation-color correlation-negative"></span>
                            Corrélation négative (< -0.3)
                        </div>
                    </div>
                </div>
            </div>
        `;

        window.portfolioCharts.createCorrelationMatrix(
            'correlation-matrix-container',
            this.currentPortfolio.positions
        );
    }

    updatePerformanceChart(period) {
        if (!window.portfolioCharts) return;

        // Mettre à jour le graphique de valeur du portefeuille
        window.portfolioCharts.createPortfolioValueChart(
            'portfolio-value-chart',
            this.currentPortfolio,
            period
        );
        
        // Mettre à jour le graphique de drawdown
        window.portfolioCharts.createDrawdownChart(
            'drawdown-chart',
            period
        );
        
        // Mettre à jour le graphique de comparaison avec benchmark
        const benchmarkSelect = document.getElementById('benchmark-select');
        const benchmark = benchmarkSelect ? benchmarkSelect.value : 'SPY';
        
        window.portfolioCharts.createBenchmarkComparisonChart(
            'benchmark-comparison-chart',
            benchmark,
            period
        );
    }
}

// Initialisation globale
let portfolioManager;

document.addEventListener('DOMContentLoaded', () => {
    portfolioManager = new PortfolioManager();
});