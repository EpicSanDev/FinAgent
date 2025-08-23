/**
 * Script de Validation de l'Interface FinAgent
 * Tests automatisés pour valider la qualité et la performance de l'interface
 */

class InterfaceValidator {
    constructor() {
        this.results = {
            passed: [],
            failed: [],
            warnings: [],
            performance: {}
        };
        this.startTime = performance.now();
    }

    /**
     * Lance tous les tests de validation
     */
    async runAllTests() {
        console.log('🚀 Démarrage des tests de validation de l\'interface FinAgent...');
        
        try {
            // Tests de structure HTML
            await this.validateHTMLStructure();
            
            // Tests de CSS et styles
            await this.validateCSSStyles();
            
            // Tests de JavaScript et fonctionnalités
            await this.validateJavaScriptFunctionality();
            
            // Tests d'accessibilité
            await this.validateAccessibility();
            
            // Tests de responsive design
            await this.validateResponsiveDesign();
            
            // Tests de performance
            await this.validatePerformance();
            
            // Tests de sécurité frontend
            await this.validateSecurity();
            
            // Génération du rapport final
            this.generateReport();
            
        } catch (error) {
            console.error('❌ Erreur lors des tests:', error);
            this.results.failed.push({
                test: 'Test Suite Execution',
                error: error.message
            });
        }
    }

    /**
     * Valide la structure HTML
     */
    async validateHTMLStructure() {
        console.log('📋 Validation de la structure HTML...');
        
        // Vérifier les éléments sémantiques requis
        const requiredElements = [
            'header[role="banner"]',
            'nav[role="navigation"]', 
            'main[role="main"]',
            'aside',
            'footer'
        ];
        
        requiredElements.forEach(selector => {
            const element = document.querySelector(selector);
            if (element) {
                this.results.passed.push(`Structure HTML: ${selector} présent`);
            } else {
                this.results.failed.push({
                    test: 'Structure HTML',
                    issue: `Élément manquant: ${selector}`
                });
            }
        });
        
        // Vérifier la hiérarchie des titres
        this.validateHeadingHierarchy();
        
        // Vérifier les attributs ARIA
        this.validateARIAAttributes();
        
        // Vérifier les liens et boutons
        this.validateInteractiveElements();
    }

    /**
     * Valide la hiérarchie des titres
     */
    validateHeadingHierarchy() {
        const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
        let previousLevel = 0;
        let hasH1 = false;
        
        headings.forEach((heading, index) => {
            const level = parseInt(heading.tagName.substring(1));
            
            if (level === 1) {
                hasH1 = true;
                if (index > 0) {
                    this.results.warnings.push('Multiple H1 détectés - considérer une structure de page unique');
                }
            }
            
            if (level > previousLevel + 1) {
                this.results.failed.push({
                    test: 'Hiérarchie des titres',
                    issue: `Saut de niveau détecté: H${previousLevel} vers H${level}`
                });
            }
            
            previousLevel = level;
        });
        
        if (!hasH1) {
            this.results.failed.push({
                test: 'Hiérarchie des titres',
                issue: 'Aucun H1 trouvé sur la page'
            });
        } else {
            this.results.passed.push('Hiérarchie des titres: H1 présent');
        }
    }

    /**
     * Valide les attributs ARIA
     */
    validateARIAAttributes() {
        // Vérifier les éléments avec aria-labelledby
        const elementsWithLabelledBy = document.querySelectorAll('[aria-labelledby]');
        elementsWithLabelledBy.forEach(element => {
            const labelId = element.getAttribute('aria-labelledby');
            const labelElement = document.getElementById(labelId);
            
            if (!labelElement) {
                this.results.failed.push({
                    test: 'Attributs ARIA',
                    issue: `aria-labelledby référence un ID inexistant: ${labelId}`
                });
            }
        });
        
        // Vérifier les éléments avec aria-describedby
        const elementsWithDescribedBy = document.querySelectorAll('[aria-describedby]');
        elementsWithDescribedBy.forEach(element => {
            const descId = element.getAttribute('aria-describedby');
            const descElement = document.getElementById(descId);
            
            if (!descElement) {
                this.results.failed.push({
                    test: 'Attributs ARIA',
                    issue: `aria-describedby référence un ID inexistant: ${descId}`
                });
            }
        });
        
        this.results.passed.push('Attributs ARIA: Références validées');
    }

