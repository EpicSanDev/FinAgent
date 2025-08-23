/**
 * Gestionnaire de responsivité et d'adaptation mobile pour FinAgent
 * Gère les breakpoints, le sidebar mobile, l'orientation, et l'optimisation tactile
 */

class ResponsiveManager {
    constructor() {
        this.breakpoints = {
            xs: 320,
            sm: 576,
            md: 768,
            lg: 992,
            xl: 1200,
            xxl: 1400
        };
        
        this.currentBreakpoint = null;
        this.isLandscape = false;
        this.isTouchDevice = false;
        this.sidebarOpen = false;
        
        this.init();
    }
    
    init() {
        this.detectTouchDevice();
        this.setupBreakpointDetection();
        this.setupOrientationHandling();
        this.setupSidebarToggle();
        this.setupTouchOptimizations();
        this.setupKeyboardHandling();
        this.setupScrollOptimizations();
        this.setupMobileGestures();
        
        // Écouter les changements de taille
        window.addEventListener('resize', this.debounce(() => {
            this.handleResize();
        }, 150));
        
        // Écouter les changements d'orientation
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });
        
        // Initial setup
        this.handleResize();
    }
    
    /**
     * Détecte si l'appareil supporte le tactile
     */
    detectTouchDevice() {
        this.isTouchDevice = (
            'ontouchstart' in window ||
            navigator.maxTouchPoints > 0 ||
            navigator.msMaxTouchPoints > 0
        );
        
        if (this.isTouchDevice) {
            document.body.classList.add('touch-device');
        } else {
            document.body.classList.add('no-touch');
        }
    }
    
    /**
     * Configure la détection des breakpoints
     */
    setupBreakpointDetection() {
        this.mediaQueries = {
            xs: window.matchMedia(`(max-width: ${this.breakpoints.sm - 1}px)`),
            sm: window.matchMedia(`(min-width: ${this.breakpoints.sm}px) and (max-width: ${this.breakpoints.md - 1}px)`),
            md: window.matchMedia(`(min-width: ${this.breakpoints.md}px) and (max-width: ${this.breakpoints.lg - 1}px)`),
            lg: window.matchMedia(`(min-width: ${this.breakpoints.lg}px) and (max-width: ${this.breakpoints.xl - 1}px)`),
            xl: window.matchMedia(`(min-width: ${this.breakpoints.xl}px) and (max-width: ${this.breakpoints.xxl - 1}px)`),
            xxl: window.matchMedia(`(min-width: ${this.breakpoints.xxl}px)`)
        };
        
        // Écouter les changements de breakpoint
        Object.keys(this.mediaQueries).forEach(breakpoint => {
            this.mediaQueries[breakpoint].addEventListener('change', () => {
                this.updateBreakpoint();
            });
        });
    }
    
    /**
     * Met à jour le breakpoint actuel
     */
    updateBreakpoint() {
        const previousBreakpoint = this.currentBreakpoint;
        
        for (const [breakpoint, mediaQuery] of Object.entries(this.mediaQueries)) {
            if (mediaQuery.matches) {
                this.currentBreakpoint = breakpoint;
                break;
            }
        }
        
        if (previousBreakpoint !== this.currentBreakpoint) {
            this.onBreakpointChange(previousBreakpoint, this.currentBreakpoint);
        }
        
        // Mettre à jour les classes CSS
        document.body.className = document.body.className.replace(/breakpoint-\w+/g, '');
        document.body.classList.add(`breakpoint-${this.currentBreakpoint}`);
    }
    
    /**
     * Gestionnaire de changement de breakpoint
     */
    onBreakpointChange(from, to) {
        console.log(`Breakpoint changed: ${from} -> ${to}`);
        
        // Fermer la sidebar sur mobile
        if (this.isMobile() && this.sidebarOpen) {
            this.closeSidebar();
        }
        
        // Ajuster les widgets pour mobile
        if (this.isMobile()) {
            this.optimizeForMobile();
        } else {
            this.optimizeForDesktop();
        }
        
        // Émettre un événement personnalisé
        window.dispatchEvent(new CustomEvent('breakpointChange', {
            detail: { from, to, isMobile: this.isMobile() }
        }));
    }
    
    /**
     * Configure la gestion de l'orientation
     */
    setupOrientationHandling() {
        const checkOrientation = () => {
            this.isLandscape = window.innerWidth > window.innerHeight;
            document.body.classList.toggle('landscape', this.isLandscape);
            document.body.classList.toggle('portrait', !this.isLandscape);
        };
        
        checkOrientation();
        window.addEventListener('resize', checkOrientation);
    }
    
    /**
     * Configure le toggle de la sidebar mobile
     */
    setupSidebarToggle() {
        const sidebar = document.querySelector('.app-sidebar');
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
        
        // Bouton toggle
        const toggleBtn = document.querySelector('.sidebar-toggle') || this.createSidebarToggle();
        
        toggleBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleSidebar();
        });
        
        // Fermer en cliquant sur l'overlay
        overlay.addEventListener('click', () => {
            this.closeSidebar();
        });
        
        // Fermer avec Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.sidebarOpen) {
                this.closeSidebar();
            }
        });
    }
    
    /**
     * Crée le bouton de toggle de la sidebar
     */
    createSidebarToggle() {
        const toggle = document.createElement('button');
        toggle.className = 'sidebar-toggle btn btn-secondary d-lg-none';
        toggle.innerHTML = '<i class="icon-menu"></i>';
        toggle.setAttribute('aria-label', 'Toggle navigation');
        
        const header = document.querySelector('.app-header .header-left');
        if (header) {
            header.insertBefore(toggle, header.firstChild);
        }
        
        return toggle;
    }
    
    /**
     * Bascule l'état de la sidebar
     */
    toggleSidebar() {
        if (this.sidebarOpen) {
            this.closeSidebar();
        } else {
            this.openSidebar();
        }
    }
    
    /**
     * Ouvre la sidebar mobile
     */
    openSidebar() {
        const sidebar = document.querySelector('.app-sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        
        if (sidebar && overlay) {
            sidebar.classList.add('mobile-open');
            overlay.classList.add('active');
            document.body.classList.add('sidebar-open');
            this.sidebarOpen = true;
            
            // Focus sur le premier élément de navigation
            const firstNavItem = sidebar.querySelector('.nav-link');
            if (firstNavItem) {
                firstNavItem.focus();
            }
        }
    }
    
    /**
     * Ferme la sidebar mobile
     */
    closeSidebar() {
        const sidebar = document.querySelector('.app-sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        
        if (sidebar && overlay) {
            sidebar.classList.remove('mobile-open');
            overlay.classList.remove('active');
            document.body.classList.remove('sidebar-open');
            this.sidebarOpen = false;
        }
    }
    
    /**
     * Configure les optimisations tactiles
     */
    setupTouchOptimizations() {
        if (!this.isTouchDevice) return;
        
        // Augmenter la zone de toucher pour les petits éléments
        const smallElements = document.querySelectorAll('.btn-sm, .nav-link, .dropdown-toggle');
        smallElements.forEach(element => {
            element.style.minHeight = '44px';
            element.style.minWidth = '44px';
        });
        
        // Optimiser les hover states pour mobile
        document.addEventListener('touchstart', () => {}, { passive: true });
    }
    
    /**
     * Configure la gestion du clavier
     */
    setupKeyboardHandling() {
        // Navigation au clavier dans les menus
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                this.handleTabNavigation(e);
            }
        });
        
        // Raccourcis clavier
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + M pour toggle sidebar
            if ((e.ctrlKey || e.metaKey) && e.key === 'm' && this.isMobile()) {
                e.preventDefault();
                this.toggleSidebar();
            }
        });
    }
    
    /**
     * Gère la navigation par tabulation
     */
    handleTabNavigation(e) {
        const focusableElements = document.querySelectorAll(
            'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
        }
    }
    
    /**
     * Configure les optimisations de scroll
     */
    setupScrollOptimizations() {
        let scrollTimeout;
        
        window.addEventListener('scroll', () => {
            // Masquer les tooltips pendant le scroll
            document.querySelectorAll('.tooltip.show').forEach(tooltip => {
                tooltip.classList.remove('show');
            });
            
            // Indicateur de scroll pour mobile
            if (this.isMobile()) {
                document.body.classList.add('scrolling');
                
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    document.body.classList.remove('scrolling');
                }, 150);
            }
        }, { passive: true });
    }
    
    /**
     * Configure les gestes mobiles
     */
    setupMobileGestures() {
        if (!this.isTouchDevice) return;
        
        let touchStartX = 0;
        let touchStartY = 0;
        let touchEndX = 0;
        let touchEndY = 0;
        
        document.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
            touchStartY = e.changedTouches[0].screenY;
        }, { passive: true });
        
        document.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            touchEndY = e.changedTouches[0].screenY;
            this.handleSwipeGesture();
        }, { passive: true });
        
        const handleSwipeGesture = () => {
            const deltaX = touchEndX - touchStartX;
            const deltaY = touchEndY - touchStartY;
            const minSwipeDistance = 50;
            
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > minSwipeDistance) {
                if (deltaX > 0 && touchStartX < 50) {
                    // Swipe vers la droite depuis le bord gauche - ouvrir sidebar
                    this.openSidebar();
                } else if (deltaX < 0 && this.sidebarOpen) {
                    // Swipe vers la gauche - fermer sidebar
                    this.closeSidebar();
                }
            }
        };
        
        this.handleSwipeGesture = handleSwipeGesture;
    }
    
    /**
     * Optimise l'interface pour mobile
     */
    optimizeForMobile() {
        // Réduire le padding des cartes
        document.querySelectorAll('.card').forEach(card => {
            card.classList.add('mobile-optimized');
        });
        
        // Adapter les tableaux
        document.querySelectorAll('table').forEach(table => {
            if (!table.closest('.table-responsive')) {
                const wrapper = document.createElement('div');
                wrapper.className = 'table-responsive';
                table.parentNode.insertBefore(wrapper, table);
                wrapper.appendChild(table);
            }
        });
        
        // Adapter les formulaires
        document.querySelectorAll('.form-row').forEach(row => {
            row.classList.add('mobile-stack');
        });
    }
    
    /**
     * Optimise l'interface pour desktop
     */
    optimizeForDesktop() {
        // Restaurer le padding normal
        document.querySelectorAll('.card').forEach(card => {
            card.classList.remove('mobile-optimized');
        });
        
        // Restaurer les formulaires
        document.querySelectorAll('.form-row').forEach(row => {
            row.classList.remove('mobile-stack');
        });
    }
    
    /**
     * Gère le redimensionnement de la fenêtre
     */
    handleResize() {
        this.updateBreakpoint();
        this.updateViewportHeight();
        
        // Fermer la sidebar si on passe en desktop
        if (!this.isMobile() && this.sidebarOpen) {
            this.closeSidebar();
        }
    }
    
    /**
     * Gère le changement d'orientation
     */
    handleOrientationChange() {
        this.updateViewportHeight();
        
        // Fermer les modales en orientation paysage sur mobile
        if (this.isMobile() && this.isLandscape) {
            document.querySelectorAll('.modal.show').forEach(modal => {
                const closeBtn = modal.querySelector('.btn-close, [data-dismiss="modal"]');
                if (closeBtn) {
                    closeBtn.click();
                }
            });
        }
    }
    
    /**
     * Met à jour la hauteur de viewport (fix iOS)
     */
    updateViewportHeight() {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }
    
    /**
     * Utilitaires de débounce
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * Vérifie si on est sur mobile
     */
    isMobile() {
        return this.currentBreakpoint === 'xs' || this.currentBreakpoint === 'sm';
    }
    
    /**
     * Vérifie si on est sur tablette
     */
    isTablet() {
        return this.currentBreakpoint === 'md';
    }
    
    /**
     * Vérifie si on est sur desktop
     */
    isDesktop() {
        return this.currentBreakpoint === 'lg' || this.currentBreakpoint === 'xl' || this.currentBreakpoint === 'xxl';
    }
    
    /**
     * Obtient le breakpoint actuel
     */
    getCurrentBreakpoint() {
        return this.currentBreakpoint;
    }
    
    /**
     * Vérifie si un breakpoint donné est actif
     */
    isBreakpoint(breakpoint) {
        return this.currentBreakpoint === breakpoint;
    }
    
    /**
     * Vérifie si on est au-dessus d'un breakpoint donné
     */
    isBreakpointUp(breakpoint) {
        const breakpointOrder = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl'];
        const currentIndex = breakpointOrder.indexOf(this.currentBreakpoint);
        const targetIndex = breakpointOrder.indexOf(breakpoint);
        return currentIndex >= targetIndex;
    }
    
    /**
     * Vérifie si on est en-dessous d'un breakpoint donné
     */
    isBreakpointDown(breakpoint) {
        const breakpointOrder = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl'];
        const currentIndex = breakpointOrder.indexOf(this.currentBreakpoint);
        const targetIndex = breakpointOrder.indexOf(breakpoint);
        return currentIndex <= targetIndex;
    }
}

