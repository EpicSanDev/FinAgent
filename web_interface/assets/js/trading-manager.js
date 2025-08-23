/**
 * Trading Manager - Système de gestion des ordres et du trading
 * Gère l'interface de trading, les ordres, les positions et l'exécution
 */

class TradingManager {
    constructor() {
        this.symbols = new Map();
        this.orderBook = new Map();
        this.currentSymbol = 'AAPL';
        this.currentOrderType = 'market';
        this.currentSide = 'buy';
        this.priceUpdateInterval = null;
        this.charts = new Map();
        this.webSocket = null;
        
        this.init();
    }

    /**
     * Initialisation du gestionnaire de trading
     */
    init() {
        this.initializeSymbols();
        this.setupEventListeners();
        this.initializeCharts();
        this.loadInitialData();
        this.startRealTimeUpdates();
        console.log('Trading Manager initialisé');
    }

    /**
     * Initialisation des symboles disponibles
     */
    initializeSymbols() {
        // Données de test pour les symboles
        const symbolData = [
            { symbol: 'AAPL', name: 'Apple Inc.', price: 175.43, change: 2.15, changePercent: 1.24 },
            { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 2847.35, change: -12.45, changePercent: -0.43 },
            { symbol: 'MSFT', name: 'Microsoft Corp.', price: 338.52, change: 5.78, changePercent: 1.74 },
            { symbol: 'TSLA', name: 'Tesla Inc.', price: 248.91, change: -8.32, changePercent: -3.24 },
            { symbol: 'AMZN', name: 'Amazon.com Inc.', price: 3384.16, change: 15.67, changePercent: 0.47 },
            { symbol: 'NVDA', name: 'NVIDIA Corp.', price: 465.78, change: 12.34, changePercent: 2.72 },
            { symbol: 'META', name: 'Meta Platforms Inc.', price: 284.39, change: -3.21, changePercent: -1.12 },
            { symbol: 'BTC-USD', name: 'Bitcoin USD', price: 43250.78, change: 1250.34, changePercent: 2.98 },
            { symbol: 'ETH-USD', name: 'Ethereum USD', price: 2654.32, change: -45.67, changePercent: -1.69 }
        ];

        symbolData.forEach(data => {
            this.symbols.set(data.symbol, {
                ...data,
                bid: data.price - 0.01,
                ask: data.price + 0.01,
                volume: Math.floor(Math.random() * 10000000) + 1000000
            });
        });
    }

