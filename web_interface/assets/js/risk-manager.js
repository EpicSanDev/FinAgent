/**
 * Risk Management Module
 * Gère l'évaluation des risques, les calculs VaR, les tests de stress et les alertes
 */

class RiskManager {
    constructor() {
        this.currentPortfolio = null;
        this.riskMetrics = {};
        this.varData = {};
        this.alertsData = [];
        this.stressScenarios = {};
        this.charts = {};
        
        this.init();
    }

    init() {
        this.initializeTabs();
        this.initializeEventListeners();
        this.loadRiskData();
        this.initializeCharts();
    }

    initializeTabs() {
        const tabButtons = document.querySelectorAll('.risk-tabs .tab-btn');
        const tabPanes = document.querySelectorAll('.risk-tabs .tab-pane');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.getAttribute('data-tab');
                
                // Remove active class from all buttons and panes
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabPanes.forEach(pane => pane.classList.remove('active'));
                
                // Add active class to clicked button and corresponding pane
                button.classList.add('active');
                const targetPane = document.getElementById(targetTab);
                if (targetPane) {
                    targetPane.classList.add('active');
                    this.onTabChange(targetTab);
                }
            });
        });
    }

    initializeEventListeners() {
        // Risk data refresh
        const refreshBtn = document.getElementById('refresh-risk-data');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshRiskData());
        }

        // VaR calculation
        const calculateVarBtn = document.getElementById('calculate-var');
        if (calculateVarBtn) {
            calculateVarBtn.addEventListener('click', () => this.calculateVaR());
        }

        // Stress testing scenarios
        const scenarioCards = document.querySelectorAll('.scenario-card');
        scenarioCards.forEach(card => {
            card.addEventListener('click', () => this.runStressTest(card.dataset.scenario));
        });

        // Custom stress test
        const customStressBtn = document.getElementById('run-custom-stress');
        if (customStressBtn) {
            customStressBtn.addEventListener('click', () => this.runCustomStressTest());
        }

        // Risk limits saving
        const saveLimitsBtn = document.getElementById('save-limits');
        if (saveLimitsBtn) {
            saveLimitsBtn.addEventListener('click', () => this.saveRiskLimits());
        }

        // Export risk report
        const exportBtn = document.getElementById('export-risk-report');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportRiskReport());
        }

        // Create new alert
        const createAlertBtn = document.getElementById('create-alert');
        if (createAlertBtn) {
            createAlertBtn.addEventListener('click', () => this.createNewAlert());
        }
    }

    onTabChange(tabName) {
        switch (tabName) {
            case 'risk-dashboard':
                this.updateRiskDashboard();
                break;
            case 'var-analysis':
                this.updateVarAnalysis();
                break;
            case 'stress-testing':
                this.updateStressTesting();
                break;
            case 'risk-alerts':
                this.updateRiskAlerts();
                break;
            case 'risk-limits':
                this.updateRiskLimits();
                break;
        }
    }

    async loadRiskData() {
        try {
            // Simuler le chargement des données de risque
            this.currentPortfolio = await this.fetchPortfolioData();
            this.riskMetrics = await this.calculateRiskMetrics();
            this.updateRiskOverview();
        } catch (error) {
            console.error('Erreur lors du chargement des données de risque:', error);
            this.showNotification('Erreur lors du chargement des données', 'error');
        }
    }

    async fetchPortfolioData() {
        // Simulation de données de portefeuille
        return {
            totalValue: 150000,
            positions: [
                { symbol: 'AAPL', value: 25000, weight: 16.7 },
                { symbol: 'MSFT', value: 22000, weight: 14.7 },
                { symbol: 'GOOGL', value: 20000, weight: 13.3 },
                { symbol: 'AMZN', value: 18000, weight: 12.0 },
                { symbol: 'TSLA', value: 15000, weight: 10.0 }
            ],
            currency: 'EUR'
        };
    }

    async calculateRiskMetrics() {
        // Simulation de calculs de métriques de risque
        return {
            overallRiskScore: 7.2,
            riskLevel: 'moderate',
            var1Day95: -2340,
            var10Day99: -7890,
            volatilityAnnualized: 18.5,
            averageCorrelation: 0.72,
            sharpeRatio: 1.34,
            maxDrawdown: -12.8,
            beta: 1.18,
            alpha: 2.7,
            expectedShortfall: -11240
        };
    }

    updateRiskOverview() {
        // Mettre à jour les cartes de risque principales
        const overallScoreEl = document.getElementById('overall-risk-score');
        if (overallScoreEl) {
            const scoreValue = overallScoreEl.querySelector('.score-value');
            if (scoreValue) {
                scoreValue.textContent = this.riskMetrics.overallRiskScore.toFixed(1);
            }
        }

        const riskLevelEl = document.getElementById('overall-risk-level');
        if (riskLevelEl) {
            riskLevelEl.className = `risk-level ${this.riskMetrics.riskLevel}`;
            riskLevelEl.textContent = this.getRiskLevelText(this.riskMetrics.riskLevel);
        }

        // Mettre à jour les valeurs VaR
        const varCards = document.querySelectorAll('.var-item .var-value');
        if (varCards.length >= 2) {
            varCards[0].textContent = this.formatCurrency(this.riskMetrics.var1Day95);
            varCards[1].textContent = this.formatCurrency(this.riskMetrics.var10Day99);
        }

        // Mettre à jour la volatilité
        const volatilityValue = document.querySelector('.volatility-value');
        if (volatilityValue) {
            volatilityValue.textContent = `${this.riskMetrics.volatilityAnnualized}%`;
        }

        // Mettre à jour la corrélation
        const correlationNumber = document.querySelector('.correlation-number');
        if (correlationNumber) {
            correlationNumber.textContent = this.riskMetrics.averageCorrelation.toFixed(2);
        }
    }

    updateRiskDashboard() {
        // Mettre à jour les métriques de risque détaillées
        const metrics = [
            { selector: '.risk-metric-card:nth-child(1) .metric-value', value: this.riskMetrics.sharpeRatio.toFixed(2), class: 'positive' },
            { selector: '.risk-metric-card:nth-child(2) .metric-value', value: `${this.riskMetrics.maxDrawdown}%`, class: 'negative' },
            { selector: '.risk-metric-card:nth-child(3) .metric-value', value: this.riskMetrics.beta.toFixed(2), class: '' },
            { selector: '.risk-metric-card:nth-child(4) .metric-value', value: `${this.riskMetrics.alpha}%`, class: 'positive' }
        ];

        metrics.forEach(metric => {
            const element = document.querySelector(metric.selector);
            if (element) {
                element.textContent = metric.value;
                element.className = `metric-value ${metric.class}`;
            }
        });

        // Initialiser les graphiques si nécessaire
        if (!this.charts.varEvolution) {
            this.initializeVarEvolutionChart();
        }
        if (!this.charts.returnsDistribution) {
            this.initializeReturnsDistributionChart();
        }
    }

    updateVarAnalysis() {
        // Mettre à jour l'analyse VaR
        const calculatedVarEl = document.getElementById('calculated-var');
        if (calculatedVarEl) {
            calculatedVarEl.textContent = this.formatCurrency(this.riskMetrics.var10Day99);
        }

        const expectedShortfallEl = document.getElementById('expected-shortfall');
        if (expectedShortfallEl) {
            expectedShortfallEl.textContent = this.formatCurrency(this.riskMetrics.expectedShortfall);
        }

        // Initialiser les graphiques VaR si nécessaire
        if (!this.charts.varDistribution) {
            this.initializeVarDistributionChart();
        }
        if (!this.charts.varBacktesting) {
            this.initializeVarBacktestingChart();
        }
    }

    updateStressTesting() {
        // Les scénarios sont déjà affichés dans le HTML
        // Masquer les résultats initialement
        const stressResults = document.getElementById('stress-results');
        if (stressResults) {
            stressResults.style.display = 'none';
        }
    }

    updateRiskAlerts() {
        // Les alertes sont déjà affichées dans le HTML
        // Mettre à jour les compteurs
        this.updateAlertCounters();
    }

    updateRiskLimits() {
        // Les limites sont déjà configurées dans le HTML
        // Mettre à jour les barres d'utilisation
        this.updateLimitUsageBars();
    }

    async calculateVaR() {
        const period = document.getElementById('var-period')?.value || '10';
        const confidence = document.getElementById('var-confidence')?.value || '0.95';
        const method = document.getElementById('var-method')?.value || 'historical';

        try {
            // Simulation du calcul VaR
            const varResult = await this.performVarCalculation(period, confidence, method);
            
            // Mettre à jour les résultats
            const calculatedVarEl = document.getElementById('calculated-var');
            if (calculatedVarEl) {
                calculatedVarEl.textContent = this.formatCurrency(varResult.var);
            }

            const expectedShortfallEl = document.getElementById('expected-shortfall');
            if (expectedShortfallEl) {
                expectedShortfallEl.textContent = this.formatCurrency(varResult.expectedShortfall);
            }

            // Mettre à jour les graphiques
            this.updateVarCharts(varResult);
            
            this.showNotification('Calcul VaR terminé avec succès', 'success');
        } catch (error) {
            console.error('Erreur lors du calcul VaR:', error);
            this.showNotification('Erreur lors du calcul VaR', 'error');
        }
    }

    async performVarCalculation(period, confidence, method) {
        // Simulation de calcul VaR
        const baseVar = -7890;
        const periodMultiplier = Math.sqrt(parseInt(period) / 10);
        const confidenceMultiplier = confidence === '0.99' ? 1.3 : confidence === '0.90' ? 0.8 : 1.0;
        
        return {
            var: baseVar * periodMultiplier * confidenceMultiplier,
            expectedShortfall: baseVar * periodMultiplier * confidenceMultiplier * 1.4,
            method: method,
            period: period,
            confidence: confidence
        };
    }

    async runStressTest(scenario) {
        try {
            // Simulation du test de stress
            const result = await this.performStressTest(scenario);
            
            // Afficher les résultats
            this.displayStressTestResults(result);
            
            this.showNotification(`Test de stress "${scenario}" terminé`, 'success');
        } catch (error) {
            console.error('Erreur lors du test de stress:', error);
            this.showNotification('Erreur lors du test de stress', 'error');
        }
    }

    async performStressTest(scenario) {
        const scenarios = {
            'market-crash': {
                name: 'Krach Boursier',
                totalLoss: -45670,
                lossPercentage: -30.4,
                impactByAsset: [
                    { symbol: 'AAPL', impact: -7500 },
                    { symbol: 'MSFT', impact: -6600 },
                    { symbol: 'GOOGL', impact: -6000 },
                    { symbol: 'AMZN', impact: -5400 },
                    { symbol: 'TSLA', impact: -4500 }
                ]
            },
            'interest-rate': {
                name: 'Hausse des Taux',
                totalLoss: -12890,
                lossPercentage: -8.6,
                impactByAsset: [
                    { symbol: 'AAPL', impact: -2580 },
                    { symbol: 'MSFT', impact: -2320 },
                    { symbol: 'GOOGL', impact: -2100 },
                    { symbol: 'AMZN', impact: -1890 },
                    { symbol: 'TSLA', impact: -1500 }
                ]
            },
            'currency-crisis': {
                name: 'Crise Monétaire',
                totalLoss: -8450,
                lossPercentage: -5.6,
                impactByAsset: [
                    { symbol: 'AAPL', impact: -1690 },
                    { symbol: 'MSFT', impact: -1520 },
                    { symbol: 'GOOGL', impact: -1380 },
                    { symbol: 'AMZN', impact: -1240 },
                    { symbol: 'TSLA', impact: -1040 }
                ]
            },
            'volatility-spike': {
                name: 'Pic de Volatilité',
                totalLoss: -23120,
                lossPercentage: -15.4,
                impactByAsset: [
                    { symbol: 'AAPL', impact: -4624 },
                    { symbol: 'MSFT', impact: -4157 },
                    { symbol: 'GOOGL', impact: -3768 },
                    { symbol: 'AMZN', impact: -3394 },
                    { symbol: 'TSLA', impact: -2831 }
                ]
            }
        };

        return scenarios[scenario] || scenarios['market-crash'];
    }

    displayStressTestResults(result) {
        const stressResults = document.getElementById('stress-results');
        if (!stressResults) return;

        // Mettre à jour les données
        const selectedScenario = document.getElementById('selected-scenario');
        if (selectedScenario) {
            selectedScenario.textContent = result.name;
        }

        const totalLoss = document.getElementById('total-loss');
        if (totalLoss) {
            totalLoss.textContent = this.formatCurrency(result.totalLoss);
        }

        const lossPercentage = document.getElementById('loss-percentage');
        if (lossPercentage) {
            lossPercentage.textContent = `${result.lossPercentage}%`;
        }

        // Afficher les résultats
        stressResults.style.display = 'block';

        // Mettre à jour le graphique d'impact
        this.updateStressImpactChart(result);
    }

    async runCustomStressTest() {
        const cac40Change = parseFloat(document.getElementById('cac40-change')?.value || '0');
        const usdeurChange = parseFloat(document.getElementById('usdeur-change')?.value || '0');
        const rateChange = parseFloat(document.getElementById('rate-change')?.value || '0');
        const vixChange = parseFloat(document.getElementById('vix-change')?.value || '0');

        try {
            // Simulation du test personnalisé
            const result = await this.performCustomStressTest({
                cac40: cac40Change,
                usdeur: usdeurChange,
                rate: rateChange,
                vix: vixChange
            });

            this.displayStressTestResults(result);
            this.showNotification('Test de stress personnalisé terminé', 'success');
        } catch (error) {
            console.error('Erreur lors du test de stress personnalisé:', error);
            this.showNotification('Erreur lors du test de stress personnalisé', 'error');
        }
    }

    async performCustomStressTest(parameters) {
        // Simulation de calcul personnalisé basé sur les paramètres
        const baseImpact = (parameters.cac40 * -500) + (parameters.usdeur * -200) + 
                          (parameters.rate * -100) + (parameters.vix * -150);
        
        const totalLoss = Math.round(baseImpact);
        const lossPercentage = (totalLoss / this.currentPortfolio.totalValue * 100).toFixed(1);

        return {
            name: 'Test Personnalisé',
            totalLoss: totalLoss,
            lossPercentage: parseFloat(lossPercentage),
            impactByAsset: this.currentPortfolio.positions.map(pos => ({
                symbol: pos.symbol,
                impact: Math.round(totalLoss * pos.weight / 100)
            }))
        };
    }

    async refreshRiskData() {
        try {
            this.showNotification('Actualisation des données...', 'info');
            
            // Simuler le rechargement des données
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            await this.loadRiskData();
            this.updateAllCharts();
            
            this.showNotification('Données actualisées avec succès', 'success');
        } catch (error) {
            console.error('Erreur lors de l\'actualisation:', error);
            this.showNotification('Erreur lors de l\'actualisation', 'error');
        }
    }

    saveRiskLimits() {
        try {
            // Récupérer les valeurs des limites
            const limits = this.collectRiskLimits();
            
            // Simulation de sauvegarde
            console.log('Sauvegarde des limites de risque:', limits);
            
            this.showNotification('Limites de risque sauvegardées', 'success');
        } catch (error) {
            console.error('Erreur lors de la sauvegarde:', error);
            this.showNotification('Erreur lors de la sauvegarde', 'error');
        }
    }

    collectRiskLimits() {
        const limitInputs = document.querySelectorAll('.limit-input-group input');
        const limits = {};
        
        limitInputs.forEach((input, index) => {
            const label = input.closest('.limit-item').querySelector('label').textContent;
            limits[label] = parseFloat(input.value);
        });
        
        return limits;
    }

    exportRiskReport() {
        try {
            // Simulation d'export de rapport
            const reportData = {
                timestamp: new Date().toISOString(),
                portfolio: this.currentPortfolio,
                riskMetrics: this.riskMetrics,
                varData: this.varData
            };
            
            // Créer un blob et déclencher le téléchargement
            const blob = new Blob([JSON.stringify(reportData, null, 2)], 
                                { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `risk-report-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showNotification('Rapport exporté avec succès', 'success');
        } catch (error) {
            console.error('Erreur lors de l\'export:', error);
            this.showNotification('Erreur lors de l\'export', 'error');
        }
    }

    createNewAlert() {
        // Simulation de création d'alerte
        const alertModal = this.createAlertModal();
        document.body.appendChild(alertModal);
        alertModal.style.display = 'block';
    }

    createAlertModal() {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Nouvelle Alerte de Risque</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Type d'Alerte</label>
                        <select id="alert-type">
                            <option value="var">VaR Dépassé</option>
                            <option value="volatility">Volatilité Élevée</option>
                            <option value="correlation">Corrélation Élevée</option>
                            <option value="drawdown">Drawdown Dépassé</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Seuil</label>
                        <input type="number" id="alert-threshold" step="0.01">
                    </div>
                    <div class="form-group">
                        <label>Notification</label>
                        <select id="alert-notification">
                            <option value="email">Email</option>
                            <option value="push">Push</option>
                            <option value="sms">SMS</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" id="save-alert">Créer Alerte</button>
                    <button class="btn btn-outline" id="cancel-alert">Annuler</button>
                </div>
            </div>
        `;

        // Ajouter les événements
        modal.querySelector('.modal-close').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        modal.querySelector('#cancel-alert').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        modal.querySelector('#save-alert').addEventListener('click', () => {
            this.saveNewAlert(modal);
        });

        return modal;
    }

    saveNewAlert(modal) {
        const type = modal.querySelector('#alert-type').value;
        const threshold = modal.querySelector('#alert-threshold').value;
        const notification = modal.querySelector('#alert-notification').value;

        // Simulation de sauvegarde
        console.log('Nouvelle alerte créée:', { type, threshold, notification });
        
        this.showNotification('Alerte créée avec succès', 'success');
        document.body.removeChild(modal);
    }

    // Méthodes pour les graphiques
    initializeCharts() {
        // Les graphiques seront initialisés lors du changement d'onglet
    }

    initializeVarEvolutionChart() {
        const ctx = document.getElementById('var-evolution-chart');
        if (!ctx) return;

        this.charts.varEvolution = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.generateDateLabels(30),
                datasets: [{
                    label: 'VaR 1-jour (95%)',
                    data: this.generateVarData(30),
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return new Intl.NumberFormat('fr-FR', {
                                    style: 'currency',
                                    currency: 'EUR',
                                    minimumFractionDigits: 0
                                }).format(value);
                            }
                        }
                    }
                }
            }
        });
    }

    initializeReturnsDistributionChart() {
        const ctx = document.getElementById('returns-distribution-chart');
        if (!ctx) return;

        this.charts.returnsDistribution = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: this.generateReturnBins(),
                datasets: [{
                    label: 'Fréquence',
                    data: this.generateReturnDistribution(),
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: 'rgb(59, 130, 246)',
                    borderWidth: 1
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
                        title: {
                            display: true,
                            text: 'Rendements (%)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Fréquence'
                        }
                    }
                }
            }
        });
    }

    initializeVarDistributionChart() {
        const ctx = document.getElementById('var-distribution-chart');
        if (!ctx) return;

        const data = this.generateVarDistributionData();
        
        this.charts.varDistribution = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Distribution P&L',
                    data: data.distribution,
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'VaR 95%',
                    data: data.varLine,
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderDash: [5, 5],
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
    }

    initializeVarBacktestingChart() {
        const ctx = document.getElementById('var-backtesting-chart');
        if (!ctx) return;

        const data = this.generateBacktestingData();
        
        this.charts.varBacktesting = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'P&L Réalisé',
                    data: data.actualPnL,
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    pointBackgroundColor: data.actualPnL.map(val => 
                        val < data.varThreshold ? 'rgb(239, 68, 68)' : 'rgb(34, 197, 94)'
                    ),
                    pointRadius: 3
                }, {
                    label: 'VaR Seuil',
                    data: new Array(data.labels.length).fill(data.varThreshold),
                    borderColor: 'rgb(239, 68, 68)',
                    borderDash: [5, 5],
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        ticks: {
                            callback: function(value) {
                                return new Intl.NumberFormat('fr-FR', {
                                    style: 'currency',
                                    currency: 'EUR',
                                    minimumFractionDigits: 0
                                }).format(value);
                            }
                        }
                    }
                }
            }
        });
    }

    updateStressImpactChart(result) {
        const ctx = document.getElementById('stress-impact-chart');
        if (!ctx) return;

        if (this.charts.stressImpact) {
            this.charts.stressImpact.destroy();
        }

        this.charts.stressImpact = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: result.impactByAsset.map(item => item.symbol),
                datasets: [{
                    label: 'Impact (€)',
                    data: result.impactByAsset.map(item => item.impact),
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    borderColor: 'rgb(239, 68, 68)',
                    borderWidth: 1
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
                    y: {
                        ticks: {
                            callback: function(value) {
                                return new Intl.NumberFormat('fr-FR', {
                                    style: 'currency',
                                    currency: 'EUR',
                                    minimumFractionDigits: 0
                                }).format(value);
                            }
                        }
                    }
                }
            }
        });
    }

    updateVarCharts(varResult) {
        // Mettre à jour les graphiques VaR avec les nouveaux résultats
        if (this.charts.varDistribution) {
            this.charts.varDistribution.destroy();
            this.initializeVarDistributionChart();
        }
        
        if (this.charts.varBacktesting) {
            this.charts.varBacktesting.destroy();
            this.initializeVarBacktestingChart();
        }
    }

    updateAllCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.update === 'function') {
                chart.update();
            }
        });
    }

    updateAlertCounters() {
        // Simulation de mise à jour des compteurs d'alertes
        const criticalCount = document.querySelector('.alert-summary-card.critical .alert-count');
        const warningCount = document.querySelector('.alert-summary-card.warning .alert-count');
        const infoCount = document.querySelector('.alert-summary-card.info .alert-count');

        if (criticalCount) criticalCount.textContent = '2';
        if (warningCount) warningCount.textContent = '5';
        if (infoCount) infoCount.textContent = '3';
    }

    updateLimitUsageBars() {
        const usageBars = document.querySelectorAll('.usage-fill');
        const usagePercentages = [47, 53, 74, 85]; // Exemples de pourcentages d'utilisation

        usageBars.forEach((bar, index) => {
            if (index < usagePercentages.length) {
                bar.style.width = `${usagePercentages[index]}%`;
                
                // Changer la couleur selon le niveau d'utilisation
                if (usagePercentages[index] > 80) {
                    bar.style.background = 'var(--error-color)';
                } else if (usagePercentages[index] > 60) {
                    bar.style.background = 'var(--warning-color)';
                } else {
                    bar.style.background = 'var(--primary-color)';
                }
            }
        });
    }

    // Méthodes utilitaires
    getRiskLevelText(level) {
        const levels = {
            'low': 'Risque Faible',
            'moderate': 'Risque Modéré',
            'high': 'Risque Élevé'
        };
        return levels[level] || 'Inconnu';
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR',
            minimumFractionDigits: 0
        }).format(amount);
    }

    generateDateLabels(days) {
        const labels = [];
        const today = new Date();
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' }));
        }
        return labels;
    }

    generateVarData(days) {
        const data = [];
        for (let i = 0; i < days; i++) {
            data.push(-2000 - Math.random() * 1000 - Math.sin(i / 5) * 500);
        }
        return data;
    }

    generateReturnBins() {
        const bins = [];
        for (let i = -5; i <= 5; i += 0.5) {
            bins.push(`${i.toFixed(1)}%`);
        }
        return bins;
    }

    generateReturnDistribution() {
        // Distribution normale simulée
        const data = [];
        const bins = this.generateReturnBins();
        for (let i = 0; i < bins.length; i++) {
            const x = (i - bins.length / 2) / 2;
            data.push(Math.exp(-0.5 * x * x) * (Math.random() * 0.3 + 0.7));
        }
        return data;
    }

    generateVarDistributionData() {
        const labels = [];
        const distribution = [];
        const varThreshold = -7890;
        
        for (let i = -15000; i <= 5000; i += 500) {
            labels.push(i);
            const normalized = (i + 5000) / 20000;
            distribution.push(Math.exp(-0.5 * Math.pow((normalized - 0.6) * 6, 2)) * 100);
        }
        
        const varLine = labels.map(val => val <= varThreshold ? 
            distribution[labels.indexOf(val)] : null);
        
        return { labels, distribution, varLine };
    }

    generateBacktestingData() {
        const labels = this.generateDateLabels(250);
        const varThreshold = -2340;
        const actualPnL = [];
        
        for (let i = 0; i < 250; i++) {
            // Génération de P&L avec quelques exceptions
            let pnl = (Math.random() - 0.3) * 3000;
            if (Math.random() < 0.05) { // 5% d'exceptions
                pnl = varThreshold - Math.random() * 1000;
            }
            actualPnL.push(pnl);
        }
        
        return { labels, actualPnL, varThreshold };
    }

    showNotification(message, type = 'info') {
        // Utiliser le système de notifications existant
        if (window.showNotification) {
            window.showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    destroy() {
        // Nettoyer les graphiques
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}

// Initialiser le gestionnaire de risques quand la page est chargée
document.addEventListener('DOMContentLoaded', () => {
    window.riskManager = new RiskManager();
});

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RiskManager;
}