/**
 * Dashboard Charts - Gestion des graphiques pour le dashboard FinAgent
 * Initialisation et mise à jour des graphiques Chart.js
 */

class DashboardCharts {
    constructor() {
        this.charts = new Map();
        this.chartConfigs = new Map();
        this.colors = {
            primary: '#3B82F6',
            success: '#10B981',
            danger: '#EF4444',
            warning: '#F59E0B',
            info: '#06B6D4',
            secondary: '#6B7280',
            gradient: {
                primary: ['#3B82F6', '#1D4ED8'],
                success: ['#10B981', '#059669'],
                danger: ['#EF4444', '#DC2626']
            }
        };
        
        this.init();
    }

    /**
     * Initialisation des graphiques
     */
    init() {
        // Attendre que le DOM soit chargé
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeCharts());
        } else {
            this.initializeCharts();
        }
    }

    /**
     * Initialiser tous les graphiques du dashboard
     */
    initializeCharts() {
        try {
            this.initPerformanceChart();
            console.log('Graphiques du dashboard initialisés avec succès');
        } catch (error) {
            console.error('Erreur lors de l\'initialisation des graphiques:', error);
        }
    }

    /**
     * Initialiser le graphique de performance du portefeuille
     */
    initPerformanceChart() {
        const canvas = document.getElementById('performance-chart');
        if (!canvas) {
            console.warn('Canvas performance-chart non trouvé');
            return;
        }

        const ctx = canvas.getContext('2d');
        
        // Données simulées pour la performance
        const performanceData = this.generatePerformanceData();
        
        const config = {
            type: 'line',
            data: {
                labels: performanceData.labels,
                datasets: [{
                    label: 'Valeur du Portefeuille',
                    data: performanceData.values,
                    borderColor: this.colors.primary,
                    backgroundColor: this.createGradient(ctx, this.colors.gradient.primary),
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: this.colors.primary,
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 2
                }, {
                    label: 'Benchmark (CAC 40)',
                    data: performanceData.benchmark,
                    borderColor: this.colors.secondary,
                    backgroundColor: 'transparent',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        align: 'end',
                        labels: {
                            boxWidth: 12,
                            padding: 15,
                            font: {
                                size: 12,
                                family: 'Inter'
                            }
                        }
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: this.colors.primary,
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true,
                        callbacks: {
                            title: (context) => {
                                const date = new Date(context[0].label);
                                return date.toLocaleDateString('fr-FR', {
                                    weekday: 'long',
                                    year: 'numeric',
                                    month: 'long',
                                    day: 'numeric'
                                });
                            },
                            label: (context) => {
                                const value = context.parsed.y;
                                return `${context.dataset.label}: ${this.formatCurrency(value)}`;
                            },
                            afterBody: (context) => {
                                if (context.length > 0) {
                                    const currentValue = context[0].parsed.y;
                                    const initialValue = performanceData.values[0];
                                    const change = ((currentValue - initialValue) / initialValue) * 100;
                                    return `Performance: ${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'dd/MM'
                            }
                        },
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 11,
                                family: 'Inter'
                            },
                            color: '#6B7280',
                            maxTicksLimit: 8
                        }
                    },
                    y: {
                        position: 'right',
                        grid: {
                            color: 'rgba(107, 114, 128, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            font: {
                                size: 11,
                                family: 'Inter'
                            },
                            color: '#6B7280',
                            callback: (value) => this.formatCurrency(value, 0)
                        }
                    }
                },
                elements: {
                    point: {
                        radius: 0,
                        hoverRadius: 6
                    }
                }
            }
        };

        const chart = new Chart(ctx, config);
        this.charts.set('performance', chart);
        this.chartConfigs.set('performance', config);

        // Gestion des boutons de période
        this.setupTimeframeButtons('performance');
    }

    /**
     * Créer un gradient pour les graphiques
     */
    createGradient(ctx, colors) {
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, colors[0] + '40'); // 40 = 25% opacity
        gradient.addColorStop(1, colors[1] + '10'); // 10 = 6% opacity
        return gradient;
    }

    /**
     * Générer des données simulées pour la performance
     */
    generatePerformanceData() {
        const days = 30;
        const labels = [];
        const values = [];
        const benchmark = [];
        
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - days);
        
        let portfolioValue = 113000; // Valeur initiale
        let benchmarkValue = 100; // Base 100 pour le benchmark
        
        for (let i = 0; i <= days; i++) {
            const date = new Date(startDate);
            date.setDate(date.getDate() + i);
            labels.push(date.toISOString());
            
            // Simulation de la volatilité du portefeuille
            const portfolioChange = (Math.random() - 0.48) * 0.02; // Légèrement positif
            portfolioValue *= (1 + portfolioChange);
            values.push(Math.round(portfolioValue * 100) / 100);
            
            // Simulation du benchmark (plus stable)
            const benchmarkChange = (Math.random() - 0.5) * 0.015;
            benchmarkValue *= (1 + benchmarkChange);
            benchmark.push(Math.round(benchmarkValue * portfolioValue / 100 * 100) / 100);
        }
        
        return { labels, values, benchmark };
    }

    /**
     * Configuration des boutons de période
     */
    setupTimeframeButtons(chartId) {
        const chart = this.charts.get(chartId);
        if (!chart) return;

        const buttons = document.querySelectorAll('.chart-timeframe-btn');
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Mise à jour de l'état actif
                buttons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                // Mise à jour des données du graphique
                const period = button.dataset.period;
                this.updateChartData(chartId, period);
            });
        });
    }

    /**
     * Mettre à jour les données d'un graphique
     */
    updateChartData(chartId, period) {
        const chart = this.charts.get(chartId);
        if (!chart) return;

        // Générer de nouvelles données selon la période
        let newData;
        switch (period) {
            case '1D':
                newData = this.generatePerformanceData(1);
                break;
            case '1W':
                newData = this.generatePerformanceData(7);
                break;
            case '1M':
                newData = this.generatePerformanceData(30);
                break;
            case '3M':
                newData = this.generatePerformanceData(90);
                break;
            case '1Y':
                newData = this.generatePerformanceData(365);
                break;
            case 'ALL':
                newData = this.generatePerformanceData(730); // 2 ans
                break;
            default:
                newData = this.generatePerformanceData(30);
        }

        // Mettre à jour le graphique
        chart.data.labels = newData.labels;
        chart.data.datasets[0].data = newData.values;
        chart.data.datasets[1].data = newData.benchmark;
        
        // Animer la mise à jour
        chart.update('active');
    }

    /**
     * Actualiser tous les graphiques
     */
    refreshAllCharts() {
        this.charts.forEach((chart, id) => {
            try {
                if (id === 'performance') {
                    const newData = this.generatePerformanceData();
                    chart.data.labels = newData.labels;
                    chart.data.datasets[0].data = newData.values;
                    chart.data.datasets[1].data = newData.benchmark;
                }
                
                chart.update('active');
            } catch (error) {
                console.error(`Erreur lors de l'actualisation du graphique ${id}:`, error);
            }
        });
    }

    /**
     * Redimensionner tous les graphiques
     */
    resizeAllCharts() {
        this.charts.forEach(chart => {
            try {
                chart.resize();
            } catch (error) {
                console.error('Erreur lors du redimensionnement:', error);
            }
        });
    }

    /**
     * Mettre à jour le thème des graphiques
     */
    updateChartsTheme(isDark) {
        const textColor = isDark ? '#E5E7EB' : '#6B7280';
        const gridColor = isDark ? 'rgba(229, 231, 235, 0.1)' : 'rgba(107, 114, 128, 0.1)';

        this.charts.forEach(chart => {
            try {
                // Mettre à jour les couleurs des axes
                chart.options.scales.x.ticks.color = textColor;
                chart.options.scales.y.ticks.color = textColor;
                chart.options.scales.y.grid.color = gridColor;
                
                // Mettre à jour la légende
                chart.options.plugins.legend.labels.color = textColor;
                
                chart.update('none');
            } catch (error) {
                console.error('Erreur lors de la mise à jour du thème:', error);
            }
        });
    }

    /**
     * Nettoyer tous les graphiques
     */
    destroy() {
        this.charts.forEach(chart => {
            try {
                chart.destroy();
            } catch (error) {
                console.error('Erreur lors de la destruction du graphique:', error);
            }
        });
        this.charts.clear();
        this.chartConfigs.clear();
    }

    /**
     * Utilitaires de formatage
     */
    formatCurrency(value, decimals = 2) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value);
    }

    formatNumber(value, decimals = 2) {
        return new Intl.NumberFormat('fr-FR', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value);
    }

    formatPercentage(value, decimals = 2) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'percent',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value / 100);
    }
}

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardCharts;
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    if (typeof window !== 'undefined') {
        window.dashboardCharts = new DashboardCharts();
    }
});