/**
 * Technical Indicators and Advanced Analytics
 * Système avancé d'indicateurs techniques et d'analyses financières
 */

class TechnicalIndicators {
    constructor() {
        this.indicators = new Map();
        this.charts = new Map();
        this.dataCache = new Map();
        this.settings = {
            rsi: { period: 14, overbought: 70, oversold: 30 },
            macd: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
            bollinger: { period: 20, stdDev: 2 },
            sma: { periods: [20, 50, 200] },
            ema: { periods: [12, 26] },
            stochastic: { kPeriod: 14, dPeriod: 3, slowing: 3 },
            adx: { period: 14 },
            williams: { period: 14 },
            atr: { period: 14 },
            obv: {},
            vwap: {}
        };
        this.init();
    }

    /**
     * Initialisation du système d'indicateurs
     */
    init() {
        this.setupIndicatorPanels();
        this.bindEvents();
        this.loadDefaultIndicators();
    }

    /**
     * Configuration des panneaux d'indicateurs
     */
    setupIndicatorPanels() {
        const indicatorsContainer = document.getElementById('technical-indicators');
        if (!indicatorsContainer) return;

        indicatorsContainer.innerHTML = `
            <div class="indicators-toolbar">
                <div class="indicators-controls">
                    <button class="btn btn-sm btn-primary" id="add-indicator">
                        <i class="fas fa-plus"></i> Ajouter Indicateur
                    </button>
                    <button class="btn btn-sm btn-outline" id="reset-indicators">
                        <i class="fas fa-refresh"></i> Réinitialiser
                    </button>
                    <div class="indicator-presets">
                        <select id="indicator-preset" class="form-select">
                            <option value="">Sélectionner un preset...</option>
                            <option value="trend">Analyse de Tendance</option>
                            <option value="momentum">Momentum</option>
                            <option value="volatility">Volatilité</option>
                            <option value="volume">Volume</option>
                            <option value="full">Analyse Complète</option>
                        </select>
                    </div>
                </div>
                <div class="indicators-legend" id="indicators-legend">
                    <!-- Légende des indicateurs actifs -->
                </div>
            </div>
            <div class="indicators-panels" id="indicators-panels">
                <!-- Panneaux des indicateurs -->
            </div>
        `;
    }

    /**
     * Liaison des événements
     */
    bindEvents() {
        document.getElementById('add-indicator')?.addEventListener('click', () => {
            this.showIndicatorSelector();
        });

        document.getElementById('reset-indicators')?.addEventListener('click', () => {
            this.resetAllIndicators();
        });

        document.getElementById('indicator-preset')?.addEventListener('change', (e) => {
            if (e.target.value) {
                this.loadPreset(e.target.value);
            }
        });

        // Événements de redimensionnement
        window.addEventListener('resize', () => {
            this.resizeAllCharts();
        });
    }

    /**
     * Chargement des indicateurs par défaut
     */
    loadDefaultIndicators() {
        // RSI par défaut
        this.addIndicator('rsi', { period: 14 });
        
        // MACD par défaut
        this.addIndicator('macd', { 
            fastPeriod: 12, 
            slowPeriod: 26, 
            signalPeriod: 9 
        });

        // Volume par défaut
        this.addIndicator('volume');
    }

