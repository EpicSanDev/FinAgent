/**
 * Optimisations spécifiques pour l'expérience mobile
 * Gère les tableaux, graphiques, et interactions tactiles
 */

class MobileOptimizations {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupTableOptimizations();
        this.setupChartOptimizations();
        this.setupFormOptimizations();
        this.setupModalOptimizations();
        this.setupDropdownOptimizations();
        this.setupTooltipOptimizations();
        this.setupPerformanceOptimizations();
        
        // Écouter les changements de breakpoint
        window.addEventListener('breakpointChange', (e) => {
            this.handleBreakpointChange(e.detail);
        });
    }
    
    /**
     * Optimise les tableaux pour mobile
     */
    setupTableOptimizations() {
        const tables = document.querySelectorAll('table');
        
        tables.forEach(table => {
            this.makeTableResponsive(table);
        });
        
        // Observer pour les nouveaux tableaux
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
                        const tables = node.querySelectorAll ? node.querySelectorAll('table') : [];
                        tables.forEach(table => this.makeTableResponsive(table));
                    }
                });
            });
        });
        
        observer.observe(document.body, { childList: true, subtree: true });
    }
    
    /**
     * Rend un tableau responsive
     */
    makeTableResponsive(table) {
        if (table.dataset.responsive) return; // Déjà traité
        
        table.dataset.responsive = 'true';
        
        // Wrapper responsive si pas déjà présent
        if (!table.closest('.table-responsive')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'table-responsive';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
        
        // Ajouter des attributs data pour mobile
        const headers = table.querySelectorAll('thead th');
        const rows = table.querySelectorAll('tbody tr');
        
        headers.forEach((header, index) => {
            const headerText = header.textContent.trim();
            
            rows.forEach(row => {
                const cell = row.cells[index];
                if (cell) {
                    cell.setAttribute('data-label', headerText);
                }
            });
        });
        
        // Créer une version mobile alternative
        this.createMobileTableView(table);
    }
    
    /**
     * Crée une vue mobile alternative pour les tableaux
     */
    createMobileTableView(table) {
        const mobileView = document.createElement('div');
        mobileView.className = 'table-mobile-view d-md-none';
        
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach((row, rowIndex) => {
            const card = document.createElement('div');
            card.className = 'table-mobile-card';
            
            const cells = row.querySelectorAll('td');
            cells.forEach((cell, cellIndex) => {
                const header = table.querySelector(`thead th:nth-child(${cellIndex + 1})`);
                if (header && cell.textContent.trim()) {
                    const item = document.createElement('div');
                    item.className = 'table-mobile-item';
                    
                    const label = document.createElement('span');
                    label.className = 'table-mobile-label';
                    label.textContent = header.textContent.trim();
                    
                    const value = document.createElement('span');
                    value.className = 'table-mobile-value';
                    value.innerHTML = cell.innerHTML;
                    
                    item.appendChild(label);
                    item.appendChild(value);
                    card.appendChild(item);
                }
            });
            
            mobileView.appendChild(card);
        });
        
        table.parentNode.insertBefore(mobileView, table.nextSibling);
    }
    
    /**
     * Optimise les graphiques pour mobile
     */
    setupChartOptimizations() {
        const charts = document.querySelectorAll('.chart-container');
        
        charts.forEach(chart => {
            this.optimizeChart(chart);
        });
    }
    
    /**
     * Optimise un graphique individuel
     */
    optimizeChart(chartContainer) {
        if (chartContainer.dataset.mobileOptimized) return;
        
        chartContainer.dataset.mobileOptimized = 'true';
        
        // Réduire la hauteur sur mobile
        const originalHeight = chartContainer.style.height || '400px';
        chartContainer.dataset.originalHeight = originalHeight;
        
        const updateChartHeight = () => {
            if (window.responsiveManager && window.responsiveManager.isMobile()) {
                chartContainer.style.height = '250px';
            } else {
                chartContainer.style.height = chartContainer.dataset.originalHeight;
            }
        };
        
        updateChartHeight();
        window.addEventListener('breakpointChange', updateChartHeight);
        
        // Simplifier les légendes sur mobile
        const chart = chartContainer.querySelector('canvas');
        if (chart && chart.chart) {
            const originalOptions = { ...chart.chart.options };
            
            window.addEventListener('breakpointChange', (e) => {
                if (e.detail.isMobile) {
                    chart.chart.options.legend.display = false;
                    chart.chart.options.scales.x.display = false;
                    chart.chart.options.plugins.tooltip.enabled = false;
                } else {
                    chart.chart.options = originalOptions;
                }
                chart.chart.update();
            });
        }
    }
    
    /**
     * Optimise les formulaires pour mobile
     */
    setupFormOptimizations() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            this.optimizeForm(form);
        });
    }
    
    /**
     * Optimise un formulaire individuel
     */
    optimizeForm(form) {
        // Grouper les champs liés sur mobile
        const formRows = form.querySelectorAll('.form-row');
        
        formRows.forEach(row => {
            const groups = row.querySelectorAll('.form-group');
            
            if (groups.length > 1) {
                // Créer des accordéons pour les formulaires complexes
                const accordion = document.createElement('div');
                accordion.className = 'mobile-form-accordion d-md-none';
                
                groups.forEach((group, index) => {
                    const label = group.querySelector('label');
                    const input = group.querySelector('input, select, textarea');
                    
                    if (label && input) {
                        const item = document.createElement('div');
                        item.className = 'mobile-form-item';
                        
                        const header = document.createElement('div');
                        header.className = 'mobile-form-header';
                        header.textContent = label.textContent;
                        header.addEventListener('click', () => {
                            item.classList.toggle('active');
                            input.focus();
                        });
                        
                        const content = document.createElement('div');
                        content.className = 'mobile-form-content';
                        content.appendChild(input.cloneNode(true));
                        
                        item.appendChild(header);
                        item.appendChild(content);
                        accordion.appendChild(item);
                    }
                });
                
                row.parentNode.insertBefore(accordion, row);
            }
        });
        
        // Optimiser les inputs pour iOS
        const inputs = form.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], input[type="number"]');
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                if (window.responsiveManager && window.responsiveManager.isMobile()) {
                    // Prévenir le zoom sur iOS
                    input.style.fontSize = '16px';
                    
                    // Scroll vers l'input après un délai
                    setTimeout(() => {
                        input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 300);
                }
            });
        });
    }
    
    /**
     * Optimise les modales pour mobile
     */
    setupModalOptimizations() {
        const modals = document.querySelectorAll('.modal');
        
        modals.forEach(modal => {
            this.optimizeModal(modal);
        });
    }
    
    /**
     * Optimise une modale individuelle
     */
    optimizeModal(modal) {
        const dialog = modal.querySelector('.modal-dialog');
        if (!dialog) return;
        
        // Adapter la position sur mobile
        window.addEventListener('breakpointChange', (e) => {
            if (e.detail.isMobile) {
                dialog.style.margin = '0';
                dialog.style.maxHeight = '95vh';
                dialog.style.borderRadius = '12px 12px 0 0';
                
                // Ajouter un handle de glissement
                if (!dialog.querySelector('.modal-handle')) {
                    const handle = document.createElement('div');
                    handle.className = 'modal-handle';
                    dialog.insertBefore(handle, dialog.firstChild);
                }
            } else {
                dialog.style.margin = '';
                dialog.style.maxHeight = '';
                dialog.style.borderRadius = '';
                
                const handle = dialog.querySelector('.modal-handle');
                if (handle) {
                    handle.remove();
                }
            }
        });
        
        // Gérer le swipe down pour fermer
        let startY = 0;
        let currentY = 0;
        let isDragging = false;
        
        dialog.addEventListener('touchstart', (e) => {
            if (window.responsiveManager && window.responsiveManager.isMobile()) {
                startY = e.touches[0].clientY;
                isDragging = true;
            }
        }, { passive: true });
        
        dialog.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            
            currentY = e.touches[0].clientY;
            const diff = currentY - startY;
            
            if (diff > 0) {
                dialog.style.transform = `translateY(${diff}px)`;
            }
        }, { passive: true });
        
        dialog.addEventListener('touchend', () => {
            if (!isDragging) return;
            
            const diff = currentY - startY;
            isDragging = false;
            
            if (diff > 100) {
                // Fermer la modale
                const closeBtn = modal.querySelector('.btn-close, [data-dismiss="modal"]');
                if (closeBtn) {
                    closeBtn.click();
                }
            } else {
                // Revenir à la position originale
                dialog.style.transform = '';
            }
        });
    }
    
    /**
     * Optimise les dropdowns pour mobile
     */
    setupDropdownOptimizations() {
        const dropdowns = document.querySelectorAll('.dropdown');
        
        dropdowns.forEach(dropdown => {
            this.optimizeDropdown(dropdown);
        });
    }
    
    /**
     * Optimise un dropdown individuel
     */
    optimizeDropdown(dropdown) {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (!toggle || !menu) return;
        
        // Convertir en modal sur mobile
        toggle.addEventListener('click', (e) => {
            if (window.responsiveManager && window.responsiveManager.isMobile()) {
                e.preventDefault();
                e.stopPropagation();
                
                this.showDropdownAsModal(dropdown, menu);
            }
        });
    }
    
    /**
     * Affiche un dropdown comme une modale sur mobile
     */
    showDropdownAsModal(dropdown, menu) {
        const modal = document.createElement('div');
        modal.className = 'dropdown-modal';
        modal.innerHTML = `
            <div class="dropdown-modal-backdrop"></div>
            <div class="dropdown-modal-content">
                <div class="dropdown-modal-header">
                    <h5>Sélectionner une option</h5>
                    <button class="btn-close" type="button"></button>
                </div>
                <div class="dropdown-modal-body">
                    ${menu.innerHTML}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Gérer la fermeture
        const closeModal = () => {
            modal.remove();
        };
        
        modal.querySelector('.btn-close').addEventListener('click', closeModal);
        modal.querySelector('.dropdown-modal-backdrop').addEventListener('click', closeModal);
        
        // Gérer les clics sur les éléments
        modal.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', (e) => {
                // Simuler le clic original
                const originalItem = menu.querySelector(`[href="${item.getAttribute('href')}"], [data-value="${item.dataset.value}"]`);
                if (originalItem) {
                    originalItem.click();
                }
                closeModal();
            });
        });
        
        // Animer l'ouverture
        requestAnimationFrame(() => {
            modal.classList.add('show');
        });
    }
    
    /**
     * Optimise les tooltips pour mobile
     */
    setupTooltipOptimizations() {
        const tooltipElements = document.querySelectorAll('[data-tooltip], [title]');
        
        tooltipElements.forEach(element => {
            // Remplacer les tooltips par des modales sur mobile
            element.addEventListener('touchstart', (e) => {
                if (window.responsiveManager && window.responsiveManager.isMobile()) {
                    e.preventDefault();
                    
                    const tooltipText = element.dataset.tooltip || element.title;
                    if (tooltipText) {
                        this.showTooltipAsModal(tooltipText, element);
                    }
                }
            });
        });
    }
    
    /**
     * Affiche un tooltip comme une modale sur mobile
     */
    showTooltipAsModal(text, element) {
        const modal = document.createElement('div');
        modal.className = 'tooltip-modal';
        modal.innerHTML = `
            <div class="tooltip-modal-backdrop"></div>
            <div class="tooltip-modal-content">
                <p>${text}</p>
                <button class="btn btn-primary btn-sm">OK</button>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const closeModal = () => {
            modal.remove();
        };
        
        modal.querySelector('.tooltip-modal-backdrop').addEventListener('click', closeModal);
        modal.querySelector('button').addEventListener('click', closeModal);
        
        // Auto-fermeture après 3 secondes
        setTimeout(closeModal, 3000);
        
        // Animer l'ouverture
        requestAnimationFrame(() => {
            modal.classList.add('show');
        });
    }
    
    /**
     * Optimisations de performance pour mobile
     */
    setupPerformanceOptimizations() {
        // Lazy loading pour les images
        const images = document.querySelectorAll('img[data-src]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            images.forEach(img => imageObserver.observe(img));
        }
        
        // Réduire les animations sur mobile
        if (window.responsiveManager && window.responsiveManager.isTouchDevice) {
            document.body.classList.add('reduced-animations');
        }
        
        // Optimiser les événements de scroll
        let ticking = false;
        
        const updateScrollPosition = () => {
            // Logique de scroll optimisée
            ticking = false;
        };
        
        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(updateScrollPosition);
                ticking = true;
            }
        }, { passive: true });
    }
    
    /**
     * Gère les changements de breakpoint
     */
    handleBreakpointChange(detail) {
        if (detail.isMobile) {
            this.enableMobileOptimizations();
        } else {
            this.disableMobileOptimizations();
        }
    }
    
    /**
     * Active les optimisations mobiles
     */
    enableMobileOptimizations() {
        document.body.classList.add('mobile-optimized');
        
        // Masquer les tooltips desktop
        document.querySelectorAll('.tooltip').forEach(tooltip => {
            tooltip.style.display = 'none';
        });
        
        // Ajuster les z-index pour mobile
        this.adjustZIndexForMobile();
    }
    
    /**
     * Désactive les optimisations mobiles
     */
    disableMobileOptimizations() {
        document.body.classList.remove('mobile-optimized');
        
        // Restaurer les tooltips
        document.querySelectorAll('.tooltip').forEach(tooltip => {
            tooltip.style.display = '';
        });
    }
    
    /**
     * Ajuste les z-index pour mobile
     */
    adjustZIndexForMobile() {
        const elements = [
            { selector: '.app-header', zIndex: 1000 },
            { selector: '.app-sidebar', zIndex: 1100 },
            { selector: '.sidebar-overlay', zIndex: 1050 },
            { selector: '.modal', zIndex: 1200 },
            { selector: '.dropdown-modal', zIndex: 1300 },
            { selector: '.tooltip-modal', zIndex: 1400 }
        ];
        
        elements.forEach(({ selector, zIndex }) => {
            const element = document.querySelector(selector);
            if (element) {
                element.style.zIndex = zIndex;
            }
        });
    }
}