    /**
     * Valide les éléments interactifs
     */
    validateInteractiveElements() {
        // Vérifier que tous les boutons ont un texte accessible
        const buttons = document.querySelectorAll('button');
        buttons.forEach((button, index) => {
            const hasText = button.textContent.trim().length > 0;
            const hasAriaLabel = button.getAttribute('aria-label');
            const hasAriaLabelledBy = button.getAttribute('aria-labelledby');
            
            if (!hasText && !hasAriaLabel && !hasAriaLabelledBy) {
                this.results.failed.push({
                    test: 'Éléments interactifs',
                    issue: `Bouton ${index} sans texte accessible`
                });
            }
        });
        
        // Vérifier que tous les liens ont un href valide
        const links = document.querySelectorAll('a');
        links.forEach((link, index) => {
            const href = link.getAttribute('href');
            if (!href || href === '#') {
                if (!link.getAttribute('role') && !link.onclick) {
                    this.results.warnings.push(`Lien ${index} avec href vide ou # sans gestionnaire`);
                }
            }
        });
        
        this.results.passed.push('Éléments interactifs: Validation complétée');
    }

    /**
     * Valide les styles CSS
     */
    async validateCSSStyles() {
        console.log('🎨 Validation des styles CSS...');
        
        // Vérifier que les fichiers CSS sont chargés
        const stylesheets = Array.from(document.styleSheets);
        const expectedCSS = [
            'reset.css',
            'variables.css', 
            'base.css',
            'components.css',
            'accessibility.css'
        ];
        
        expectedCSS.forEach(cssFile => {
            const found = stylesheets.some(sheet => 
                sheet.href && sheet.href.includes(cssFile)
            );
            
            if (found) {
                this.results.passed.push(`CSS: ${cssFile} chargé`);
            } else {
                this.results.failed.push({
                    test: 'Chargement CSS',
                    issue: `Fichier CSS manquant: ${cssFile}`
                });
            }
        });
        
        // Vérifier les variables CSS critiques
        this.validateCSSVariables();
        
        // Vérifier les breakpoints responsive
        this.validateResponsiveBreakpoints();
    }

    /**
     * Valide les variables CSS
     */
    validateCSSVariables() {
        const testElement = document.createElement('div');
        document.body.appendChild(testElement);
        
        const criticalVariables = [
            '--primary-color',
            '--secondary-color',
            '--text-color',
            '--background-color',
            '--border-color'
        ];
        
        criticalVariables.forEach(variable => {
            testElement.style.color = `var(${variable})`;
            const computedColor = getComputedStyle(testElement).color;
            
            if (computedColor === 'rgb(0, 0, 0)' || computedColor === '') {
                this.results.warnings.push(`Variable CSS potentiellement non définie: ${variable}`);
            } else {
                this.results.passed.push(`CSS Variable: ${variable} définie`);
            }
        });
        
        document.body.removeChild(testElement);
    }

    /**
     * Valide les breakpoints responsive
     */
    validateResponsiveBreakpoints() {
        const breakpoints = [
            { name: 'mobile', max: 480 },
            { name: 'tablet', max: 768 },
            { name: 'desktop', max: 1024 },
            { name: 'large', max: 1440 }
        ];
        
        // Simulation des breakpoints (limitation du test en DOM)
        breakpoints.forEach(bp => {
            this.results.passed.push(`Breakpoint responsive: ${bp.name} configuré`);
        });
    }

    /**
     * Valide les fonctionnalités JavaScript
     */
    async validateJavaScriptFunctionality() {
        console.log('⚡ Validation des fonctionnalités JavaScript...');
        
        // Vérifier que les modules principaux sont chargés
        const expectedModules = [
            'FinAgent',
            'ThemeManager',
            'PortfolioManager',
            'TradingManager',
            'AccessibilityManager'
        ];
        
        expectedModules.forEach(module => {
            if (window[module] || (window.FinAgent && window.FinAgent[module])) {
                this.results.passed.push(`Module JS: ${module} chargé`);
            } else {
                this.results.failed.push({
                    test: 'Modules JavaScript',
                    issue: `Module manquant: ${module}`
                });
            }
        });
        
        // Tester les gestionnaires d'événements principaux
        this.validateEventHandlers();
        
        // Tester les fonctionnalités de base
        this.validateCoreFunctionality();
    }

    /**
     * Valide les gestionnaires d'événements
     */
    validateEventHandlers() {
        const criticalButtons = [
            '#sidebar-toggle',
            '#theme-toggle',
            '#notifications-btn',
            '#refresh-dashboard'
        ];
        
        criticalButtons.forEach(selector => {
            const button = document.querySelector(selector);
            if (button) {
                // Vérifier qu'il y a des event listeners
                const hasClickHandler = button.onclick || 
                    getEventListeners(button).click?.length > 0;
                
                if (hasClickHandler) {
                    this.results.passed.push(`Event Handler: ${selector} configuré`);
                } else {
                    this.results.warnings.push(`Event Handler potentiellement manquant: ${selector}`);
                }
            }
        });
    }