// CSS supplémentaire pour les optimisations mobiles
const mobileOptimizationCSS = `
/* Optimisations tactiles */
.touch-device .btn,
.touch-device .nav-link,
.touch-device .dropdown-toggle {
    min-height: 44px !important;
    min-width: 44px !important;
}

/* Overlay sidebar mobile */
.sidebar-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1050;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
}

.sidebar-overlay.active {
    opacity: 1;
    visibility: visible;
}

/* États de scroll */
.scrolling .tooltip,
.scrolling .dropdown-menu {
    opacity: 0 !important;
}

/* Optimisations mobile pour cartes */
.mobile-optimized {
    border-radius: var(--border-radius) !important;
    margin-bottom: var(--spacing-sm) !important;
}

/* Stack formulaires sur mobile */
.mobile-stack {
    flex-direction: column !important;
}

.mobile-stack .form-group {
    margin-right: 0 !important;
    margin-bottom: var(--spacing-sm) !important;
}

/* Fix hauteur viewport iOS */
.app-container {
    min-height: 100vh;
    min-height: calc(var(--vh, 1vh) * 100);
}

/* Indicateurs visuels pour le debug responsive */
.debug-responsive::before {
    content: attr(data-breakpoint);
    position: fixed;
    top: 10px;
    right: 10px;
    background: var(--primary-color);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    z-index: 10000;
    pointer-events: none;
}

/* Styles pour différents breakpoints */
.breakpoint-xs .debug-responsive::before { content: 'XS'; }
.breakpoint-sm .debug-responsive::before { content: 'SM'; }
.breakpoint-md .debug-responsive::before { content: 'MD'; }
.breakpoint-lg .debug-responsive::before { content: 'LG'; }
.breakpoint-xl .debug-responsive::before { content: 'XL'; }
.breakpoint-xxl .debug-responsive::before { content: 'XXL'; }
`;

// Injecter le CSS
const style = document.createElement('style');
style.textContent = mobileOptimizationCSS;
document.head.appendChild(style);

// Initialiser le gestionnaire responsive
const responsiveManager = new ResponsiveManager();

// Export pour utilisation externe
window.ResponsiveManager = ResponsiveManager;
window.responsiveManager = responsiveManager;