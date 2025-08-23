/**
 * Portfolio Charts System
 * Système de graphiques pour l'analyse de portefeuille
 */

class PortfolioCharts {
    constructor() {
        this.charts = new Map();
        this.colors = {
            primary: '#3b82f6',
            success: '#10b981',
            danger: '#ef4444',
            warning: '#f59e0b',
            info: '#06b6d4',
            secondary: '#6b7280',
            light: '#f3f4f6',
            dark: '#1f2937'
        };
        this.chartDefaults = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        };
    }

    /**
     * Crée le graphique d'évolution de la valeur du portefeuille
     */
    createPortfolioValueChart(canvasId, data, period = '1M') {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        
        // Détruire le graphique existant s'il existe
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const chartData = this.generatePortfolioValueData(period);
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Valeur du Portefeuille',
                    data: chartData.portfolioValue,
                    borderColor: this.colors.primary,
                    backgroundColor: this.colors.primary + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Benchmark (S&P 500)',
                    data: chartData.benchmark,
                    borderColor: this.colors.secondary,
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.4
                }]
            },
            options: {
                ...this.chartDefaults,
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return new Intl.NumberFormat('fr-FR', {
                                    style: 'currency',
                                    currency: 'USD'
                                }).format(value);
                            }
                        }
                    },
                    x: {
                        type: 'time',
                        time: {
                            displayFormats: {
                                day: 'MMM dd',
                                week: 'MMM dd',
                                month: 'MMM yyyy'
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + 
                                    new Intl.NumberFormat('fr-FR', {
                                        style: 'currency',
                                        currency: 'USD'
                                    }).format(context.parsed.y);
                            }
                        }
                    }
                }
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Crée le graphique de drawdown
     */
    createDrawdownChart(canvasId, period = '1M') {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const chartData = this.generateDrawdownData(period);
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Drawdown (%)',
                    data: chartData.drawdown,
                    borderColor: this.colors.danger,
                    backgroundColor: this.colors.danger + '20',
                    borderWidth: 2,
                    fill: 'origin',
                    tension: 0.4
                }]
            },
            options: {
                ...this.chartDefaults,
                scales: {
                    y: {
                        max: 0,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    },
                    x: {
                        type: 'time',
                        time: {
                            displayFormats: {
                                day: 'MMM dd',
                                week: 'MMM dd',
                                month: 'MMM yyyy'
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Drawdown: ' + context.parsed.y.toFixed(2) + '%';
                            }
                        }
                    }
                }
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Crée le graphique de comparaison avec benchmark
     */
    createBenchmarkComparisonChart(canvasId, benchmark = 'SPY', period = '1M') {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const chartData = this.generateBenchmarkComparisonData(benchmark, period);
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Portfolio (Rendement Cumulé)',
                    data: chartData.portfolioReturns,
                    borderColor: this.colors.primary,
                    backgroundColor: 'transparent',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4
                }, {
                    label: `${benchmark} (Rendement Cumulé)`,
                    data: chartData.benchmarkReturns,
                    borderColor: this.colors.secondary,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                }]
            },
            options: {
                ...this.chartDefaults,
                scales: {
                    y: {
                        ticks: {
                            callback: function(value) {
                                return (value >= 0 ? '+' : '') + value.toFixed(1) + '%';
                            }
                        }
                    },
                    x: {
                        type: 'time',
                        time: {
                            displayFormats: {
                                day: 'MMM dd',
                                week: 'MMM dd',
                                month: 'MMM yyyy'
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + 
                                    (context.parsed.y >= 0 ? '+' : '') + 
                                    context.parsed.y.toFixed(2) + '%';
                            }
                        }
                    }
                }
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Crée le graphique d'allocation actuelle (pie chart)
     */
    createCurrentAllocationChart(canvasId, positions) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const chartData = this.prepareAllocationData(positions);
        
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.values,
                    backgroundColor: this.generateColors(chartData.labels.length),
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                ...this.chartDefaults,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'right'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((sum, val) => sum + val, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return context.label + ': ' + percentage + '%';
                            }
                        }
                    }
                }
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Crée le graphique d'allocation cible (pie chart)
     */
    createTargetAllocationChart(canvasId, targets) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: targets.map(t => t.symbol),
                datasets: [{
                    data: targets.map(t => t.target),
                    backgroundColor: this.generateColors(targets.length),
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                ...this.chartDefaults,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'right'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed + '%';
                            }
                        }
                    }
                }
            }
        });

        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Crée le graphique de corrélation (heatmap)
     */
    createCorrelationMatrix(containerId, positions) {
        const container = document.getElementById(containerId);
        if (!container) return null;

        const correlationData = this.generateCorrelationData(positions);
        
        // Créer la heatmap de corrélation
        container.innerHTML = '';
        
        const table = document.createElement('table');
        table.className = 'correlation-matrix';
        
        // En-tête
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.appendChild(document.createElement('th')); // Cellule vide
        
        correlationData.symbols.forEach(symbol => {
            const th = document.createElement('th');
            th.textContent = symbol;
            headerRow.appendChild(th);
        });
        
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Corps
        const tbody = document.createElement('tbody');
        
        correlationData.matrix.forEach((row, i) => {
            const tr = document.createElement('tr');
            
            // Label de ligne
            const th = document.createElement('th');
            th.textContent = correlationData.symbols[i];
            tr.appendChild(th);
            
            // Cellules de corrélation
            row.forEach((correlation, j) => {
                const td = document.createElement('td');
                td.textContent = correlation.toFixed(2);
                td.className = this.getCorrelationClass(correlation);
                td.style.backgroundColor = this.getCorrelationColor(correlation);
                tr.appendChild(td);
            });
            
            tbody.appendChild(tr);
        });
        
        table.appendChild(tbody);
        container.appendChild(table);
        
        return table;
    }

    /**
     * Génère des données simulées pour l'évolution du portefeuille
     */
    generatePortfolioValueData(period) {
        const now = new Date();
        const points = this.getPeriodPoints(period);
        const startValue = 100000;
        
        const labels = [];
        const portfolioValue = [];
        const benchmark = [];
        
        for (let i = 0; i < points; i++) {
            const date = new Date(now.getTime() - (points - i - 1) * this.getPeriodInterval(period));
            labels.push(date);
            
            // Simulation d'évolution du portefeuille (tendance positive avec volatilité)
            const portfolioGrowth = Math.random() * 0.001 + 0.0005; // +0.05% à +0.15% par période
            const portfolioVolatility = (Math.random() - 0.5) * 0.02; // ±1% de volatilité
            const portfolioReturn = portfolioGrowth + portfolioVolatility;
            
            const portfolioVal = i === 0 ? startValue : portfolioValue[i-1] * (1 + portfolioReturn);
            portfolioValue.push(portfolioVal);
            
            // Benchmark (légèrement moins performant mais plus stable)
            const benchmarkGrowth = Math.random() * 0.0008 + 0.0003; // +0.03% à +0.11% par période
            const benchmarkVolatility = (Math.random() - 0.5) * 0.015; // ±0.75% de volatilité
            const benchmarkReturn = benchmarkGrowth + benchmarkVolatility;
            
            const benchmarkVal = i === 0 ? startValue : benchmark[i-1] * (1 + benchmarkReturn);
            benchmark.push(benchmarkVal);
        }
        
        return { labels, portfolioValue, benchmark };
    }

    /**
     * Génère des données de drawdown
     */
    generateDrawdownData(period) {
        const portfolioData = this.generatePortfolioValueData(period);
        const labels = portfolioData.labels;
        const values = portfolioData.portfolioValue;
        
        const drawdown = [];
        let peak = values[0];
        
        values.forEach(value => {
            if (value > peak) {
                peak = value;
            }
            const dd = ((value - peak) / peak) * 100;
            drawdown.push(dd);
        });
        
        return { labels, drawdown };
    }

    /**
     * Génère des données de comparaison avec benchmark
     */
    generateBenchmarkComparisonData(benchmark, period) {
        const data = this.generatePortfolioValueData(period);
        const labels = data.labels;
        
        const portfolioReturns = [];
        const benchmarkReturns = [];
        
        const portfolioStart = data.portfolioValue[0];
        const benchmarkStart = data.benchmark[0];
        
        data.portfolioValue.forEach(value => {
            const return_ = ((value - portfolioStart) / portfolioStart) * 100;
            portfolioReturns.push(return_);
        });
        
        data.benchmark.forEach(value => {
            const return_ = ((value - benchmarkStart) / benchmarkStart) * 100;
            benchmarkReturns.push(return_);
        });
        
        return { labels, portfolioReturns, benchmarkReturns };
    }

    /**
     * Prépare les données d'allocation
     */
    prepareAllocationData(positions) {
        const labels = positions.map(p => p.symbol);
        const values = positions.map(p => p.weight);
        
        return { labels, values };
    }

    /**
     * Génère des données de corrélation simulées
     */
    generateCorrelationData(positions) {
        const symbols = positions.map(p => p.symbol);
        const matrix = [];
        
        symbols.forEach((symbol1, i) => {
            const row = [];
            symbols.forEach((symbol2, j) => {
                if (i === j) {
                    row.push(1.0); // Corrélation parfaite avec soi-même
                } else {
                    // Corrélation simulée basée sur le secteur
                    const correlation = this.simulateCorrelation(
                        positions[i].sector, 
                        positions[j].sector
                    );
                    row.push(correlation);
                }
            });
            matrix.push(row);
        });
        
        return { symbols, matrix };
    }

    /**
     * Simule une corrélation basée sur les secteurs
     */
    simulateCorrelation(sector1, sector2) {
        if (sector1 === sector2) {
            // Même secteur: corrélation élevée (0.6 à 0.9)
            return 0.6 + Math.random() * 0.3;
        } else if (
            (sector1 === 'Technology' && sector2 === 'ETF') ||
            (sector1 === 'ETF' && sector2 === 'Technology')
        ) {
            // Tech et ETF: corrélation modérée (0.3 à 0.7)
            return 0.3 + Math.random() * 0.4;
        } else {
            // Secteurs différents: corrélation faible (-0.2 à 0.5)
            return -0.2 + Math.random() * 0.7;
        }
    }

    /**
     * Obtient la classe CSS pour la corrélation
     */
    getCorrelationClass(correlation) {
        if (correlation >= 0.7) return 'correlation-high';
        if (correlation >= 0.3) return 'correlation-medium';
        if (correlation >= -0.3) return 'correlation-low';
        return 'correlation-negative';
    }

    /**
     * Obtient la couleur pour la corrélation
     */
    getCorrelationColor(correlation) {
        // Rouge pour corrélation négative, vert pour positive
        const intensity = Math.abs(correlation);
        if (correlation >= 0) {
            const green = Math.floor(intensity * 255);
            return `rgba(16, 185, 129, ${intensity * 0.8})`;
        } else {
            const red = Math.floor(intensity * 255);
            return `rgba(239, 68, 68, ${intensity * 0.8})`;
        }
    }

    /**
     * Génère un tableau de couleurs
     */
    generateColors(count) {
        const baseColors = [
            this.colors.primary,
            this.colors.success,
            this.colors.warning,
            this.colors.info,
            this.colors.danger,
            '#8b5cf6', // purple
            '#ec4899', // pink
            '#06b6d4', // cyan
            '#84cc16', // lime
            '#f97316'  // orange
        ];
        
        const colors = [];
        for (let i = 0; i < count; i++) {
            if (i < baseColors.length) {
                colors.push(baseColors[i]);
            } else {
                // Générer des couleurs aléatoires si on dépasse les couleurs de base
                const hue = (i * 137.508) % 360; // Golden angle approximation
                colors.push(`hsl(${hue}, 70%, 50%)`);
            }
        }
        
        return colors;
    }

    /**
     * Obtient le nombre de points pour une période
     */
    getPeriodPoints(period) {
        switch (period) {
            case '1M': return 30;
            case '3M': return 90;
            case '6M': return 180;
            case '1Y': return 365;
            case 'ALL': return 500;
            default: return 30;
        }
    }

    /**
     * Obtient l'intervalle en millisecondes pour une période
     */
    getPeriodInterval(period) {
        switch (period) {
            case '1M': return 24 * 60 * 60 * 1000; // 1 jour
            case '3M': return 24 * 60 * 60 * 1000; // 1 jour
            case '6M': return 24 * 60 * 60 * 1000; // 1 jour
            case '1Y': return 24 * 60 * 60 * 1000; // 1 jour
            case 'ALL': return 7 * 24 * 60 * 60 * 1000; // 1 semaine
            default: return 24 * 60 * 60 * 1000;
        }
    }

    /**
     * Met à jour un graphique existant
     */
    updateChart(canvasId, newData) {
        const chart = this.charts.get(canvasId);
        if (!chart) return;

        chart.data = newData;
        chart.update('none'); // Animation désactivée pour les mises à jour temps réel
    }

    /**
     * Redimensionne tous les graphiques
     */
    resizeAllCharts() {
        this.charts.forEach(chart => {
            chart.resize();
        });
    }

    /**
     * Détruit un graphique
     */
    destroyChart(canvasId) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.destroy();
            this.charts.delete(canvasId);
        }
    }

    /**
     * Détruit tous les graphiques
     */
    destroyAllCharts() {
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
    }

    /**
     * Exporte un graphique en image
     */
    exportChart(canvasId, filename = 'chart.png') {
        const chart = this.charts.get(canvasId);
        if (!chart) return;

        const link = document.createElement('a');
        link.download = filename;
        link.href = chart.toBase64Image();
        link.click();
    }

    /**
     * Configure le thème des graphiques
     */
    setTheme(isDark) {
        const textColor = isDark ? '#e5e7eb' : '#374151';
        const gridColor = isDark ? '#374151' : '#e5e7eb';
        
        Chart.defaults.color = textColor;
        Chart.defaults.borderColor = gridColor;
        Chart.defaults.backgroundColor = 'transparent';
        
        // Mettre à jour tous les graphiques existants
        this.charts.forEach(chart => {
            chart.options.scales = chart.options.scales || {};
            
            Object.keys(chart.options.scales).forEach(scaleKey => {
                const scale = chart.options.scales[scaleKey];
                scale.ticks = scale.ticks || {};
                scale.grid = scale.grid || {};
                
                scale.ticks.color = textColor;
                scale.grid.color = gridColor;
            });
            
            chart.update('none');
        });
    }
}

// Export global
window.PortfolioCharts = PortfolioCharts;

// Auto-initialisation
document.addEventListener('DOMContentLoaded', () => {
    if (typeof window.portfolioCharts === 'undefined') {
        window.portfolioCharts = new PortfolioCharts();
        
        // Liaison avec le gestionnaire de thème
        if (window.themeManager) {
            window.themeManager.addEventListener('themeChanged', (event) => {
                window.portfolioCharts.setTheme(event.detail.isDark);
            });
        }
        
        // Redimensionnement automatique
        window.addEventListener('resize', () => {
            setTimeout(() => {
                window.portfolioCharts.resizeAllCharts();
            }, 100);
        });
    }
});