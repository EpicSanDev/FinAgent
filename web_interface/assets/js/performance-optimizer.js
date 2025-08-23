/**
 * Optimiseur de Performance - FinAgent
 * Système d'optimisation automatique des performances de l'interface
 */

class PerformanceOptimizer {
    constructor() {
        this.config = {
            lazyLoadThreshold: 100, // px avant le viewport
            debounceDelay: 250, // ms pour debouncing
            throttleDelay: 16, // ms pour throttling (60fps)
            cacheExpiry: 5 * 60 * 1000, // 5 minutes
            maxCacheSize: 100, // nombre d'entrées max
            criticalResourceTimeout: 10000 // 10 secondes
        };
        
        this.cache = new Map();
        this.observers = new Map();
        this.performanceMetrics = {
            loadTime: 0,
            firstPaint: 0,
            largestContentfulPaint: 0,
            cumulativeLayoutShift: 0,
            firstInputDelay: 0
        };
        
        this.init();
    }

    /**
     * Initialise l'optimiseur de performance
     */
    init() {
        // Mesurer les métriques de base
        this.measureCoreWebVitals();
        
        // Optimiser le chargement des ressources
        this.optimizeResourceLoading();
        
        // Implémenter le lazy loading
        this.setupLazyLoading();
        
        // Optimiser les gestionnaires d'événements
        this.optimizeEventHandlers();
        
        // Cache intelligent
        this.setupIntelligentCaching();
        
        // Optimiser les animations
        this.optimizeAnimations();
        
        // Surveiller les performances en continu
        this.setupPerformanceMonitoring();
        
        console.log('🚀 Optimiseur de performance initialisé');
    }

    /**
     * Mesure les Core Web Vitals
     */
    measureCoreWebVitals() {
        // Largest Contentful Paint (LCP)
        this.observeLCP();
        
        // First Input Delay (FID)
        this.observeFID();
        
        // Cumulative Layout Shift (CLS)
        this.observeCLS();
        
        // Time to First Byte (TTFB)
        this.measureTTFB();
        
        // First Contentful Paint (FCP)
        this.measureFCP();
    }

    /**
     * Observe le Largest Contentful Paint
     */
    observeLCP() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                this.performanceMetrics.largestContentfulPaint = lastEntry.startTime;
                