    /**
     * Configuration des écouteurs d'événements
     */
    setupEventListeners() {
        // Navigation entre les types d'ordres
        document.querySelectorAll('.order-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchOrderType(e.target.dataset.type);
            });
        });

        // Basculement Buy/Sell
        document.querySelectorAll('input[name="orderSide"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentSide = e.target.value;
                this.updateOrderSummary();
            });
        });

        // Recherche de symboles
        const symbolInput = document.getElementById('symbolInput');
        if (symbolInput) {
            symbolInput.addEventListener('input', (e) => {
                this.handleSymbolSearch(e.target.value);
            });
            symbolInput.addEventListener('blur', () => {
                setTimeout(() => this.hideSymbolSuggestions(), 200);
            });
        }

        // Bouton de recherche de symboles
        const searchBtn = document.getElementById('symbolSearchBtn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                this.searchSymbol();
            });
        }

        // Inputs de quantité et prix
        const quantityInput = document.getElementById('quantityInput');
        if (quantityInput) {
            quantityInput.addEventListener('input', () => {
                this.updateOrderSummary();
            });
        }

        const priceInput = document.getElementById('priceInput');
        if (priceInput) {
            priceInput.addEventListener('input', () => {
                this.updateOrderSummary();
            });
        }

        // Boutons d'aide à la quantité
        document.querySelectorAll('.qty-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setQuantityPercentage(e.target.textContent);
            });
        });

        // Boutons d'action d'ordre
        const previewBtn = document.getElementById('previewOrderBtn');
        if (previewBtn) {
            previewBtn.addEventListener('click', () => {
                this.previewOrder();
            });
        }

        const submitBtn = document.getElementById('submitOrderBtn');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                this.submitOrder();
            });
        }

        // Navigation entre les tableaux
        document.querySelectorAll('.table-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTable(e.target.dataset.table);
            });
        });

        // Contrôles de timeframe
        document.querySelectorAll('.timeframe-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTimeframe(e.target.dataset.timeframe);
            });
        });

        // Plein écran pour les graphiques
        document.querySelectorAll('.chart-fullscreen').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.toggleChartFullscreen(e.target.closest('.chart-container'));
            });
        });
    }

    /**
     * Basculement entre les types d'ordres
     */
    switchOrderType(type) {
        this.currentOrderType = type;
        
        // Mise à jour des onglets
        document.querySelectorAll('.order-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.type === type);
        });

        // Affichage/masquage des champs selon le type
        this.updateOrderFields();
        this.updateOrderSummary();
    }

    /**
     * Mise à jour des champs d'ordre selon le type
     */
    updateOrderFields() {
        const priceField = document.getElementById('priceField');
        const stopPriceField = document.getElementById('stopPriceField');
        const timeInForceField = document.getElementById('timeInForceField');

        if (priceField) {
            priceField.style.display = this.currentOrderType === 'market' ? 'none' : 'block';
        }

        if (stopPriceField) {
            stopPriceField.style.display = 
                (this.currentOrderType === 'stop' || this.currentOrderType === 'stop-limit') ? 'block' : 'none';
        }

        if (timeInForceField) {
            timeInForceField.style.display = this.currentOrderType !== 'market' ? 'block' : 'none';
        }
    }

    /**
     * Gestion de la recherche de symboles
     */
    handleSymbolSearch(query) {
        if (query.length < 1) {
            this.hideSymbolSuggestions();
            return;
        }

        const suggestions = Array.from(this.symbols.values())
            .filter(symbol => 
                symbol.symbol.toLowerCase().includes(query.toLowerCase()) ||
                symbol.name.toLowerCase().includes(query.toLowerCase())
            )
            .slice(0, 10);

        this.showSymbolSuggestions(suggestions);
    }

    /**
     * Affichage des suggestions de symboles
     */
    showSymbolSuggestions(suggestions) {
        const container = document.getElementById('symbolSuggestions');
        if (!container) return;

        container.innerHTML = '';
        
        suggestions.forEach(symbol => {
            const suggestion = document.createElement('div');
            suggestion.className = 'symbol-suggestion';
            suggestion.innerHTML = `
                <div>
                    <div class="suggestion-symbol">${symbol.symbol}</div>
                    <div class="suggestion-name">${symbol.name}</div>
                </div>
                <div class="suggestion-price">${this.formatCurrency(symbol.price)}</div>
            `;
            
            suggestion.addEventListener('click', () => {
                this.selectSymbol(symbol.symbol);
            });
            
            container.appendChild(suggestion);
        });

        container.style.display = suggestions.length > 0 ? 'block' : 'none';
    }

    /**
     * Masquage des suggestions de symboles
     */
    hideSymbolSuggestions() {
        const container = document.getElementById('symbolSuggestions');
        if (container) {
            container.style.display = 'none';
        }
    }

    /**
     * Sélection d'un symbole
     */
    selectSymbol(symbol) {
        this.currentSymbol = symbol;
        
        const symbolInput = document.getElementById('symbolInput');
        if (symbolInput) {
            symbolInput.value = symbol;
        }

        this.hideSymbolSuggestions();
        this.updateCurrentPrice();
        this.updateChart();
        this.updateOrderBook();
    }

    /**
     * Mise à jour du prix actuel affiché
     */
    updateCurrentPrice() {
        const symbolData = this.symbols.get(this.currentSymbol);
        if (!symbolData) return;

        const priceDisplay = document.getElementById('currentPriceDisplay');
        if (priceDisplay) {
            priceDisplay.innerHTML = `
                <div class="price-info">
                    <span class="symbol-name">${symbolData.symbol}</span>
                    <span class="current-price">${this.formatCurrency(symbolData.price)}</span>
                </div>
                <div class="price-change ${symbolData.change >= 0 ? 'positive' : 'negative'}">
                    ${symbolData.change >= 0 ? '+' : ''}${this.formatCurrency(symbolData.change)} 
                    (${symbolData.changePercent >= 0 ? '+' : ''}${symbolData.changePercent.toFixed(2)}%)
                </div>
                <div class="bid-ask">
                    <span>Bid: ${this.formatCurrency(symbolData.bid)}</span>
                    <span>Ask: ${this.formatCurrency(symbolData.ask)}</span>
                </div>
            `;
        }
    }

    /**
     * Définition de la quantité par pourcentage
     */
    setQuantityPercentage(percentage) {
        const availableBalance = 10000; // Balance fictive
        const symbolData = this.symbols.get(this.currentSymbol);
        if (!symbolData) return;

        const percent = parseFloat(percentage.replace('%', '')) / 100;
        const maxShares = Math.floor(availableBalance * percent / symbolData.price);

        const quantityInput = document.getElementById('quantityInput');
        if (quantityInput) {
            quantityInput.value = maxShares;
            this.updateOrderSummary();
        }
    }

    /**
     * Mise à jour du résumé d'ordre
     */
    updateOrderSummary() {
        const symbolData = this.symbols.get(this.currentSymbol);
        if (!symbolData) return;

        const quantity = parseFloat(document.getElementById('quantityInput')?.value || 0);
        const price = this.currentOrderType === 'market' ? 
            (this.currentSide === 'buy' ? symbolData.ask : symbolData.bid) :
            parseFloat(document.getElementById('priceInput')?.value || symbolData.price);

        const total = quantity * price;
        const commission = total * 0.001; // 0.1% de commission
        const totalWithFees = total + commission;

        const summaryContainer = document.getElementById('orderSummary');
        if (summaryContainer) {
            summaryContainer.innerHTML = `
                <div class="summary-row">
                    <span>Quantité:</span>
                    <span>${quantity.toLocaleString()} actions</span>
                </div>
                <div class="summary-row">
                    <span>Prix ${this.currentOrderType === 'market' ? '(estimé)' : ''}:</span>
                    <span>${this.formatCurrency(price)}</span>
                </div>
                <div class="summary-row">
                    <span>Sous-total:</span>
                    <span>${this.formatCurrency(total)}</span>
                </div>
                <div class="summary-row">
                    <span>Commission:</span>
                    <span>${this.formatCurrency(commission)}</span>
                </div>
                <div class="summary-row total">
                    <span>Total:</span>
                    <span>${this.formatCurrency(totalWithFees)}</span>
                </div>
            `;
        }
    }

    /**
     * Prévisualisation d'un ordre
     */
    previewOrder() {
        const orderData = this.getOrderData();
        
        // Affichage de la modal de prévisualisation
        this.showOrderPreview(orderData);
    }

    /**
     * Soumission d'un ordre
     */
    submitOrder() {
        const orderData = this.getOrderData();
        
        // Validation de l'ordre
        if (!this.validateOrder(orderData)) {
            return;
        }

        // Simulation de soumission d'ordre
        this.executeOrder(orderData);
    }

    /**
     * Récupération des données d'ordre
     */
    getOrderData() {
        const symbolData = this.symbols.get(this.currentSymbol);
        const quantity = parseFloat(document.getElementById('quantityInput')?.value || 0);
        const price = this.currentOrderType === 'market' ? 
            (this.currentSide === 'buy' ? symbolData.ask : symbolData.bid) :
            parseFloat(document.getElementById('priceInput')?.value || symbolData.price);

        return {
            symbol: this.currentSymbol,
            side: this.currentSide,
            type: this.currentOrderType,
            quantity: quantity,
            price: price,
            stopPrice: parseFloat(document.getElementById('stopPriceInput')?.value || 0),
            timeInForce: document.getElementById('timeInForce')?.value || 'DAY',
            timestamp: new Date()
        };
    }

    /**
     * Validation d'un ordre
     */
    validateOrder(orderData) {
        if (!orderData.symbol || !this.symbols.has(orderData.symbol)) {
            this.showNotification('Symbole invalide', 'error');
            return false;
        }

        if (orderData.quantity <= 0) {
            this.showNotification('La quantité doit être positive', 'error');
            return false;
        }

        if (orderData.type !== 'market' && orderData.price <= 0) {
            this.showNotification('Le prix doit être positif', 'error');
            return false;
        }

        return true;
    }

    /**
     * Exécution d'un ordre
     */
    executeOrder(orderData) {
        // Génération d'un ID d'ordre
        const orderId = 'ORD-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        
        // Simulation du statut d'ordre
        const order = {
            ...orderData,
            id: orderId,
            status: orderData.type === 'market' ? 'filled' : 'pending',
            filledQuantity: orderData.type === 'market' ? orderData.quantity : 0,
            remainingQuantity: orderData.type === 'market' ? 0 : orderData.quantity,
            avgPrice: orderData.price,
            commission: orderData.quantity * orderData.price * 0.001
        };

        // Ajout à la liste des ordres
        this.addOrderToTable(order);
        
        // Si l'ordre est rempli, mise à jour du portefeuille
        if (order.status === 'filled') {
            this.updatePortfolio(order);
        }

        // Notification
        this.showNotification(
            `Ordre ${order.status === 'filled' ? 'exécuté' : 'soumis'} avec succès`,
            'success'
        );

        // Réinitialisation du formulaire
        this.resetOrderForm();
    }

    /**
     * Ajout d'un ordre au tableau
     */
    addOrderToTable(order) {
        const tableBody = document.querySelector('#openOrdersTable tbody');
        if (!tableBody) return;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <div class="symbol-cell">
                    <div class="symbol">${order.symbol}</div>
                    <div class="company">${this.symbols.get(order.symbol)?.name || ''}</div>
                </div>
            </td>
            <td><span class="order-side ${order.side}">${order.side.toUpperCase()}</span></td>
            <td><span class="order-type ${order.type}">${order.type.toUpperCase()}</span></td>
            <td>${order.quantity.toLocaleString()}</td>
            <td>${this.formatCurrency(order.price)}</td>
            <td>${order.filledQuantity.toLocaleString()}</td>
            <td><span class="order-status ${order.status}">${order.status.toUpperCase()}</span></td>
            <td>
                <div class="order-actions">
                    <button class="btn btn-xs btn-outline" onclick="tradingManager.modifyOrder('${order.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-xs btn-error" onclick="tradingManager.cancelOrder('${order.id}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </td>
        `;

        tableBody.insertBefore(row, tableBody.firstChild);
        
        // Mise à jour du badge de comptage
        this.updateTableBadge('orders');
    }

    /**
     * Mise à jour du portefeuille après exécution
     */
    updatePortfolio(order) {
        // Simulation de mise à jour du portefeuille
        const positionsTable = document.querySelector('#positionsTable tbody');
        if (!positionsTable) return;

        // Recherche d'une position existante
        const existingRow = Array.from(positionsTable.rows).find(row => 
            row.cells[0].textContent.includes(order.symbol)
        );

        if (existingRow) {
            // Mise à jour de la position existante
            this.updateExistingPosition(existingRow, order);
        } else {
            // Création d'une nouvelle position
            this.createNewPosition(order);
        }
    }

    /**
     * Création d'une nouvelle position
     */
    createNewPosition(order) {
        const positionsTable = document.querySelector('#positionsTable tbody');
        if (!positionsTable) return;

        const symbolData = this.symbols.get(order.symbol);
        const currentPrice = symbolData?.price || order.price;
        const unrealizedPnL = (currentPrice - order.avgPrice) * order.quantity * (order.side === 'buy' ? 1 : -1);
        const unrealizedPnLPercent = (unrealizedPnL / (order.avgPrice * order.quantity)) * 100;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <div class="symbol-cell">
                    <div class="symbol">${order.symbol}</div>
                    <div class="company">${symbolData?.name || ''}</div>
                </div>
            </td>
            <td>${order.side === 'buy' ? order.quantity : -order.quantity}</td>
            <td>${this.formatCurrency(order.avgPrice)}</td>
            <td>${this.formatCurrency(currentPrice)}</td>
            <td>
                <div class="pnl ${unrealizedPnL >= 0 ? 'positive' : 'negative'}">
                    ${this.formatCurrency(unrealizedPnL)}
                </div>
                <div class="pnl-percent ${unrealizedPnLPercent >= 0 ? 'positive' : 'negative'}">
                    (${unrealizedPnLPercent >= 0 ? '+' : ''}${unrealizedPnLPercent.toFixed(2)}%)
                </div>
            </td>
            <td>${this.formatCurrency(order.avgPrice * Math.abs(order.quantity))}</td>
            <td>
                <div class="position-actions">
                    <button class="btn btn-xs btn-outline" onclick="tradingManager.closePosition('${order.symbol}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </td>
        `;

        positionsTable.appendChild(row);
        this.updateTableBadge('positions');
    }

    /**
     * Basculement entre les tableaux
     */
    switchTable(tableName) {
        // Mise à jour des onglets
        document.querySelectorAll('.table-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.table === tableName);
        });

        // Affichage du bon tableau
        document.querySelectorAll('.trading-table').forEach(table => {
            table.classList.toggle('active', table.id === tableName + 'Table');
        });
    }

    /**
     * Basculement de timeframe
     */
    switchTimeframe(timeframe) {
        document.querySelectorAll('.timeframe-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.timeframe === timeframe);
        });

        // Mise à jour du graphique avec le nouveau timeframe
        this.updateChart(timeframe);
    }

    /**
     * Initialisation des graphiques
     */
    initializeCharts() {
        this.initializePriceChart();
        this.updateOrderBook();
    }

    /**
     * Initialisation du graphique de prix principal
     */
    initializePriceChart() {
        const canvas = document.getElementById('tradingChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        // Génération de données de test pour le graphique candlestick
        const data = this.generateCandlestickData();

        this.charts.set('main', new Chart(ctx, {
            type: 'candlestick',
            data: {
                datasets: [{
                    label: this.currentSymbol,
                    data: data,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            title: function(context) {
                                return new Date(context[0].parsed.x).toLocaleString();
                            },
                            label: function(context) {
                                const data = context.parsed;
                                return [
                                    `Open: ${data.o?.toFixed(2) || 'N/A'}`,
                                    `High: ${data.h?.toFixed(2) || 'N/A'}`,
                                    `Low: ${data.l?.toFixed(2) || 'N/A'}`,
                                    `Close: ${data.c?.toFixed(2) || 'N/A'}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'minute'
                        }
                    },
                    y: {
                        position: 'right'
                    }
                }
            }
        }));
    }

    /**
     * Génération de données candlestick de test
     */
    generateCandlestickData() {
        const data = [];
        const symbolData = this.symbols.get(this.currentSymbol);
        let basePrice = symbolData?.price || 100;
        
        for (let i = 0; i < 100; i++) {
            const time = new Date(Date.now() - (100 - i) * 60000);
            const open = basePrice;
            const high = open + Math.random() * 5;
            const low = open - Math.random() * 5;
            const close = low + Math.random() * (high - low);
            
            data.push({
                x: time,
                o: open,
                h: high,
                l: low,
                c: close
            });
            
            basePrice = close + (Math.random() - 0.5) * 2;
        }
        
        return data;
    }

    /**
     * Mise à jour du carnet d'ordres
     */
    updateOrderBook() {
        const asksContainer = document.querySelector('.orderbook-asks');
        const bidsContainer = document.querySelector('.orderbook-bids');
        
        if (!asksContainer || !bidsContainer) return;

        const symbolData = this.symbols.get(this.currentSymbol);
        if (!symbolData) return;

        // Génération des données du carnet d'ordres
        const asks = this.generateOrderBookSide(symbolData.ask, 'ask');
        const bids = this.generateOrderBookSide(symbolData.bid, 'bid');

        // Mise à jour des asks (ordres de vente)
        asksContainer.innerHTML = asks.map(order => `
            <div class="orderbook-row">
                <span>${order.size.toLocaleString()}</span>
                <span>${this.formatCurrency(order.price)}</span>
                <span>${order.total.toLocaleString()}</span>
            </div>
        `).join('');

        // Mise à jour des bids (ordres d'achat)
        bidsContainer.innerHTML = bids.map(order => `
            <div class="orderbook-row">
                <span>${order.size.toLocaleString()}</span>
                <span>${this.formatCurrency(order.price)}</span>
                <span>${order.total.toLocaleString()}</span>
            </div>
        `).join('');

        // Mise à jour du spread
        const spread = symbolData.ask - symbolData.bid;
        const spreadContainer = document.querySelector('.spread-value');
        if (spreadContainer) {
            spreadContainer.textContent = this.formatCurrency(spread);
        }
    }

    /**
     * Génération d'un côté du carnet d'ordres
     */
    generateOrderBookSide(basePrice, side) {
        const orders = [];
        const increment = side === 'ask' ? 0.01 : -0.01;
        
        for (let i = 0; i < 10; i++) {
            const price = basePrice + (increment * i);
            const size = Math.floor(Math.random() * 10000) + 100;
            const total = size * price;
            
            orders.push({ price, size, total });
        }
        
        return orders;
    }

    /**
     * Mise à jour des badges de comptage des tableaux
     */
    updateTableBadge(tableName) {
        const tab = document.querySelector(`[data-table="${tableName}"]`);
        if (!tab) return;

        const badge = tab.querySelector('.badge');
        const table = document.getElementById(tableName + 'Table');
        
        if (badge && table) {
            const rowCount = table.querySelectorAll('tbody tr').length;
            badge.textContent = rowCount;
        }
    }

    /**
     * Démarrage des mises à jour en temps réel
     */
    startRealTimeUpdates() {
        // Simulation de mises à jour de prix en temps réel
        this.priceUpdateInterval = setInterval(() => {
            this.updatePrices();
        }, 2000);
    }

    /**
     * Mise à jour des prix en temps réel
     */
    updatePrices() {
        this.symbols.forEach((data, symbol) => {
            // Simulation de changement de prix
            const change = (Math.random() - 0.5) * 2;
            const newPrice = Math.max(data.price + change, 0.01);
            const priceChange = newPrice - data.price;
            const percentChange = (priceChange / data.price) * 100;

            this.symbols.set(symbol, {
                ...data,
                price: newPrice,
                change: priceChange,
                changePercent: percentChange,
                bid: newPrice - 0.01,
                ask: newPrice + 0.01
            });
        });

        // Mise à jour de l'affichage du symbole actuel
        if (this.currentSymbol) {
            this.updateCurrentPrice();
            this.updateOrderBook();
            this.updateOrderSummary();
        }
    }

    /**
     * Réinitialisation du formulaire d'ordre
     */
    resetOrderForm() {
        const form = document.getElementById('orderForm');
        if (form) {
            form.reset();
            this.currentSide = 'buy';
            document.getElementById('buyOption').checked = true;
            this.updateOrderSummary();
        }
    }

    /**
     * Affichage de notifications
     */
    showNotification(message, type = 'info') {
        // Intégration avec le système de notifications existant
        if (window.notifications) {
            window.notifications.show(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    /**
     * Formatage des valeurs monétaires
     */
    formatCurrency(value, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    }

    /**
     * Chargement des données initiales
     */
    loadInitialData() {
        // Sélection du symbole par défaut
        this.selectSymbol(this.currentSymbol);
        
        // Chargement des ordres et positions existantes
        this.loadOpenOrders();
        this.loadPositions();
        this.loadTradeHistory();
    }

    /**
     * Chargement des ordres ouverts
     */
    loadOpenOrders() {
        // Simulation de données d'ordres existantes
        const sampleOrders = [
            {
                id: 'ORD-001',
                symbol: 'AAPL',
                side: 'buy',
                type: 'limit',
                quantity: 100,
                price: 170.00,
                filledQuantity: 0,
                status: 'pending'
            },
            {
                id: 'ORD-002',
                symbol: 'GOOGL',
                side: 'sell',
                type: 'stop',
                quantity: 10,
                price: 2800.00,
                filledQuantity: 0,
                status: 'pending'
            }
        ];

        sampleOrders.forEach(order => this.addOrderToTable(order));
    }

    /**
     * Chargement des positions
     */
    loadPositions() {
        // Simulation de positions existantes
        const samplePositions = [
            {
                symbol: 'MSFT',
                side: 'buy',
                quantity: 50,
                avgPrice: 335.00
            },
            {
                symbol: 'TSLA',
                side: 'buy',
                quantity: 25,
                avgPrice: 255.00
            }
        ];

        samplePositions.forEach(position => {
            const order = {
                ...position,
                id: 'POS-' + Date.now(),
                status: 'filled',
                filledQuantity: position.quantity
            };
            this.createNewPosition(order);
        });
    }

    /**
     * Chargement de l'historique des transactions
     */
    loadTradeHistory() {
        // Simulation d'historique de trades
        const sampleTrades = [
            {
                symbol: 'AAPL',
                side: 'buy',
                quantity: 100,
                price: 165.50,
                timestamp: new Date(Date.now() - 86400000)
            },
            {
                symbol: 'NVDA',
                side: 'sell',
                quantity: 20,
                price: 450.00,
                timestamp: new Date(Date.now() - 172800000)
            }
        ];

        const historyTable = document.querySelector('#historyTable tbody');
        if (!historyTable) return;

        sampleTrades.forEach(trade => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="symbol-cell">
                        <div class="symbol">${trade.symbol}</div>
                        <div class="company">${this.symbols.get(trade.symbol)?.name || ''}</div>
                    </div>
                </td>
                <td><span class="order-side ${trade.side}">${trade.side.toUpperCase()}</span></td>
                <td>${trade.quantity.toLocaleString()}</td>
                <td>${this.formatCurrency(trade.price)}</td>
                <td>${this.formatCurrency(trade.quantity * trade.price)}</td>
                <td>${trade.timestamp.toLocaleString()}</td>
            `;
            historyTable.appendChild(row);
        });

        this.updateTableBadge('history');
    }

    /**
     * Arrêt du gestionnaire
     */
    destroy() {
        if (this.priceUpdateInterval) {
            clearInterval(this.priceUpdateInterval);
        }
        
        if (this.webSocket) {
            this.webSocket.close();
        }
        
        console.log('Trading Manager arrêté');
    }
}

// Initialisation globale
let tradingManager;

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation du gestionnaire de trading uniquement sur la page trading
    if (document.querySelector('.trading-layout')) {
        tradingManager = new TradingManager();
    }
});

// Fonctions globales pour les événements
window.tradingManager = {
    modifyOrder: function(orderId) {
        console.log('Modification de l\'ordre:', orderId);
        // Implémentation de la modification d'ordre
    },
    
    cancelOrder: function(orderId) {
        console.log('Annulation de l\'ordre:', orderId);
        // Implémentation de l'annulation d'ordre
    },
    
    closePosition: function(symbol) {
        console.log('Fermeture de la position:', symbol);
        // Implémentation de la fermeture de position
    }
};