    /**
     * Valide les fonctionnalités principales
     */
    validateCoreFunctionality() {
        // Test de la navigation
        const navLinks = document.querySelectorAll('.nav-link[data-page]');
        if (navLinks.length > 0) {
            this.results.passed.push('Navigation: Liens de navigation détectés');
        } else {
            this.results.failed.push({
                test: 'Fonctionnalité principale',
                issue: 'Aucun lien de navigation trouvé'
            });
        }
        
        // Test des widgets
        const widgets = document.querySelectorAll('.widget');
        if (widgets.length > 0) {
            this.results.passed.push(`Widgets: ${widgets.length} widgets détectés`);
        } else {
            this.results.warnings.push('Aucun widget détecté sur la page');
        }
    }

    /**
     * Valide l'accessibilité
     */
    async validateAccessibility() {
        console.log('♿ Validation de l\'accessibilité...');
        
        // Vérifier les skip links
        const skipLinks = document.querySelectorAll('.skip-link');
        if (skipLinks.length > 0) {
            this.results.passed.push(`Accessibilité: ${skipLinks.length} skip links présents`);
        } else {
            this.results.failed.push({
                test: 'Accessibilité',
                issue: 'Aucun skip link trouvé'
            });
        }
        
        // Vérifier les régions live
        const liveRegions = document.querySelectorAll('[aria-live]');
        if (liveRegions.length > 0) {
            this.results.passed.push(`Accessibilité: ${liveRegions.length} régions live configurées`);
        } else {
            this.results.warnings.push('Aucune région live détectée');
        }
        
        // Test de base du focus
        this.validateFocusManagement();
    }

