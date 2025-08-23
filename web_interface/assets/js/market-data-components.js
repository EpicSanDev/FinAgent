/**
 * Market Data Components - Composants de visualisation des données de marché
 * Gestion des graphiques financiers avancés et visualisation de données
 */

class MarketDataComponents {
    constructor() {
        this.charts = new Map();
        this.dataProviders = new Map();
        this.updateIntervals = new Map();
        this.wsConnections = new Map();
        
        this.chartColors = {
            bullish: '#10B981',   // Vert pour hausse
            bearish: '#EF4444',   // Rouge pour baisse
            neutral: '#6B7280',   // Gris pour neutre
            volume: '#8B5CF6',    // Violet pour volume
            ma50: '#F59E0B',      // Orange pour MA50
            ma200: '#3B82F6',     // Bleu pour MA200
            rsi: '#EC4899',       // Rose pour RSI
            macd: '#06B6D4'       // Cyan pour MACD
        };
        
        this.init();
    }

    /**
     * Initialisation des composants de données de marché
     */
    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeComponents());
        } else {
            this.initializeComponents();
        }
    }

    /**
     * Initialiser tous les composants
     */
    initializeComponents() {
        try {
            this.setupDataProviders();
            this.initializeCandlestickChart();
            this.initializeVolumeChart();
            this.initializeIndicatorsCharts();
            this.initializeHeatmap();
            this.initializeDepthChart();
            
            console.log('Composants de données de marché initialisés avec succès');
        } catch (error) {
            console.error('Erreur lors de l\'initialisation des composants:', error);
        }
    }

    /**
     * Configuration des fournisseurs de données
     */
    setupDataProviders() {
        // Simulateur de données de marché
        this.dataProviders.set('stocks', new StockDataProvider());
        this.dataProviders.set('forex', new ForexDataProvider());
        this.dataProviders.set('crypto', new CryptoDataProvider());
        this.dataProviders.set('indices', new IndicesDataProvider());
    }

    /**
     * Graphique en chandelles japonaises
     */
    initializeCandlestickChart() {
        const container = document.getElementById('candlestick-chart');
        if (!container) return;

        // Utiliser TradingView Lightweight Charts pour les chandelles
        const chart = LightweightCharts.createChart(container, {
            width: container.clientWidth,
            height: 400,
            layout: {
                backgroundColor: 'transparent',
                textColor: '#333',
            },
            grid: {
                vertLines: {
                    color: '#f0f0f0',
                },
                horzLines: {
                    color: '#f0f0f0',
                },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#cccccc',
            },
            timeScale: {
                borderColor: '#cccccc',
                timeVisible: true,
                secondsVisible: false,
            },
        });

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: this.chartColors.bullish,
            downColor: this.chartColors.bearish,
            borderUpColor: this.chartColors.bullish,
            borderDownColor: this.chartColors.bearish,
            wickUpColor: this.chartColors.bullish,
            wickDownColor: this.chartColors.bearish,
        });

        // Ajouter des moyennes mobiles
        const ma50Series = chart.addLineSeries({
            color: this.chartColors.ma50,
            lineWidth: 2,
            title: 'MA50',
        });

        const ma200Series = chart.addLineSeries({
            color: this.chartColors.ma200,
            lineWidth: 2,
            title: 'MA200',
        });

        // Générer des données OHLC simulées
        const ohlcData = this.generateOHLCData();
        candlestickSeries.setData(ohlcData.candles);
        ma50Series.setData(ohlcData.ma50);
        ma200Series.setData(ohlcData.ma200);

        this.charts.set('candlestick', {
            chart,
            series: {
                candlestick: candlestickSeries,
                ma50: ma50Series,
                ma200: ma200Series
            }
        });

        // Redimensionnement automatique
        new ResizeObserver(entries => {
            if (entries.length === 0) return;
            const { width, height } = entries[0].contentRect;
            chart.applyOptions({ width, height });
        }).observe(container);
    }

    /**
     * Graphique de volume
     */
    initializeVolumeChart() {
        const canvas = document.getElementById('volume-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const volumeData = this.generateVolumeData();

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: volumeData.labels,
                datasets: [{
                    label: 'Volume',
                    data: volumeData.volumes,
                    backgroundColor: volumeData.colors,
                    borderWidth: 0,
                    barPercentage: 0.8,
                    categoryPercentage: 0.9
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
                        callbacks: {
                            label: (context) => {
                                return `Volume: ${this.formatVolume(context.parsed.y)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        position: 'right',
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        },
                        ticks: {
                            callback: (value) => this.formatVolume(value)
                        }
                    }
                },
                interaction: {
                    intersect: false
                }
            }
        });

        this.charts.set('volume', chart);
    }

    /**
     * Graphiques d'indicateurs techniques
     */
    initializeIndicatorsCharts() {
        this.initializeRSIChart();
        this.initializeMACDChart();
        this.initializeBollingerBandsChart();
    }

    /**
     * Graphique RSI
     */
    initializeRSIChart() {
        const canvas = document.getElementById('rsi-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const rsiData = this.generateRSIData();

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: rsiData.labels,
                datasets: [{
                    label: 'RSI',
                    data: rsiData.values,
                    borderColor: this.chartColors.rsi,
                    backgroundColor: this.chartColors.rsi + '20',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        position: 'right',
                        grid: {
                            color: (context) => {
                                if (context.tick.value === 70 || context.tick.value === 30) {
                                    return this.chartColors.rsi;
                                }
                                return 'rgba(0,0,0,0.1)';
                            }
                        },
                        ticks: {
                            callback: (value) => value + '%'
                        }
                    }
                },
                // Ajouter des lignes de référence à 30 et 70
                annotation: {
                    annotations: {
                        oversold: {
                            type: 'line',
                            yMin: 30,
                            yMax: 30,
                            borderColor: this.chartColors.bearish,
                            borderWidth: 1,
                            borderDash: [5, 5]
                        },
                        overbought: {
                            type: 'line',
                            yMin: 70,
                            yMax: 70,
                            borderColor: this.chartColors.bullish,
                            borderWidth: 1,
                            borderDash: [5, 5]
                        }
                    }
                }
            }
        });

        this.charts.set('rsi', chart);
    }

    /**
     * Graphique MACD
     */
    initializeMACDChart() {
        const canvas = document.getElementById('macd-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const macdData = this.generateMACDData();

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: macdData.labels,
                datasets: [{
                    label: 'MACD',
                    data: macdData.macd,
                    borderColor: this.chartColors.macd,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0
                }, {
                    label: 'Signal',
                    data: macdData.signal,
                    borderColor: this.chartColors.bearish,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0
                }, {
                    label: 'Histogramme',
                    data: macdData.histogram,
                    type: 'bar',
                    backgroundColor: macdData.histogramColors,
                    borderWidth: 0,
                    barPercentage: 0.6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'start',
                        labels: {
                            boxWidth: 12,
                            padding: 15,
                            font: {
                                size: 11
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        position: 'right',
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    }
                }
            }
        });

        this.charts.set('macd', chart);
    }

    /**
     * Heatmap des corrélations
     */
    initializeHeatmap() {
        const container = document.getElementById('correlation-heatmap');
        if (!container) return;

        const correlationData = this.generateCorrelationData();
        this.renderHeatmap(container, correlationData);
    }

    /**
     * Graphique de profondeur du marché
     */
    initializeDepthChart() {
        const canvas = document.getElementById('depth-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const depthData = this.generateDepthData();

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: depthData.prices,
                datasets: [{
                    label: 'Demande (Bids)',
                    data: depthData.bids,
                    borderColor: this.chartColors.bullish,
                    backgroundColor: this.chartColors.bullish + '30',
                    fill: 'origin',
                    stepped: true,
                    pointRadius: 0
                }, {
                    label: 'Offre (Asks)',
                    data: depthData.asks,
                    borderColor: this.chartColors.bearish,
                    backgroundColor: this.chartColors.bearish + '30',
                    fill: 'origin',
                    stepped: true,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Prix'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Volume Cumulé'
                        },
                        position: 'right'
                    }
                }
            }
        });

        this.charts.set('depth', chart);
    }

    /**
     * Générateurs de données simulées
     */
    generateOHLCData() {
        const days = 100;
        const candles = [];
        const ma50 = [];
        const ma200 = [];
        let currentPrice = 100;
        const prices = [];

        for (let i = 0; i < days; i++) {
            const date = new Date();
            date.setDate(date.getDate() - (days - i));
            
            const open = currentPrice;
            const change = (Math.random() - 0.5) * 4;
            const high = open + Math.random() * 2 + Math.abs(change);
            const low = open - Math.random() * 2 - Math.abs(change);
            const close = open + change;
            
            candles.push({
                time: date.getTime() / 1000,
                open: parseFloat(open.toFixed(2)),
                high: parseFloat(high.toFixed(2)),
                low: parseFloat(low.toFixed(2)),
                close: parseFloat(close.toFixed(2))
            });
            
            prices.push(close);
            currentPrice = close;
            
            // Calcul des moyennes mobiles
            if (i >= 49) {
                const ma50Value = prices.slice(i - 49, i + 1).reduce((a, b) => a + b) / 50;
                ma50.push({
                    time: date.getTime() / 1000,
                    value: parseFloat(ma50Value.toFixed(2))
                });
            }
            
            if (i >= 199) {
                const ma200Value = prices.slice(i - 199, i + 1).reduce((a, b) => a + b) / 200;
                ma200.push({
                    time: date.getTime() / 1000,
                    value: parseFloat(ma200Value.toFixed(2))
                });
            }
        }

        return { candles, ma50, ma200 };
    }

    generateVolumeData() {
        const days = 30;
        const labels = [];
        const volumes = [];
        const colors = [];

        for (let i = 0; i < days; i++) {
            const date = new Date();
            date.setDate(date.getDate() - (days - i));
            labels.push(date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' }));
            
            const volume = Math.random() * 1000000 + 500000;
            volumes.push(volume);
            
            // Couleur basée sur la tendance
            const color = Math.random() > 0.5 ? this.chartColors.bullish : this.chartColors.bearish;
            colors.push(color + '80');
        }

        return { labels, volumes, colors };
    }

    generateRSIData() {
        const days = 50;
        const labels = [];
        const values = [];

        for (let i = 0; i < days; i++) {
            const date = new Date();
            date.setDate(date.getDate() - (days - i));
            labels.push(date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' }));
            
            // Simuler des valeurs RSI réalistes
            const rsi = Math.random() * 60 + 20; // Entre 20 et 80
            values.push(parseFloat(rsi.toFixed(2)));
        }

        return { labels, values };
    }

    generateMACDData() {
        const days = 50;
        const labels = [];
        const macd = [];
        const signal = [];
        const histogram = [];
        const histogramColors = [];

        for (let i = 0; i < days; i++) {
            const date = new Date();
            date.setDate(date.getDate() - (days - i));
            labels.push(date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' }));
            
            const macdValue = (Math.random() - 0.5) * 2;
            const signalValue = macdValue + (Math.random() - 0.5) * 0.5;
            const histValue = macdValue - signalValue;
            
            macd.push(parseFloat(macdValue.toFixed(3)));
            signal.push(parseFloat(signalValue.toFixed(3)));
            histogram.push(parseFloat(histValue.toFixed(3)));
            
            histogramColors.push(histValue >= 0 ? this.chartColors.bullish + '80' : this.chartColors.bearish + '80');
        }

        return { labels, macd, signal, histogram, histogramColors };
    }

    generateCorrelationData() {
        const symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX'];
        const correlations = [];

        for (let i = 0; i < symbols.length; i++) {
            const row = [];
            for (let j = 0; j < symbols.length; j++) {
                if (i === j) {
                    row.push(1.0);
                } else {
                    row.push(parseFloat((Math.random() * 1.8 - 0.9).toFixed(2)));
                }
            }
            correlations.push(row);
        }

        return { symbols, correlations };
    }

    generateDepthData() {
        const centerPrice = 100;
        const prices = [];
        const bids = [];
        const asks = [];
        
        // Génération des prix autour du prix central
        for (let i = -20; i <= 20; i++) {
            const price = centerPrice + (i * 0.1);
            prices.push(price.toFixed(1));
            
            if (i <= 0) {
                // Côté demande (bids)
                const volume = Math.abs(i) * 1000 + Math.random() * 5000;
                bids.push(volume);
                asks.push(null);
            } else {
                // Côté offre (asks)
                const volume = i * 1000 + Math.random() * 5000;
                asks.push(volume);
                bids.push(null);
            }
        }

        return { prices, bids, asks };
    }

    /**
     * Rendu de la heatmap
     */
    renderHeatmap(container, data) {
        container.innerHTML = '';
        
        const table = document.createElement('table');
        table.className = 'correlation-heatmap-table';
        
        // En-tête
        const header = document.createElement('tr');
        header.appendChild(document.createElement('th')); // Cellule vide pour l'angle
        data.symbols.forEach(symbol => {
            const th = document.createElement('th');
            th.textContent = symbol;
            header.appendChild(th);
        });
        table.appendChild(header);
        
        // Lignes de données
        data.symbols.forEach((symbol, i) => {
            const row = document.createElement('tr');
            
            const rowHeader = document.createElement('th');
            rowHeader.textContent = symbol;
            row.appendChild(rowHeader);
            
            data.correlations[i].forEach(correlation => {
                const cell = document.createElement('td');
                cell.textContent = correlation.toFixed(2);
                
                // Couleur basée sur la corrélation
                const intensity = Math.abs(correlation);
                const color = correlation >= 0 ? this.chartColors.bullish : this.chartColors.bearish;
                cell.style.backgroundColor = color + Math.floor(intensity * 255).toString(16).padStart(2, '0');
                cell.style.color = intensity > 0.5 ? 'white' : 'black';
                
                row.appendChild(cell);
            });
            
            table.appendChild(row);
        });
        
        container.appendChild(table);
    }

    /**
     * Mise à jour des données en temps réel
     */
    startRealTimeUpdates() {
        // Simuler les mises à jour en temps réel
        this.updateIntervals.set('prices', setInterval(() => {
            this.updatePriceData();
        }, 5000));
        
        this.updateIntervals.set('volume', setInterval(() => {
            this.updateVolumeData();
        }, 10000));
    }

    updatePriceData() {
        const candlestickChart = this.charts.get('candlestick');
        if (candlestickChart) {
            // Ajouter une nouvelle chandelle
            const lastTime = Math.floor(Date.now() / 1000);
            const newCandle = {
                time: lastTime,
                open: 100 + (Math.random() - 0.5) * 10,
                high: 105 + Math.random() * 5,
                low: 95 + Math.random() * 5,
                close: 100 + (Math.random() - 0.5) * 10
            };
            
            candlestickChart.series.candlestick.update(newCandle);
        }
    }

    updateVolumeData() {
        const volumeChart = this.charts.get('volume');
        if (volumeChart) {
            // Mettre à jour le dernier volume
            const data = volumeChart.data.datasets[0].data;
            data[data.length - 1] = Math.random() * 1000000 + 500000;
            volumeChart.update('none');
        }
    }

    /**
     * Utilitaires
     */
    formatVolume(volume) {
        if (volume >= 1000000) {
            return (volume / 1000000).toFixed(1) + 'M';
        } else if (volume >= 1000) {
            return (volume / 1000).toFixed(1) + 'K';
        }
        return volume.toString();
    }

    formatCurrency(value, currency = 'EUR') {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2
        }).format(value);
    }

    /**
     * Gestion du thème
     */
    updateTheme(isDark) {
        const textColor = isDark ? '#E5E7EB' : '#374151';
        const gridColor = isDark ? 'rgba(229, 231, 235, 0.1)' : 'rgba(107, 114, 128, 0.1)';
        
        this.charts.forEach(chart => {
            if (chart.chart && chart.chart.applyOptions) {
                // TradingView chart
                chart.chart.applyOptions({
                    layout: {
                        backgroundColor: 'transparent',
                        textColor: textColor,
                    },
                    grid: {
                        vertLines: { color: gridColor },
                        horzLines: { color: gridColor },
                    }
                });
            } else if (chart.options) {
                // Chart.js
                chart.options.scales.x.ticks.color = textColor;
                chart.options.scales.y.ticks.color = textColor;
                chart.options.scales.y.grid.color = gridColor;
                chart.update('none');
            }
        });
    }

    /**
     * Nettoyage
     */
    destroy() {
        this.updateIntervals.forEach(interval => clearInterval(interval));
        this.updateIntervals.clear();
        
        this.wsConnections.forEach(ws => ws.close());
        this.wsConnections.clear();
        
        this.charts.forEach(chart => {
            if (chart.chart && chart.chart.remove) {
                chart.chart.remove();
            } else if (chart.destroy) {
                chart.destroy();
            }
        });
        this.charts.clear();
    }
}

/**
 * Fournisseurs de données simulées
 */
class StockDataProvider {
    async getData(symbol, timeframe = '1D') {
        // Simuler une API REST
        return new Promise(resolve => {
            setTimeout(() => {
                resolve(this.generateStockData(symbol, timeframe));
            }, Math.random() * 1000 + 500);
        });
    }
    
    generateStockData(symbol, timeframe) {
        // Générer des données OHLCV simulées
        return {
            symbol,
            timeframe,
            data: [] // Données OHLCV
        };
    }
}

class ForexDataProvider {
    async getData(pair, timeframe = '1H') {
        return new Promise(resolve => {
            setTimeout(() => {
                resolve(this.generateForexData(pair, timeframe));
            }, Math.random() * 800 + 300);
        });
    }
    
    generateForexData(pair, timeframe) {
        return {
            pair,
            timeframe,
            data: []
        };
    }
}

class CryptoDataProvider {
    async getData(symbol, timeframe = '1H') {
        return new Promise(resolve => {
            setTimeout(() => {
                resolve(this.generateCryptoData(symbol, timeframe));
            }, Math.random() * 1200 + 400);
        });
    }
    
    generateCryptoData(symbol, timeframe) {
        return {
            symbol,
            timeframe,
            data: []
        };
    }
}

class IndicesDataProvider {
    async getData(index, timeframe = '1D') {
        return new Promise(resolve => {
            setTimeout(() => {
                resolve(this.generateIndexData(index, timeframe));
            }, Math.random() * 600 + 200);
        });
    }
    
    generateIndexData(index, timeframe) {
        return {
            index,
            timeframe,
            data: []
        };
    }
}

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MarketDataComponents;
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    if (typeof window !== 'undefined') {
        window.marketDataComponents = new MarketDataComponents();
    }
});