                if (lastEntry.startTime > 2500) {
                    console.warn(`⚠️ LCP élevé: ${Math.round(lastEntry.startTime)}ms`);
                    this.optimizeLCP();
                }
            });
            
            observer.observe({ entryTypes: ['largest-contentful-paint'] });
            this.observers.set('lcp', observer);
        }
    }

    /**
     * Observe le First Input Delay
     */
    observeFID() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    this.performanceMetrics.firstInputDelay = entry.processingStart - entry.startTime;
                    
                    if (entry.processingStart - entry.startTime > 100) {
                        console.warn(`⚠️ FID élevé: ${Math.round(entry.processingStart - entry.startTime)}ms`);
                        this.optimizeFID();
                    }
                });
            });
            
            observer.observe({ entryTypes: ['first-input'] });
            this.observers.set('fid', observer);
        }
    }

    /**
     * Observe le Cumulative Layout Shift
     */
    observeCLS() {
        if ('PerformanceObserver' in window) {
            let clsScore = 0;
            
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (!entry.hadRecentInput) {
                        clsScore += entry.value;
                        this.performanceMetrics.cumulativeLayoutShift = clsScore;
                        
                        if (clsScore > 0.1) {
                            console.warn(`⚠️ CLS élevé: ${clsScore.toFixed(3)}`);
                            this.optimizeCLS();
                        }
                    }
                });
            });
            
            observer.observe({ entryTypes: ['layout-shift'] });
            this.observers.set('cls', observer);
        }
    }

    /**
     * Mesure le Time to First Byte
     */
    measureTTFB() {
        if (performance.getEntriesByType) {
            const navigationEntry = performance.getEntriesByType('navigation')[0];
            if (navigationEntry) {
                const ttfb = navigationEntry.responseStart - navigationEntry.requestStart;
                this.performanceMetrics.timeToFirstByte = ttfb;
                
                if (ttfb > 600) {
                    console.warn(`⚠️ TTFB élevé: ${Math.round(ttfb)}ms`);
                }
            }
        }
    }

    /**
     * Mesure le First Contentful Paint
     */
    measureFCP() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (entry.name === 'first-contentful-paint') {
                        this.performanceMetrics.firstPaint = entry.startTime;
                        
                        if (entry.startTime > 1800) {
                            console.warn(`⚠️ FCP élevé: ${Math.round(entry.startTime)}ms`);
                        }
                    }
                });
            });
            
            observer.observe({ entryTypes: ['paint'] });
            this.observers.set('fcp', observer);
        }
    }

    /**
     * Optimise le chargement des ressources
     */
    optimizeResourceLoading() {
        // Précharger les ressources critiques
        this.preloadCriticalResources();
        
        // Charger les ressources non-critiques de manière différée
        this.deferNonCriticalResources();
        
        // Optimiser les images
        this.optimizeImages();
        
        // Utiliser le prefetch pour les ressources futures
        this.prefetchFutureResources();
    }

    /**
     * Précharge les ressources critiques
     */
    preloadCriticalResources() {
        const criticalResources = [
            { href: 'assets/css/variables.css', as: 'style' },
            { href: 'assets/css/base.css', as: 'style' },
            { href: 'assets/js/app.js', as: 'script' },
            { href: 'assets/fonts/inter-var.woff2', as: 'font', type: 'font/woff2', crossorigin: '' }
        ];
        
        criticalResources.forEach(resource => {
            if (!document.querySelector(`link[href="${resource.href}"]`)) {
                const link = document.createElement('link');
                link.rel = 'preload';
                Object.assign(link, resource);
                document.head.appendChild(link);
            }
        });
    }

    /**
     * Diffère les ressources non-critiques
     */
    deferNonCriticalResources() {
        // Charger les widgets non-visibles après le load initial
        window.addEventListener('load', () => {
            setTimeout(() => {
                this.loadNonCriticalWidgets();
            }, 100);
        });
        
        // Charger les scripts analytics de manière différée
        this.deferAnalyticsScripts();
    }

    /**
     * Charge les widgets non-critiques
     */
    loadNonCriticalWidgets() {
        const hiddenWidgets = document.querySelectorAll('.widget[style*="display: none"], .widget.hidden');
        
        hiddenWidgets.forEach(widget => {
            if (widget.dataset.widgetId) {
                // Marquer comme prêt pour le lazy loading
                widget.classList.add('lazy-load-ready');
            }
        });
    }

    /**
     * Diffère les scripts analytics
     */
    deferAnalyticsScripts() {
        // Exemple pour Google Analytics (si utilisé)
        if (window.gtag) {
            requestIdleCallback(() => {
                // Initialiser l'analytics après idle
                console.log('📊 Analytics initialisé après idle');
            });
        }
    }

    /**
     * Optimise les images
     */
    optimizeImages() {
        const images = document.querySelectorAll('img:not([loading])');
        
        images.forEach(img => {
            // Ajouter le lazy loading natif
            img.loading = 'lazy';
            
            // Optimiser les dimensions si nécessaire
            if (!img.width && !img.height) {
                img.style.maxWidth = '100%';
                img.style.height = 'auto';
            }
        });
        
        // Implémenter le lazy loading personnalisé pour les navigateurs non-supportés
        if (!('loading' in HTMLImageElement.prototype)) {
            this.implementCustomLazyLoading();
        }
    }

    /**
     * Implémente le lazy loading personnalisé
     */
    implementCustomLazyLoading() {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        observer.unobserve(img);
                    }
                }
            });
        }, {
            rootMargin: `${this.config.lazyLoadThreshold}px`
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
        
        this.observers.set('images', imageObserver);
    }

    /**
     * Prefetch les ressources futures
     */
    prefetchFutureResources() {
        // Prefetch les pages probablement visitées
        const navigationLinks = document.querySelectorAll('.nav-link[data-page]');
        
        navigationLinks.forEach(link => {
            link.addEventListener('mouseenter', this.debounce(() => {
                const page = link.dataset.page;
                this.prefetchPageResources(page);
            }, 200), { once: true });
        });
    }

    /**
     * Prefetch les ressources d'une page
     */
    prefetchPageResources(page) {
        const pageResources = {
            portfolio: ['assets/js/portfolio-charts.js', 'assets/js/portfolio-manager.js'],
            market: ['assets/js/market-data-components.js', 'assets/js/technical-indicators.js'],
            trading: ['assets/js/trading-manager.js'],
            // ... autres pages
        };
        
        if (pageResources[page]) {
            pageResources[page].forEach(resource => {
                if (!document.querySelector(`link[href="${resource}"]`)) {
                    const link = document.createElement('link');
                    link.rel = 'prefetch';
                    link.href = resource;
                    document.head.appendChild(link);
                }
            });
        }
    }

    /**
     * Configure le lazy loading
     */
    setupLazyLoading() {
        // Lazy loading pour les widgets
        this.setupWidgetLazyLoading();
        
        // Lazy loading pour les graphiques
        this.setupChartLazyLoading();
        
        // Lazy loading pour les tableaux
        this.setupTableLazyLoading();
    }

    /**
     * Configure le lazy loading des widgets
     */
    setupWidgetLazyLoading() {
        const widgetObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const widget = entry.target;
                    this.loadWidget(widget);
                    widgetObserver.unobserve(widget);
                }
            });
        }, {
            rootMargin: `${this.config.lazyLoadThreshold}px`
        });
        
        document.querySelectorAll('.widget.lazy-load-ready').forEach(widget => {
            widgetObserver.observe(widget);
        });
        
        this.observers.set('widgets', widgetObserver);
    }

    /**
     * Charge un widget de manière lazy
     */
    loadWidget(widget) {
        const widgetId = widget.dataset.widgetId;
        
        if (widgetId && window.WidgetManager) {
            requestIdleCallback(() => {
                window.WidgetManager.initializeWidget(widgetId);
                widget.classList.remove('lazy-load-ready');
                widget.classList.add('lazy-loaded');
            });
        }
    }

    /**
     * Configure le lazy loading des graphiques
     */
    setupChartLazyLoading() {
        const chartObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const chart = entry.target;
                    this.loadChart(chart);
                    chartObserver.unobserve(chart);
                }
            });
        }, {
            rootMargin: `${this.config.lazyLoadThreshold}px`
        });
        
        document.querySelectorAll('.chart-container[data-lazy]').forEach(chart => {
            chartObserver.observe(chart);
        });
        
        this.observers.set('charts', chartObserver);
    }

    /**
     * Charge un graphique de manière lazy
     */
    loadChart(chartContainer) {
        const chartType = chartContainer.dataset.chartType;
        const chartData = chartContainer.dataset.chartData;
        
        if (chartType && window.ChartManager) {
            requestIdleCallback(() => {
                window.ChartManager.createChart(chartContainer, chartType, chartData);
                chartContainer.removeAttribute('data-lazy');
            });
        }
    }

    /**
     * Configure le lazy loading des tableaux
     */
    setupTableLazyLoading() {
        // Pagination virtuelle pour les grands tableaux
        const largeTables = document.querySelectorAll('table[data-virtual-scroll]');
        
        largeTables.forEach(table => {
            this.enableVirtualScrolling(table);
        });
    }

    /**
     * Active le défilement virtuel pour un tableau
     */
    enableVirtualScrolling(table) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const rowHeight = 40; // hauteur estimée d'une ligne
        const visibleRows = Math.ceil(window.innerHeight / rowHeight) + 10; // buffer
        
        if (rows.length > visibleRows * 2) {
            this.setupVirtualScrollForTable(table, rows, visibleRows, rowHeight);
        }
    }

    /**
     * Configure le défilement virtuel pour un tableau
     */
    setupVirtualScrollForTable(table, rows, visibleRows, rowHeight) {
        const tbody = table.querySelector('tbody');
        const container = table.closest('.table-container') || table.parentElement;
        
        // Créer un container de défilement
        const scrollContainer = document.createElement('div');
        scrollContainer.style.height = `${rows.length * rowHeight}px`;
        scrollContainer.style.position = 'relative';
        
        // Vider le tbody et ajouter seulement les lignes visibles
        tbody.innerHTML = '';
        
        let startIndex = 0;
        
        const updateVisibleRows = this.throttle(() => {
            const scrollTop = container.scrollTop;
            const newStartIndex = Math.floor(scrollTop / rowHeight);
            const endIndex = Math.min(newStartIndex + visibleRows, rows.length);
            
            if (newStartIndex !== startIndex) {
                startIndex = newStartIndex;
                
                // Mettre à jour les lignes visibles
                tbody.innerHTML = '';
                tbody.style.transform = `translateY(${startIndex * rowHeight}px)`;
                
                for (let i = startIndex; i < endIndex; i++) {
                    if (rows[i]) {
                        tbody.appendChild(rows[i].cloneNode(true));
                    }
                }
            }
        }, this.config.throttleDelay);
        
        container.addEventListener('scroll', updateVisibleRows);
        
        // Initialiser avec les premières lignes
        updateVisibleRows();
    }

    /**
     * Optimise les gestionnaires d'événements
     */
    optimizeEventHandlers() {
        // Remplacer les événements répétitifs par des versions optimisées
        this.optimizeScrollHandlers();
        this.optimizeResizeHandlers();
        this.optimizeInputHandlers();
    }

    /**
     * Optimise les gestionnaires de scroll
     */
    optimizeScrollHandlers() {
        const scrollElements = document.querySelectorAll('[data-scroll-handler]');
        
        scrollElements.forEach(element => {
            const handler = element.dataset.scrollHandler;
            if (window[handler] && typeof window[handler] === 'function') {
                const optimizedHandler = this.throttle(window[handler], this.config.throttleDelay);
                element.addEventListener('scroll', optimizedHandler, { passive: true });
            }
        });
    }

    /**
     * Optimise les gestionnaires de resize
     */
    optimizeResizeHandlers() {
        const resizeHandlers = [];
        
        // Collecter tous les handlers de resize existants
        if (window.onresize) {
            resizeHandlers.push(window.onresize);
        }
        
        // Créer un gestionnaire unique optimisé
        const optimizedResizeHandler = this.debounce(() => {
            resizeHandlers.forEach(handler => {
                if (typeof handler === 'function') {
                    handler();
                }
            });
            
            // Notifier les composants du resize
            this.notifyResize();
        }, this.config.debounceDelay);
        
        window.onresize = optimizedResizeHandler;
    }

    /**
     * Notifie les composants du redimensionnement
     */
    notifyResize() {
        // Redimensionner les graphiques
        if (window.ChartManager) {
            window.ChartManager.resizeAllCharts();
        }
        
        // Recalculer les layouts responsive
        if (window.ResponsiveManager) {
            window.ResponsiveManager.updateLayout();
        }
    }

    /**
     * Optimise les gestionnaires d'input
     */
    optimizeInputHandlers() {
        const searchInputs = document.querySelectorAll('input[type="search"], input[data-search]');
        
        searchInputs.forEach(input => {
            const originalHandler = input.oninput;
            
            if (originalHandler) {
                const optimizedHandler = this.debounce(originalHandler, this.config.debounceDelay);
                input.oninput = optimizedHandler;
            }
        });
    }

    /**
     * Configure le cache intelligent
     */
    setupIntelligentCaching() {
        // Cache pour les réponses API
        this.setupAPICache();
        
        // Cache pour les ressources statiques
        this.setupResourceCache();
        
        // Nettoyage automatique du cache
        this.setupCacheCleanup();
    }

    /**
     * Configure le cache API
     */
    setupAPICache() {
        if (window.APIManager) {
            const originalFetch = window.APIManager.fetch;
            
            window.APIManager.fetch = (url, options = {}) => {
                const cacheKey = this.generateCacheKey(url, options);
                
                // Vérifier le cache
                const cached = this.getFromCache(cacheKey);
                if (cached && !this.isCacheExpired(cached.timestamp)) {
                    return Promise.resolve(cached.data);
                }
                
                // Faire la requête et mettre en cache
                return originalFetch.call(window.APIManager, url, options)
                    .then(response => {
                        if (options.cache !== false) {
                            this.setCache(cacheKey, response);
                        }
                        return response;
                    });
            };
        }
    }

    /**
     * Génère une clé de cache
     */
    generateCacheKey(url, options) {
        const params = options.params ? JSON.stringify(options.params) : '';
        return `${url}:${params}`;
    }

    /**
     * Récupère depuis le cache
     */
    getFromCache(key) {
        return this.cache.get(key);
    }

    /**
     * Met en cache
     */
    setCache(key, data) {
        // Vérifier la taille du cache
        if (this.cache.size >= this.config.maxCacheSize) {
            // Supprimer l'entrée la plus ancienne
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }
        
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    /**
     * Vérifie si le cache a expiré
     */
    isCacheExpired(timestamp) {
        return Date.now() - timestamp > this.config.cacheExpiry;
    }

    /**
     * Configure le nettoyage du cache
     */
    setupCacheCleanup() {
        setInterval(() => {
            const now = Date.now();
            
            for (const [key, value] of this.cache.entries()) {
                if (this.isCacheExpired(value.timestamp)) {
                    this.cache.delete(key);
                }
            }
        }, this.config.cacheExpiry);
    }

    /**
     * Optimise les animations
     */
    optimizeAnimations() {
        // Utiliser requestAnimationFrame pour les animations
        this.setupRAFAnimations();
        
        // Optimiser les transitions CSS
        this.optimizeCSSTransitions();
        
        // Réduire les animations si préféré
        this.respectMotionPreferences();
    }

    /**
     * Configure les animations avec RAF
     */
    setupRAFAnimations() {
        // Remplacer les setInterval par requestAnimationFrame pour les animations
        const animatedElements = document.querySelectorAll('[data-animate]');
        
        animatedElements.forEach(element => {
            const animationType = element.dataset.animate;
            
            if (animationType === 'counter') {
                this.animateCounter(element);
            } else if (animationType === 'progress') {
                this.animateProgress(element);
            }
        });
    }

    /**
     * Anime un compteur avec RAF
     */
    animateCounter(element) {
        const targetValue = parseFloat(element.dataset.target || element.textContent);
        const duration = parseInt(element.dataset.duration) || 1000;
        let startTime = null;
        let startValue = 0;
        
        const animate = (currentTime) => {
            if (!startTime) startTime = currentTime;
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const currentValue = startValue + (targetValue - startValue) * this.easeOutCubic(progress);
            element.textContent = Math.round(currentValue);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    /**
     * Anime une barre de progression
     */
    animateProgress(element) {
        const targetWidth = parseFloat(element.dataset.target || '100');
        const duration = parseInt(element.dataset.duration) || 1000;
        let startTime = null;
        
        const animate = (currentTime) => {
            if (!startTime) startTime = currentTime;
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const currentWidth = targetWidth * this.easeOutCubic(progress);
            element.style.width = `${currentWidth}%`;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    /**
     * Fonction d'easing
     */
    easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }

    /**
     * Optimise les transitions CSS
     */
    optimizeCSSTransitions() {
        // Ajouter will-change aux éléments qui vont être animés
        const transitionElements = document.querySelectorAll('[data-transition]');
        
        transitionElements.forEach(element => {
            element.style.willChange = 'transform, opacity';
            
            // Retirer will-change après la transition
            element.addEventListener('transitionend', () => {
                element.style.willChange = 'auto';
            }, { once: true });
        });
    }

    /**
     * Respecte les préférences de mouvement
     */
    respectMotionPreferences() {
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.body.classList.add('reduce-motion');
            
            // Désactiver les animations non-essentielles
            const nonEssentialAnimations = document.querySelectorAll('[data-animation="decorative"]');
            nonEssentialAnimations.forEach(element => {
                element.style.animation = 'none';
                element.style.transition = 'none';
            });
        }
    }

    /**
     * Configure la surveillance des performances
     */
    setupPerformanceMonitoring() {
        // Surveiller les métriques en continu
        setInterval(() => {
            this.checkPerformanceHealth();
        }, 30000); // Toutes les 30 secondes
        
        // Surveiller la mémoire
        this.monitorMemoryUsage();
        
        // Détecter les goulots d'étranglement
        this.detectPerformanceBottlenecks();
    }

    /**
     * Vérifie la santé des performances
     */
    checkPerformanceHealth() {
        const now = performance.now();
        
        // Vérifier le FPS
        this.checkFrameRate();
        
        // Vérifier les tâches longues
        this.checkLongTasks();
        
        // Vérifier l'utilisation mémoire
        if (performance.memory) {
            const memoryUsage = performance.memory.usedJSHeapSize / performance.memory.totalJSHeapSize;
            
            if (memoryUsage > 0.8) {
                console.warn('⚠️ Utilisation mémoire élevée:', Math.round(memoryUsage * 100) + '%');
                this.optimizeMemoryUsage();
            }
        }
    }

    /**
     * Vérifie le taux de rafraîchissement
     */
    checkFrameRate() {
        let frameCount = 0;
        let lastTime = performance.now();
        
        const countFrame = () => {
            frameCount++;
            const currentTime = performance.now();
            
            if (currentTime - lastTime >= 1000) {
                const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
                
                if (fps < 30) {
                    console.warn('⚠️ FPS faible détecté:', fps);
                    this.optimizeRenderingPerformance();
                }
                
                frameCount = 0;
                lastTime = currentTime;
            }
            
            requestAnimationFrame(countFrame);
        };
        
        requestAnimationFrame(countFrame);
    }

    /**
     * Vérifie les tâches longues
     */
    checkLongTasks() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (entry.duration > 50) {
                        console.warn('⚠️ Tâche longue détectée:', Math.round(entry.duration) + 'ms');
                        this.optimizeLongTask(entry);
                    }
                });
            });
            
            observer.observe({ entryTypes: ['longtask'] });
            this.observers.set('longtask', observer);
        }
    }

    /**
     * Surveille l'utilisation mémoire
     */
    monitorMemoryUsage() {
        if ('memory' in performance) {
            setInterval(() => {
                const memory = performance.memory;
                const usagePercent = (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100;
                
                if (usagePercent > 90) {
                    console.warn('🚨 Mémoire critique:', Math.round(usagePercent) + '%');
                    this.forceGarbageCollection();
                }
            }, 60000); // Toutes les minutes
        }
    }

    /**
     * Force le garbage collection (si possible)
     */
    forceGarbageCollection() {
        // Nettoyer les caches
        this.cache.clear();
        
        // Nettoyer les observers inutiles
        this.cleanupObservers();
        
        // Forcer le GC si disponible (dev tools)
        if (window.gc && typeof window.gc === 'function') {
            window.gc();
        }
    }

    /**
     * Nettoie les observers inutiles
     */
    cleanupObservers() {
        this.observers.forEach((observer, key) => {
            if (key !== 'lcp' && key !== 'fid' && key !== 'cls') {
                observer.disconnect();
                this.observers.delete(key);
            }
        });
    }

    /**
     * Optimise la mémoire
     */
    optimizeMemoryUsage() {
        // Libérer les références inutiles
        this.cleanupUnusedElements();
        
        // Optimiser les event listeners
        this.optimizeEventListeners();
        
        // Nettoyer les timers
        this.cleanupTimers();
    }

    /**
     * Nettoie les éléments inutiles
     */
    cleanupUnusedElements() {
        // Supprimer les éléments cachés depuis longtemps
        const hiddenElements = document.querySelectorAll('[style*="display: none"]');
        hiddenElements.forEach(element => {
            if (element.dataset.hiddenSince) {
                const hiddenTime = Date.now() - parseInt(element.dataset.hiddenSince);
                if (hiddenTime > 300000) { // 5 minutes
                    element.remove();
                }
            } else {
                element.dataset.hiddenSince = Date.now().toString();
            }
        });
    }

    /**
     * Fonctions utilitaires de performance
     */
    debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    throttle(func, delay) {
        let lastCall = 0;
        return function (...args) {
            const now = Date.now();
            if (now - lastCall >= delay) {
                lastCall = now;
                return func.apply(this, args);
            }
        };
    }

    /**
     * Obtient le rapport de performance
     */
    getPerformanceReport() {
        return {
            metrics: this.performanceMetrics,
            cacheSize: this.cache.size,
            observersCount: this.observers.size,
            timestamp: Date.now()
        };
    }

    /**
     * Nettoie l'optimiseur
     */
    cleanup() {
        // Déconnecter tous les observers
        this.observers.forEach(observer => observer.disconnect());
        this.observers.clear();
        
        // Vider le cache
        this.cache.clear();
        
        console.log('🧹 Optimiseur de performance nettoyé');
    }
}

// Initialisation automatique
if (typeof window !== 'undefined') {
    window.PerformanceOptimizer = PerformanceOptimizer;
    
    // Initialiser après le chargement complet
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.performanceOptimizer = new PerformanceOptimizer();
        });
    } else {
        window.performanceOptimizer = new PerformanceOptimizer();
    }
}

// Export pour modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceOptimizer;
}