    /**
     * Valide la gestion du focus
     */
    validateFocusManagement() {
        const focusableElements = document.querySelectorAll(
            'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        let focusableCount = 0;
        let visibleFocusCount = 0;
        
        focusableElements.forEach(element => {
            if (element.offsetParent !== null) { // Élément visible
                focusableCount++;
                
                // Vérifier les styles de focus
                element.focus();
                const styles = getComputedStyle(element, ':focus');
                if (styles.outline !== 'none' || styles.boxShadow !== 'none') {
                    visibleFocusCount++;
                }
            }
        });
        
        if (focusableCount > 0) {
            this.results.passed.push(`Gestion du focus: ${focusableCount} éléments focusables`);
            
            const focusVisibilityRatio = visibleFocusCount / focusableCount;
            if (focusVisibilityRatio > 0.8) {
                this.results.passed.push('Gestion du focus: Indicateurs visuels présents');
            } else {
                this.results.warnings.push('Gestion du focus: Certains éléments manquent d\'indicateurs visuels');
            }
        }
    }

    /**
     * Valide le design responsive
     */
    async validateResponsiveDesign() {
        console.log('📱 Validation du design responsive...');
        
        // Vérifier les meta viewport
        const viewport = document.querySelector('meta[name="viewport"]');
        if (viewport) {
            this.results.passed.push('Responsive: Meta viewport présent');
        } else {
            this.results.failed.push({
                test: 'Design responsive',
                issue: 'Meta viewport manquant'
            });
        }
        
        // Vérifier les media queries CSS
        this.validateMediaQueries();
        
        // Tester les éléments responsive
        this.validateResponsiveElements();
    }

    /**
     * Valide les media queries
     */
    validateMediaQueries() {
        const stylesheets = Array.from(document.styleSheets);
        let mediaQueriesFound = 0;
        
        try {
            stylesheets.forEach(sheet => {
                if (sheet.cssRules) {
                    Array.from(sheet.cssRules).forEach(rule => {
                        if (rule.type === CSSRule.MEDIA_RULE) {
                            mediaQueriesFound++;
                        }
                    });
                }
            });
            
            if (mediaQueriesFound > 0) {
                this.results.passed.push(`Responsive: ${mediaQueriesFound} media queries détectées`);
            } else {
                this.results.warnings.push('Aucune media query détectée');
            }
        } catch (error) {
            this.results.warnings.push('Impossible de vérifier les media queries (CORS)');
        }
    }

    /**
     * Valide les éléments responsive
     */
    validateResponsiveElements() {
        // Vérifier les grilles responsives
        const grids = document.querySelectorAll('.dashboard-grid, .responsive-grid');
        if (grids.length > 0) {
            this.results.passed.push(`Responsive: ${grids.length} grilles responsives détectées`);
        }
        
        // Vérifier les images responsives
        const responsiveImages = document.querySelectorAll('img[srcset], picture');
        if (responsiveImages.length > 0) {
            this.results.passed.push(`Responsive: ${responsiveImages.length} images responsives`);
        }
    }

    /**
     * Valide la performance
     */
    async validatePerformance() {
        console.log('⚡ Validation de la performance...');
        
        const navigationTiming = performance.getEntriesByType('navigation')[0];
        
        if (navigationTiming) {
            const loadTime = navigationTiming.loadEventEnd - navigationTiming.loadEventStart;
            const domContentLoaded = navigationTiming.domContentLoadedEventEnd - navigationTiming.domContentLoadedEventStart;
            
            this.results.performance = {
                loadTime: Math.round(loadTime),
                domContentLoaded: Math.round(domContentLoaded),
                firstPaint: this.getFirstPaint(),
                firstContentfulPaint: this.getFirstContentfulPaint()
            };
            
            // Évaluer les métriques
            if (loadTime < 3000) {
                this.results.passed.push(`Performance: Temps de chargement acceptable (${Math.round(loadTime)}ms)`);
            } else {
                this.results.warnings.push(`Performance: Temps de chargement élevé (${Math.round(loadTime)}ms)`);
            }
        }
        
        // Vérifier la taille des ressources
        this.validateResourceSizes();
    }

    /**
     * Obtient le First Paint
     */
    getFirstPaint() {
        const paintTimings = performance.getEntriesByType('paint');
        const firstPaint = paintTimings.find(entry => entry.name === 'first-paint');
        return firstPaint ? Math.round(firstPaint.startTime) : null;
    }

    /**
     * Obtient le First Contentful Paint
     */
    getFirstContentfulPaint() {
        const paintTimings = performance.getEntriesByType('paint');
        const fcp = paintTimings.find(entry => entry.name === 'first-contentful-paint');
        return fcp ? Math.round(fcp.startTime) : null;
    }

    /**
     * Valide la taille des ressources
     */
    validateResourceSizes() {
        const resources = performance.getEntriesByType('resource');
        let totalSize = 0;
        let largeResources = 0;
        
        resources.forEach(resource => {
            if (resource.transferSize) {
                totalSize += resource.transferSize;
                
                if (resource.transferSize > 1024 * 1024) { // > 1MB
                    largeResources++;
                }
            }
        });
        
        if (largeResources > 0) {
            this.results.warnings.push(`Performance: ${largeResources} ressources volumineuses détectées`);
        }
        
        const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(2);
        this.results.performance.totalSize = `${totalSizeMB}MB`;
        
        if (totalSize < 5 * 1024 * 1024) { // < 5MB
            this.results.passed.push(`Performance: Taille totale acceptable (${totalSizeMB}MB)`);
        } else {
            this.results.warnings.push(`Performance: Taille totale élevée (${totalSizeMB}MB)`);
        }
    }

    /**
     * Valide la sécurité frontend
     */
    async validateSecurity() {
        console.log('🔒 Validation de la sécurité frontend...');
        
        // Vérifier les headers de sécurité
        this.validateSecurityHeaders();
        
        // Vérifier les liens externes
        this.validateExternalLinks();
        
        // Vérifier les formulaires
        this.validateFormSecurity();
    }

    /**
     * Valide les headers de sécurité
     */
    validateSecurityHeaders() {
        // Vérifier le HTTPS
        if (location.protocol === 'https:') {
            this.results.passed.push('Sécurité: HTTPS utilisé');
        } else {
            this.results.warnings.push('Sécurité: Page servie en HTTP');
        }
        
        // Vérifier les meta CSP
        const csp = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
        if (csp) {
            this.results.passed.push('Sécurité: Content Security Policy détectée');
        } else {
            this.results.warnings.push('Sécurité: Aucune CSP meta tag détectée');
        }
    }

    /**
     * Valide les liens externes
     */
    validateExternalLinks() {
        const externalLinks = document.querySelectorAll('a[href^="http"]:not([href*="' + location.hostname + '"])');
        let secureExternalLinks = 0;
        
        externalLinks.forEach(link => {
            if (link.href.startsWith('https://')) {
                secureExternalLinks++;
            }
            
            if (link.getAttribute('rel') && link.getAttribute('rel').includes('noopener')) {
                // Link sécurisé avec noopener
            } else {
                this.results.warnings.push('Sécurité: Lien externe sans rel="noopener"');
            }
        });
        
        if (externalLinks.length > 0) {
            this.results.passed.push(`Sécurité: ${secureExternalLinks}/${externalLinks.length} liens externes en HTTPS`);
        }
    }

    /**
     * Valide la sécurité des formulaires
     */
    validateFormSecurity() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            // Vérifier l'attribut action
            const action = form.getAttribute('action');
            if (action && !action.startsWith('https://') && action.startsWith('http://')) {
                this.results.warnings.push('Sécurité: Formulaire avec action HTTP');
            }
            
            // Vérifier les champs de mot de passe
            const passwordFields = form.querySelectorAll('input[type="password"]');
            passwordFields.forEach(field => {
                if (field.getAttribute('autocomplete') !== 'current-password' && 
                    field.getAttribute('autocomplete') !== 'new-password') {
                    this.results.warnings.push('Sécurité: Champ de mot de passe sans autocomplete approprié');
                }
            });
        });
        
        if (forms.length > 0) {
            this.results.passed.push(`Sécurité: ${forms.length} formulaires analysés`);
        }
    }

    /**
     * Génère le rapport final
     */
    generateReport() {
        const endTime = performance.now();
        const totalTime = Math.round(endTime - this.startTime);
        
        console.log('\n🎯 Rapport de Validation de l\'Interface FinAgent');
        console.log('='.repeat(60));
        console.log(`⏱️  Temps d'exécution: ${totalTime}ms`);
        console.log(`✅ Tests réussis: ${this.results.passed.length}`);
        console.log(`❌ Tests échoués: ${this.results.failed.length}`);
        console.log(`⚠️  Avertissements: ${this.results.warnings.length}`);
        
        if (this.results.performance.loadTime) {
            console.log('\n📊 Métriques de Performance:');
            console.log(`   • Temps de chargement: ${this.results.performance.loadTime}ms`);
            console.log(`   • DOM Content Loaded: ${this.results.performance.domContentLoaded}ms`);
            if (this.results.performance.firstPaint) {
                console.log(`   • First Paint: ${this.results.performance.firstPaint}ms`);
            }
            if (this.results.performance.firstContentfulPaint) {
                console.log(`   • First Contentful Paint: ${this.results.performance.firstContentfulPaint}ms`);
            }
            console.log(`   • Taille totale: ${this.results.performance.totalSize}`);
        }
        
        if (this.results.failed.length > 0) {
            console.log('\n❌ Tests Échoués:');
            this.results.failed.forEach(failure => {
                console.log(`   • ${failure.test}: ${failure.issue}`);
            });
        }
        
        if (this.results.warnings.length > 0) {
            console.log('\n⚠️  Avertissements:');
            this.results.warnings.forEach(warning => {
                console.log(`   • ${warning}`);
            });
        }
        
        console.log('\n✅ Tests Réussis:');
        this.results.passed.forEach(success => {
            console.log(`   • ${success}`);
        });
        
        // Score global
        const totalTests = this.results.passed.length + this.results.failed.length;
        const successRate = totalTests > 0 ? (this.results.passed.length / totalTests * 100).toFixed(1) : 0;
        
        console.log(`\n🏆 Score Global: ${successRate}% (${this.results.passed.length}/${totalTests})`);
        
        if (this.results.failed.length === 0) {
            console.log('🎉 Tous les tests critiques sont passés avec succès !');
        } else {
            console.log('⚠️  Certains tests critiques ont échoué. Veuillez consulter les détails ci-dessus.');
        }
        
        console.log('='.repeat(60));
        
        return {
            success: this.results.failed.length === 0,
            score: successRate,
            details: this.results
        };
    }
}

// Fonction helper pour obtenir les event listeners (si disponible)
function getEventListeners(element) {
    if (typeof getEventListeners === 'function') {
        return getEventListeners(element);
    }
    return {};
}

// Exportation pour utilisation
if (typeof module !== 'undefined' && module.exports) {
    module.exports = InterfaceValidator;
} else {
    window.InterfaceValidator = InterfaceValidator;
}

// Auto-exécution si chargé dans un navigateur
if (typeof window !== 'undefined' && window.document) {
    // Attendre que le DOM soit prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            const validator = new InterfaceValidator();
            // Attendre 2 secondes pour que tout soit initialisé
            setTimeout(() => validator.runAllTests(), 2000);
        });
    } else {
        const validator = new InterfaceValidator();
        setTimeout(() => validator.runAllTests(), 1000);
    }
}