    /**
     * Affichage du sélecteur d'indicateurs
     */
    showIndicatorSelector() {
        const modal = document.createElement('div');
        modal.className = 'modal modal-active';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Ajouter un Indicateur Technique</h3>
                        <button class="modal-close" data-dismiss="modal">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="indicators-grid">
                            <div class="indicator-category">
                                <h4>Tendance</h4>
                                <div class="indicator-list">
                                    <button class="indicator-btn" data-indicator="sma">
                                        <i class="fas fa-chart-line"></i>
                                        <span>SMA</span>
                                        <small>Moyenne Mobile Simple</small>
                                    </button>
                                    <button class="indicator-btn" data-indicator="ema">
                                        <i class="fas fa-chart-line"></i>
                                        <span>EMA</span>
                                        <small>Moyenne Mobile Exponentielle</small>
                                    </button>
                                    <button class="indicator-btn" data-indicator="bollinger">
                                        <i class="fas fa-chart-area"></i>
                                        <span>Bollinger Bands</span>
                                        <small>Bandes de Bollinger</small>
                                    </button>
                                    <button class="indicator-btn" data-indicator="adx">
                                        <i class="fas fa-trending-up"></i>
                                        <span>ADX</span>
                                        <small>Average Directional Index</small>
                                    </button>
                                </div>
                            </div>
                            <div class="indicator-category">
                                <h4>Momentum</h4>
                                <div class="indicator-list">
                                    <button class="indicator-btn" data-indicator="rsi">
                                        <i class="fas fa-wave-square"></i>
                                        <span>RSI</span>
                                        <small>Relative Strength Index</small>
                                    </button>
                                    <button class="indicator-btn" data-indicator="macd">
                                        <i class="fas fa-chart-bar"></i>
                                        <span>MACD</span>
                                        <small>Moving Average Convergence Divergence</small>
                                    </button>
                                    <button class="indicator-btn" data-indicator="stochastic">
                                        <i class="fas fa-wave-square"></i>
                                        <span>Stochastique</span>
                                        <small>Oscillateur Stochastique</small>
                                    </button>
                                    <button class="indicator-btn" data-indicator="williams">
                                        <i class="fas fa-chart-line"></i>
                                        <span>Williams %R</span>
                                        <small>Williams Percent Range</small>
                                    </button>
                                </div>
                            </div>
                            <div class="indicator-category">
                                <h4>Volume</h4>
                                <div class="indicator-list">
                                    <button class="indicator-btn" data-indicator="volume">
                                        <i class="fas fa-chart-bar"></i>
                                        <span>Volume</span>
                                        <small>Volume des Transactions</small>
                                    </button>
                                    <button class="indicator-btn" data-indicator="obv">
                                        <i class="fas fa-chart-line"></i>
                                        <span>OBV</span>
                                        <small>On-Balance Volume</small>
                                    </button>
                                    <button class="indicator-btn" data-indicator="vwap">
                                        <i class="fas fa-chart-area"></i>
                                        <span>VWAP</span>
                                        <small>Volume Weighted Average Price</small>
                                    </button>
                                </div>
                            </div>
                            <div class="indicator-category">
                                <h4>Volatilité</h4>
                                <div class="indicator-list">
                                    <button class="indicator-btn" data-indicator="atr">
                                        <i class="fas fa-chart-area"></i>
                                        <span>ATR</span>
                                        <small>Average True Range</small>
                                    </button>
                                    <button class="indicator-btn" data-indicator="bollinger">
                                        <i class="fas fa-chart-area"></i>
                                        <span>Bollinger Bands</span>
                                        <small>Bandes de Bollinger</small>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Événements du modal
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        // Événements des boutons d'indicateurs
        modal.querySelectorAll('.indicator-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const indicatorType = btn.dataset.indicator;
                modal.remove();
                this.showIndicatorSettings(indicatorType);
            });
        });
    }

    /**
     * Affichage des paramètres d'un indicateur
     */
    showIndicatorSettings(type) {
        const settings = this.getIndicatorSettings(type);
        const modal = document.createElement('div');
        modal.className = 'modal modal-active';
        
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Paramètres - ${this.getIndicatorName(type)}</h3>
                        <button class="modal-close" data-dismiss="modal">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <form id="indicator-settings-form">
                            ${this.generateSettingsForm(type, settings)}
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-outline" data-dismiss="modal">Annuler</button>
                        <button type="submit" class="btn btn-primary" form="indicator-settings-form">Ajouter</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Événements
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });

        modal.querySelector('[data-dismiss="modal"]').addEventListener('click', () => {
            modal.remove();
        });

        modal.querySelector('#indicator-settings-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const params = Object.fromEntries(formData.entries());
            
            // Conversion des valeurs numériques
            Object.keys(params).forEach(key => {
                if (!isNaN(params[key]) && params[key] !== '') {
                    params[key] = Number(params[key]);
                }
            });

            this.addIndicator(type, params);
            modal.remove();
        });
    }

    /**
     * Génération du formulaire de paramètres
     */
    generateSettingsForm(type, settings) {
        let form = '';

        switch (type) {
            case 'rsi':
                form = `
                    <div class="form-group">
                        <label>Période</label>
                        <input type="number" name="period" value="${settings.period}" min="1" max="50" class="form-control">
                    </div>
                    <div class="form-group">
                        <label>Niveau de Surachat</label>
                        <input type="number" name="overbought" value="${settings.overbought}" min="50" max="90" class="form-control">
                    </div>
                    <div class="form-group">
                        <label>Niveau de Survente</label>
                        <input type="number" name="oversold" value="${settings.oversold}" min="10" max="50" class="form-control">
                    </div>
                `;
                break;

            case 'macd':
                form = `
                    <div class="form-group">
                        <label>Période Rapide</label>
                        <input type="number" name="fastPeriod" value="${settings.fastPeriod}" min="1" max="50" class="form-control">
                    </div>
                    <div class="form-group">
                        <label>Période Lente</label>
                        <input type="number" name="slowPeriod" value="${settings.slowPeriod}" min="1" max="100" class="form-control">
                    </div>
                    <div class="form-group">
                        <label>Période Signal</label>
                        <input type="number" name="signalPeriod" value="${settings.signalPeriod}" min="1" max="50" class="form-control">
                    </div>
                `;
                break;

            case 'bollinger':
                form = `
                    <div class="form-group">
                        <label>Période</label>
                        <input type="number" name="period" value="${settings.period}" min="1" max="100" class="form-control">
                    </div>
                    <div class="form-group">
                        <label>Écart-type</label>
                        <input type="number" name="stdDev" value="${settings.stdDev}" min="1" max="5" step="0.1" class="form-control">
                    </div>
                `;
                break;

            case 'sma':
            case 'ema':
                form = `
                    <div class="form-group">
                        <label>Périodes (séparées par des virgules)</label>
                        <input type="text" name="periods" value="${settings.periods.join(',')}" class="form-control" 
                               placeholder="20,50,200">
                    </div>
                `;
                break;

            case 'stochastic':
                form = `
                    <div class="form-group">
                        <label>Période %K</label>
                        <input type="number" name="kPeriod" value="${settings.kPeriod}" min="1" max="50" class="form-control">
                    </div>
                    <div class="form-group">
                        <label>Période %D</label>
                        <input type="number" name="dPeriod" value="${settings.dPeriod}" min="1" max="20" class="form-control">
                    </div>
                    <div class="form-group">
                        <label>Ralentissement</label>
                        <input type="number" name="slowing" value="${settings.slowing}" min="1" max="10" class="form-control">
                    </div>
                `;
                break;

            default:
                if (settings.period !== undefined) {
                    form = `
                        <div class="form-group">
                            <label>Période</label>
                            <input type="number" name="period" value="${settings.period}" min="1" max="100" class="form-control">
                        </div>
                    `;
                } else {
                    form = '<p>Cet indicateur ne nécessite pas de paramètres supplémentaires.</p>';
                }
                break;
        }

        return form;
    }

    /**
     * Ajout d'un indicateur
     */
    addIndicator(type, params = {}) {
        const indicatorId = `${type}_${Date.now()}`;
        const settings = { ...this.settings[type], ...params };
        
        // Création du panneau
        const panel = this.createIndicatorPanel(indicatorId, type, settings);
        document.getElementById('indicators-panels').appendChild(panel);

        // Stockage de l'indicateur
        this.indicators.set(indicatorId, {
            type,
            settings,
            panel,
            chart: null,
            data: null
        });

        // Calcul et affichage des données
        this.calculateAndDisplayIndicator(indicatorId);

        // Mise à jour de la légende
        this.updateLegend();
    }

    /**
     * Création du panneau d'un indicateur
     */
    createIndicatorPanel(id, type, settings) {
        const panel = document.createElement('div');
        panel.className = 'indicator-panel';
        panel.id = id;

        const height = this.getIndicatorHeight(type);
        
        panel.innerHTML = `
            <div class="indicator-header">
                <div class="indicator-title">
                    <i class="${this.getIndicatorIcon(type)}"></i>
                    <span>${this.getIndicatorName(type)}</span>
                    <small>${this.formatSettings(type, settings)}</small>
                </div>
                <div class="indicator-actions">
                    <button class="btn btn-sm btn-outline" onclick="technicalIndicators.editIndicator('${id}')">
                        <i class="fas fa-cog"></i>
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="technicalIndicators.removeIndicator('${id}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="indicator-body">
                <canvas id="chart_${id}" style="height: ${height}px;"></canvas>
            </div>
        `;

        return panel;
    }

    /**
     * Calcul et affichage d'un indicateur
     */
    async calculateAndDisplayIndicator(indicatorId) {
        const indicator = this.indicators.get(indicatorId);
        if (!indicator) return;

        try {
            // Récupération des données de marché
            const marketData = await this.getMarketData();
            
            // Calcul de l'indicateur
            const data = this.calculateIndicator(indicator.type, marketData, indicator.settings);
            
            // Stockage des données
            indicator.data = data;
            
            // Création du graphique
            const chart = this.createIndicatorChart(indicatorId, indicator.type, data, indicator.settings);
            indicator.chart = chart;

            // Affichage
            this.displayIndicator(indicatorId);

        } catch (error) {
            console.error(`Erreur lors du calcul de l'indicateur ${indicatorId}:`, error);
            this.showIndicatorError(indicatorId, error.message);
        }
    }

    /**
     * Calcul d'un indicateur technique
     */
    calculateIndicator(type, marketData, settings) {
        switch (type) {
            case 'rsi':
                return this.calculateRSI(marketData, settings.period);
            case 'macd':
                return this.calculateMACD(marketData, settings.fastPeriod, settings.slowPeriod, settings.signalPeriod);
            case 'bollinger':
                return this.calculateBollingerBands(marketData, settings.period, settings.stdDev);
            case 'sma':
                return this.calculateSMA(marketData, settings.periods);
            case 'ema':
                return this.calculateEMA(marketData, settings.periods);
            case 'stochastic':
                return this.calculateStochastic(marketData, settings.kPeriod, settings.dPeriod, settings.slowing);
            case 'adx':
                return this.calculateADX(marketData, settings.period);
            case 'williams':
                return this.calculateWilliamsR(marketData, settings.period);
            case 'atr':
                return this.calculateATR(marketData, settings.period);
            case 'obv':
                return this.calculateOBV(marketData);
            case 'vwap':
                return this.calculateVWAP(marketData);
            case 'volume':
                return this.extractVolume(marketData);
            default:
                throw new Error(`Indicateur non supporté: ${type}`);
        }
    }

    /**
     * Calcul du RSI
     */
    calculateRSI(data, period = 14) {
        const prices = data.map(d => d.close);
        const rsi = [];
        const gains = [];
        const losses = [];

        // Calcul des gains et pertes
        for (let i = 1; i < prices.length; i++) {
            const change = prices[i] - prices[i - 1];
            gains.push(change > 0 ? change : 0);
            losses.push(change < 0 ? Math.abs(change) : 0);
        }

        // Calcul du RSI
        for (let i = period - 1; i < gains.length; i++) {
            let avgGain, avgLoss;

            if (i === period - 1) {
                // Premier calcul (moyenne simple)
                avgGain = gains.slice(0, period).reduce((sum, gain) => sum + gain, 0) / period;
                avgLoss = losses.slice(0, period).reduce((sum, loss) => sum + loss, 0) / period;
            } else {
                // Calculs suivants (moyenne mobile lissée)
                const prevRSI = rsi[rsi.length - 1];
                avgGain = (avgGain * (period - 1) + gains[i]) / period;
                avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
            }

            const rs = avgGain / avgLoss;
            const rsiValue = 100 - (100 / (1 + rs));
            
            rsi.push({
                timestamp: data[i + 1].timestamp,
                value: rsiValue
            });
        }

        return rsi;
    }

    /**
     * Calcul du MACD
     */
    calculateMACD(data, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
        const prices = data.map(d => d.close);
        
        // Calcul des EMA
        const emaFast = this.calculateEMAValues(prices, fastPeriod);
        const emaSlow = this.calculateEMAValues(prices, slowPeriod);
        
        const macd = [];
        const signal = [];
        const histogram = [];

        // Calcul de la ligne MACD
        for (let i = slowPeriod - 1; i < prices.length; i++) {
            const macdValue = emaFast[i] - emaSlow[i];
            macd.push(macdValue);
        }

        // Calcul de la ligne de signal
        const signalEMA = this.calculateEMAValues(macd, signalPeriod);
        
        // Assemblage des résultats
        const result = [];
        for (let i = signalPeriod - 1; i < macd.length; i++) {
            const dataIndex = i + slowPeriod - 1;
            result.push({
                timestamp: data[dataIndex].timestamp,
                macd: macd[i],
                signal: signalEMA[i],
                histogram: macd[i] - signalEMA[i]
            });
        }

        return result;
    }

    /**
     * Calcul des Bandes de Bollinger
     */
    calculateBollingerBands(data, period = 20, stdDev = 2) {
        const prices = data.map(d => d.close);
        const result = [];

        for (let i = period - 1; i < prices.length; i++) {
            const slice = prices.slice(i - period + 1, i + 1);
            const sma = slice.reduce((sum, price) => sum + price, 0) / period;
            
            // Calcul de l'écart-type
            const variance = slice.reduce((sum, price) => sum + Math.pow(price - sma, 2), 0) / period;
            const standardDeviation = Math.sqrt(variance);
            
            result.push({
                timestamp: data[i].timestamp,
                middle: sma,
                upper: sma + (standardDeviation * stdDev),
                lower: sma - (standardDeviation * stdDev)
            });
        }

        return result;
    }

    /**
     * Calcul de moyennes mobiles simples multiples
     */
    calculateSMA(data, periods) {
        const prices = data.map(d => d.close);
        const result = {};

        periods.forEach(period => {
            result[period] = [];
            for (let i = period - 1; i < prices.length; i++) {
                const slice = prices.slice(i - period + 1, i + 1);
                const sma = slice.reduce((sum, price) => sum + price, 0) / period;
                result[period].push({
                    timestamp: data[i].timestamp,
                    value: sma
                });
            }
        });

        return result;
    }

    /**
     * Calcul d'EMA (fonction utilitaire)
     */
    calculateEMAValues(prices, period) {
        const ema = [];
        const multiplier = 2 / (period + 1);

        // Premier point (SMA)
        let sum = 0;
        for (let i = 0; i < period; i++) {
            sum += prices[i];
        }
        ema[period - 1] = sum / period;

        // Points suivants
        for (let i = period; i < prices.length; i++) {
            ema[i] = (prices[i] - ema[i - 1]) * multiplier + ema[i - 1];
        }

        return ema;
    }

    /**
     * Récupération des données de marché
     */
    async getMarketData() {
        // Simulation de données - à remplacer par un appel API réel
        const now = Date.now();
        const data = [];
        
        for (let i = 0; i < 200; i++) {
            const timestamp = now - (200 - i) * 24 * 60 * 60 * 1000; // 200 jours
            const basePrice = 100 + Math.sin(i / 10) * 20;
            const volatility = 2;
            
            const open = basePrice + (Math.random() - 0.5) * volatility;
            const close = open + (Math.random() - 0.5) * volatility;
            const high = Math.max(open, close) + Math.random() * volatility;
            const low = Math.min(open, close) - Math.random() * volatility;
            const volume = Math.floor(Math.random() * 1000000) + 100000;
            
            data.push({
                timestamp,
                open,
                high,
                low,
                close,
                volume
            });
        }
        
        return data;
    }

    /**
     * Obtention des paramètres par défaut d'un indicateur
     */
    getIndicatorSettings(type) {
        return { ...this.settings[type] };
    }

    /**
     * Obtention du nom d'un indicateur
     */
    getIndicatorName(type) {
        const names = {
            rsi: 'RSI',
            macd: 'MACD',
            bollinger: 'Bandes de Bollinger',
            sma: 'Moyennes Mobiles',
            ema: 'Moyennes Exponentielles',
            stochastic: 'Stochastique',
            adx: 'ADX',
            williams: 'Williams %R',
            atr: 'ATR',
            obv: 'OBV',
            vwap: 'VWAP',
            volume: 'Volume'
        };
        return names[type] || type.toUpperCase();
    }

    /**
     * Obtention de l'icône d'un indicateur
     */
    getIndicatorIcon(type) {
        const icons = {
            rsi: 'fas fa-wave-square',
            macd: 'fas fa-chart-bar',
            bollinger: 'fas fa-chart-area',
            sma: 'fas fa-chart-line',
            ema: 'fas fa-chart-line',
            stochastic: 'fas fa-wave-square',
            adx: 'fas fa-trending-up',
            williams: 'fas fa-chart-line',
            atr: 'fas fa-chart-area',
            obv: 'fas fa-chart-line',
            vwap: 'fas fa-chart-area',
            volume: 'fas fa-chart-bar'
        };
        return icons[type] || 'fas fa-chart-line';
    }

    /**
     * Formatage des paramètres d'un indicateur
     */
    formatSettings(type, settings) {
        switch (type) {
            case 'rsi':
                return `(${settings.period})`;
            case 'macd':
                return `(${settings.fastPeriod}, ${settings.slowPeriod}, ${settings.signalPeriod})`;
            case 'bollinger':
                return `(${settings.period}, ${settings.stdDev})`;
            case 'sma':
            case 'ema':
                return `(${settings.periods.join(', ')})`;
            default:
                return settings.period ? `(${settings.period})` : '';
        }
    }

    /**
     * Obtention de la hauteur d'un indicateur
     */
    getIndicatorHeight(type) {
        const heights = {
            volume: 100,
            rsi: 120,
            macd: 120,
            stochastic: 120,
            williams: 120,
            atr: 100,
            obv: 100,
            vwap: 100,
            adx: 120
        };
        return heights[type] || 150;
    }

    /**
     * Suppression d'un indicateur
     */
    removeIndicator(indicatorId) {
        const indicator = this.indicators.get(indicatorId);
        if (!indicator) return;

        // Destruction du graphique
        if (indicator.chart) {
            indicator.chart.destroy();
        }

        // Suppression du panneau
        if (indicator.panel) {
            indicator.panel.remove();
        }

        // Suppression de la map
        this.indicators.delete(indicatorId);

        // Mise à jour de la légende
        this.updateLegend();
    }

    /**
     * Édition d'un indicateur
     */
    editIndicator(indicatorId) {
        const indicator = this.indicators.get(indicatorId);
        if (!indicator) return;

        this.showIndicatorSettings(indicator.type, indicator.settings)
            .then(newSettings => {
                indicator.settings = { ...indicator.settings, ...newSettings };
                this.calculateAndDisplayIndicator(indicatorId);
            });
    }

    /**
     * Réinitialisation de tous les indicateurs
     */
    resetAllIndicators() {
        this.indicators.forEach((indicator, id) => {
            this.removeIndicator(id);
        });
        this.loadDefaultIndicators();
    }

    /**
     * Chargement d'un preset d'indicateurs
     */
    loadPreset(presetName) {
        this.resetAllIndicators();

        switch (presetName) {
            case 'trend':
                this.addIndicator('sma', { periods: [20, 50, 200] });
                this.addIndicator('bollinger', { period: 20, stdDev: 2 });
                this.addIndicator('adx', { period: 14 });
                break;

            case 'momentum':
                this.addIndicator('rsi', { period: 14 });
                this.addIndicator('macd', { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 });
                this.addIndicator('stochastic', { kPeriod: 14, dPeriod: 3, slowing: 3 });
                break;

            case 'volatility':
                this.addIndicator('bollinger', { period: 20, stdDev: 2 });
                this.addIndicator('atr', { period: 14 });
                break;

            case 'volume':
                this.addIndicator('volume');
                this.addIndicator('obv');
                this.addIndicator('vwap');
                break;

            case 'full':
                this.addIndicator('sma', { periods: [20, 50] });
                this.addIndicator('rsi', { period: 14 });
                this.addIndicator('macd', { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 });
                this.addIndicator('bollinger', { period: 20, stdDev: 2 });
                this.addIndicator('volume');
                break;
        }
    }

    /**
     * Mise à jour de la légende
     */
    updateLegend() {
        const legend = document.getElementById('indicators-legend');
        if (!legend) return;

        const items = Array.from(this.indicators.values()).map(indicator => {
            return `
                <span class="legend-item">
                    <i class="${this.getIndicatorIcon(indicator.type)}"></i>
                    ${this.getIndicatorName(indicator.type)}
                    <small>${this.formatSettings(indicator.type, indicator.settings)}</small>
                </span>
            `;
        });

        legend.innerHTML = items.join('');
    }

    /**
     * Redimensionnement de tous les graphiques
     */
    resizeAllCharts() {
        this.indicators.forEach(indicator => {
            if (indicator.chart && indicator.chart.resize) {
                indicator.chart.resize();
            }
        });
    }

    /**
     * Création d'un graphique d'indicateur
     */
    createIndicatorChart(indicatorId, type, data, settings) {
        const canvas = document.getElementById(`chart_${indicatorId}`);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        
        // Configuration spécifique selon le type d'indicateur
        const config = this.getChartConfig(type, data, settings);
        
        return new Chart(ctx, config);
    }

    /**
     * Configuration des graphiques selon le type d'indicateur
     */
    getChartConfig(type, data, settings) {
        const baseConfig = {
            type: 'line',
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
                        type: 'time',
                        display: true,
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                },
                elements: {
                    point: {
                        radius: 0
                    }
                }
            }
        };

        switch (type) {
            case 'rsi':
                return {
                    ...baseConfig,
                    data: {
                        datasets: [{
                            label: 'RSI',
                            data: data.map(d => ({ x: d.timestamp, y: d.value })),
                            borderColor: '#6366f1',
                            backgroundColor: 'rgba(99, 102, 241, 0.1)',
                            fill: false
                        }]
                    },
                    options: {
                        ...baseConfig.options,
                        scales: {
                            ...baseConfig.options.scales,
                            y: {
                                ...baseConfig.options.scales.y,
                                min: 0,
                                max: 100,
                                ticks: {
                                    callback: function(value) {
                                        if (value === settings.overbought || value === settings.oversold || value === 50) {
                                            return value;
                                        }
                                        return '';
                                    }
                                }
                            }
                        },
                        plugins: {
                            ...baseConfig.options.plugins,
                            annotation: {
                                annotations: {
                                    overbought: {
                                        type: 'line',
                                        yMin: settings.overbought,
                                        yMax: settings.overbought,
                                        borderColor: '#ef4444',
                                        borderWidth: 1,
                                        borderDash: [5, 5]
                                    },
                                    oversold: {
                                        type: 'line',
                                        yMin: settings.oversold,
                                        yMax: settings.oversold,
                                        borderColor: '#22c55e',
                                        borderWidth: 1,
                                        borderDash: [5, 5]
                                    }
                                }
                            }
                        }
                    }
                };

            case 'macd':
                return {
                    ...baseConfig,
                    type: 'line',
                    data: {
                        datasets: [
                            {
                                label: 'MACD',
                                data: data.map(d => ({ x: d.timestamp, y: d.macd })),
                                borderColor: '#6366f1',
                                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                                fill: false
                            },
                            {
                                label: 'Signal',
                                data: data.map(d => ({ x: d.timestamp, y: d.signal })),
                                borderColor: '#ef4444',
                                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                fill: false
                            },
                            {
                                label: 'Histogram',
                                type: 'bar',
                                data: data.map(d => ({ x: d.timestamp, y: d.histogram })),
                                backgroundColor: data.map(d => d.histogram >= 0 ? 'rgba(34, 197, 94, 0.5)' : 'rgba(239, 68, 68, 0.5)'),
                                borderColor: 'transparent'
                            }
                        ]
                    }
                };

            case 'volume':
                return {
                    ...baseConfig,
                    type: 'bar',
                    data: {
                        datasets: [{
                            label: 'Volume',
                            data: data.map(d => ({ x: d.timestamp, y: d.volume })),
                            backgroundColor: 'rgba(99, 102, 241, 0.6)',
                            borderColor: 'transparent'
                        }]
                    }
                };

            default:
                return {
                    ...baseConfig,
                    data: {
                        datasets: [{
                            label: type.toUpperCase(),
                            data: Array.isArray(data) ? data.map(d => ({ x: d.timestamp, y: d.value })) : [],
                            borderColor: '#6366f1',
                            backgroundColor: 'rgba(99, 102, 241, 0.1)',
                            fill: false
                        }]
                    }
                };
        }
    }

    /**
     * Affichage d'un indicateur
     */
    displayIndicator(indicatorId) {
        const indicator = this.indicators.get(indicatorId);
        if (!indicator || !indicator.chart) return;

        // Le graphique est déjà créé et affiché
        // Ici on peut ajouter des animations ou des effets
        indicator.panel.classList.add('indicator-loaded');
    }

    /**
     * Affichage d'une erreur d'indicateur
     */
    showIndicatorError(indicatorId, errorMessage) {
        const indicator = this.indicators.get(indicatorId);
        if (!indicator) return;

        const body = indicator.panel.querySelector('.indicator-body');
        body.innerHTML = `
            <div class="indicator-error">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Erreur lors du calcul de l'indicateur</p>
                <small>${errorMessage}</small>
            </div>
        `;
    }

    // Méthodes additionnelles pour les autres indicateurs
    calculateStochastic(data, kPeriod, dPeriod, slowing) {
        // Implémentation du Stochastique
        // ...
    }

    calculateADX(data, period) {
        // Implémentation de l'ADX
        // ...
    }

    calculateWilliamsR(data, period) {
        // Implémentation du Williams %R
        // ...
    }

    calculateATR(data, period) {
        // Implémentation de l'ATR
        // ...
    }

    calculateOBV(data) {
        // Implémentation de l'OBV
        // ...
    }

    calculateVWAP(data) {
        // Implémentation du VWAP
        // ...
    }

    extractVolume(data) {
        return data.map(d => ({
            timestamp: d.timestamp,
            volume: d.volume
        }));
    }
}

// Initialisation globale
let technicalIndicators;

document.addEventListener('DOMContentLoaded', () => {
    technicalIndicators = new TechnicalIndicators();
});