// CSS pour les optimisations mobiles
const mobileOptimizationStyles = `
/* Table mobile view */
.table-mobile-view {
    display: none;
}

@media (max-width: 767.98px) {
    .table-responsive table {
        display: none;
    }
    
    .table-mobile-view {
        display: block;
    }
    
    .table-mobile-card {
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: var(--spacing-md);
        margin-bottom: var(--spacing-sm);
    }
    
    .table-mobile-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: var(--spacing-xs) 0;
        border-bottom: 1px solid var(--border-color-light);
    }
    
    .table-mobile-item:last-child {
        border-bottom: none;
    }
    
    .table-mobile-label {
        font-weight: var(--font-weight-medium);
        color: var(--text-secondary);
        font-size: var(--font-size-sm);
    }
    
    .table-mobile-value {
        font-weight: var(--font-weight-medium);
        color: var(--text-primary);
        text-align: right;
    }
}

/* Dropdown modal */
.dropdown-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1300;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.dropdown-modal.show {
    opacity: 1;
}

.dropdown-modal-backdrop {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
}

.dropdown-modal-content {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    background: var(--surface-color);
    border-radius: var(--border-radius-lg) var(--border-radius-lg) 0 0;
    max-height: 70vh;
    overflow-y: auto;
    transform: translateY(100%);
    transition: transform 0.3s ease;
}

.dropdown-modal.show .dropdown-modal-content {
    transform: translateY(0);
}

.dropdown-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md);
    border-bottom: 1px solid var(--border-color);
}

.dropdown-modal-body {
    padding: var(--spacing-sm);
}

/* Tooltip modal */
.tooltip-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1400;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.tooltip-modal.show {
    opacity: 1;
}

.tooltip-modal-backdrop {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.3);
}

.tooltip-modal-content {
    background: var(--surface-color);
    padding: var(--spacing-md);
    border-radius: var(--border-radius);
    margin: var(--spacing-md);
    text-align: center;
    box-shadow: var(--shadow-lg);
    transform: scale(0.9);
    transition: transform 0.3s ease;
}

.tooltip-modal.show .tooltip-modal-content {
    transform: scale(1);
}

/* Modal handle */
.modal-handle {
    width: 40px;
    height: 4px;
    background: var(--border-color);
    border-radius: 2px;
    margin: var(--spacing-sm) auto;
    cursor: grab;
}

/* Animations réduites */
.reduced-animations * {
    animation-duration: 0.1s !important;
    transition-duration: 0.1s !important;
}

/* Form mobile accordion */
.mobile-form-accordion {
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    overflow: hidden;
}

.mobile-form-item {
    border-bottom: 1px solid var(--border-color);
}

.mobile-form-item:last-child {
    border-bottom: none;
}

.mobile-form-header {
    padding: var(--spacing-md);
    background: var(--background-secondary);
    cursor: pointer;
    font-weight: var(--font-weight-medium);
    color: var(--text-primary);
}

.mobile-form-content {
    padding: var(--spacing-md);
    display: none;
}

.mobile-form-item.active .mobile-form-content {
    display: block;
}

/* Input focus optimizations */
@media (max-width: 767.98px) {
    input[type="text"]:focus,
    input[type="email"]:focus,
    input[type="password"]:focus,
    input[type="number"]:focus,
    textarea:focus,
    select:focus {
        font-size: 16px !important; /* Prevent zoom on iOS */
    }
}
`;

// Injecter les styles
const styleSheet = document.createElement('style');
styleSheet.textContent = mobileOptimizationStyles;
document.head.appendChild(styleSheet);

// Initialiser les optimisations mobiles
const mobileOptimizations = new MobileOptimizations();

// Export pour utilisation externe
window.MobileOptimizations = MobileOptimizations;
window.mobileOptimizations = mobileOptimizations;