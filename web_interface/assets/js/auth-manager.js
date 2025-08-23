/**
 * Authentication Manager - Système d'authentification complet
 * Gère la connexion, inscription, réinitialisation de mot de passe et sécurité
 */

class AuthManager {
    constructor() {
        this.currentForm = 'loginForm';
        this.passwordStrengthRules = {
            minLength: 8,
            hasUppercase: /[A-Z]/,
            hasLowercase: /[a-z]/,
            hasNumbers: /\d/,
            hasSpecialChars: /[!@#$%^&*(),.?":{}|<>]/
        };
        this.apiEndpoint = '/api/auth';
        this.redirectUrl = 'index.html';
        
        this.init();
    }

    /**
     * Initialisation du gestionnaire d'authentification
     */
    init() {
        this.setupEventListeners();
        this.checkAuthState();
        this.handleUrlParams();
        console.log('Auth Manager initialisé');
    }

    /**
     * Configuration des écouteurs d'événements
     */
    setupEventListeners() {
        // Basculement entre les formulaires
        document.querySelectorAll('.switch-form').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = e.target.dataset.target;
                this.switchForm(target);
            });
        });

        // Lien mot de passe oublié
        const forgotLink = document.getElementById('showForgotPassword');
        if (forgotLink) {
            forgotLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchForm('forgotPasswordForm');
            });
        }

        // Basculement de visibilité du mot de passe
        document.querySelectorAll('.password-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.togglePasswordVisibility(e.target.closest('.password-toggle'));
            });
        });

        // Validation des mots de passe en temps réel
        const passwordInputs = ['registerPassword', 'newPassword'];
        passwordInputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('input', () => {
                    this.validatePasswordStrength(input);
                });
            }
        });

        // Validation de confirmation de mot de passe
        const confirmInputs = ['registerConfirmPassword', 'confirmNewPassword'];
        confirmInputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('input', () => {
                    this.validatePasswordConfirmation(input);
                });
            }
        });

        // Soumission des formulaires
        document.getElementById('loginForm')?.addEventListener('submit', (e) => {
            this.handleLogin(e);
        });

        document.getElementById('registerForm')?.addEventListener('submit', (e) => {
            this.handleRegister(e);
        });

        document.getElementById('forgotPasswordForm')?.addEventListener('submit', (e) => {
            this.handleForgotPassword(e);
        });

        document.getElementById('resetPasswordForm')?.addEventListener('submit', (e) => {
            this.handleResetPassword(e);
        });

        // Connexion sociale
        document.getElementById('googleLogin')?.addEventListener('click', () => {
            this.handleSocialLogin('google');
        });

        document.getElementById('microsoftLogin')?.addEventListener('click', () => {
            this.handleSocialLogin('microsoft');
        });

        // Validation en temps réel des champs
        document.querySelectorAll('input[type="email"]').forEach(input => {
            input.addEventListener('blur', () => {
                this.validateEmail(input);
            });
        });

        document.querySelectorAll('input[required]').forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
        });
    }

    /**
     * Basculement entre les formulaires
     */
    switchForm(formId) {
        // Masquer tous les formulaires
        document.querySelectorAll('.auth-form').forEach(form => {
            form.classList.remove('active');
        });

        // Afficher le formulaire cible
        const targetForm = document.getElementById(formId);
        if (targetForm) {
            targetForm.classList.add('active');
            this.currentForm = formId;
            
            // Focus sur le premier champ
            const firstInput = targetForm.querySelector('input');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
            
            // Réinitialiser les erreurs
            this.clearFormErrors(targetForm);
        }
    }

    /**
     * Basculement de la visibilité du mot de passe
     */
    togglePasswordVisibility(button) {
        const targetId = button.dataset.target;
        const input = document.getElementById(targetId);
        const icon = button.querySelector('i');

        if (input && icon) {
            if (input.type === 'password') {
                input.type = 'text';
                icon.className = 'fas fa-eye-slash';
            } else {
                input.type = 'password';
                icon.className = 'fas fa-eye';
            }
        }
    }

    /**
     * Validation de la force du mot de passe
     */
    validatePasswordStrength(input) {
        const password = input.value;
        const strengthContainer = input.closest('.form-group').querySelector('.password-strength');
        
        if (!strengthContainer) return;

        if (password.length === 0) {
            strengthContainer.classList.remove('show');
            return;
        }

        strengthContainer.classList.add('show');
        
        const strength = this.calculatePasswordStrength(password);
        const strengthFill = strengthContainer.querySelector('.strength-fill');
        const strengthText = strengthContainer.querySelector('.strength-text');

        // Mise à jour de la barre de force
        strengthFill.className = `strength-fill ${strength.level}`;
        strengthText.textContent = strength.text;
    }

    /**
     * Calcul de la force du mot de passe
     */
    calculatePasswordStrength(password) {
        let score = 0;
        const checks = {
            length: password.length >= this.passwordStrengthRules.minLength,
            uppercase: this.passwordStrengthRules.hasUppercase.test(password),
            lowercase: this.passwordStrengthRules.hasLowercase.test(password),
            numbers: this.passwordStrengthRules.hasNumbers.test(password),
            special: this.passwordStrengthRules.hasSpecialChars.test(password)
        };

        // Calcul du score
        Object.values(checks).forEach(check => {
            if (check) score++;
        });

        // Bonus pour la longueur
        if (password.length >= 12) score += 0.5;
        if (password.length >= 16) score += 0.5;

        // Détermination du niveau
        if (score < 2) {
            return { level: 'weak', text: 'Mot de passe faible' };
        } else if (score < 3) {
            return { level: 'fair', text: 'Mot de passe acceptable' };
        } else if (score < 4) {
            return { level: 'good', text: 'Mot de passe bon' };
        } else {
            return { level: 'strong', text: 'Mot de passe fort' };
        }
    }

    /**
     * Validation de la confirmation de mot de passe
     */
    validatePasswordConfirmation(confirmInput) {
        const form = confirmInput.closest('form');
        const passwordInput = form.querySelector('input[name="password"]');
        const errorContainer = document.getElementById(confirmInput.id + 'Error');

        if (passwordInput && confirmInput.value && confirmInput.value !== passwordInput.value) {
            this.showFieldError(confirmInput, 'Les mots de passe ne correspondent pas');
        } else {
            this.hideFieldError(confirmInput);
        }
    }

    /**
     * Validation d'email
     */
    validateEmail(input) {
        const email = input.value.trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (email && !emailRegex.test(email)) {
            this.showFieldError(input, 'Format d\'email invalide');
            return false;
        } else {
            this.hideFieldError(input);
            return true;
        }
    }

    /**
     * Validation générique de champ
     */
    validateField(input) {
        const value = input.value.trim();
        const isRequired = input.hasAttribute('required');

        if (isRequired && !value) {
            this.showFieldError(input, 'Ce champ est obligatoire');
            return false;
        }

        // Validations spécifiques par type
        if (input.type === 'email') {
            return this.validateEmail(input);
        }

        if (input.name === 'firstName' || input.name === 'lastName') {
            if (value.length < 2) {
                this.showFieldError(input, 'Minimum 2 caractères');
                return false;
            }
        }

        if (input.name === 'password') {
            if (value.length < this.passwordStrengthRules.minLength) {
                this.showFieldError(input, `Minimum ${this.passwordStrengthRules.minLength} caractères`);
                return false;
            }
        }

        this.hideFieldError(input);
        return true;
    }

    /**
     * Affichage d'erreur de champ
     */
    showFieldError(input, message) {
        const errorContainer = document.getElementById(input.id + 'Error');
        if (errorContainer) {
            errorContainer.textContent = message;
            errorContainer.classList.add('show');
        }
        
        input.style.borderColor = 'var(--error-color)';
    }

    /**
     * Masquage d'erreur de champ
     */
    hideFieldError(input) {
        const errorContainer = document.getElementById(input.id + 'Error');
        if (errorContainer) {
            errorContainer.classList.remove('show');
        }
        
        input.style.borderColor = '';
    }

    /**
     * Réinitialisation des erreurs de formulaire
     */
    clearFormErrors(form) {
        form.querySelectorAll('.field-error').forEach(error => {
            error.classList.remove('show');
        });
        
        form.querySelectorAll('input').forEach(input => {
            input.style.borderColor = '';
        });
    }

    /**
     * Gestion de la connexion
     */
    async handleLogin(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);

        // Validation
        if (!this.validateLoginForm(data)) {
            return;
        }

        // Affichage du loading
        this.setButtonLoading('loginSubmit', true);

        try {
            // Simulation d'appel API
            const response = await this.simulateApiCall('/auth/login', data);
            
            if (response.success) {
                // Stockage du token et des données utilisateur
                this.storeAuthData(response.data);
                
                // Notification de succès
                this.showAlert('success', 'Connexion réussie', 'Redirection en cours...');
                
                // Redirection après un délai
                setTimeout(() => {
                    window.location.href = this.redirectUrl;
                }, 1500);
            } else {
                this.showAlert('error', 'Erreur de connexion', response.message);
            }
        } catch (error) {
            this.showAlert('error', 'Erreur de connexion', 'Une erreur inattendue s\'est produite');
            console.error('Erreur de connexion:', error);
        } finally {
            this.setButtonLoading('loginSubmit', false);
        }
    }

    /**
     * Validation du formulaire de connexion
     */
    validateLoginForm(data) {
        let isValid = true;
        
        if (!data.email || !this.validateEmail(document.getElementById('loginEmail'))) {
            isValid = false;
        }
        
        if (!data.password) {
            this.showFieldError(document.getElementById('loginPassword'), 'Mot de passe requis');
            isValid = false;
        }
        
        return isValid;
    }

    /**
     * Gestion de l'inscription
     */
    async handleRegister(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);

        // Validation
        if (!this.validateRegisterForm(data)) {
            return;
        }

        // Affichage du loading
        this.setButtonLoading('registerSubmit', true);

        try {
            // Simulation d'appel API
            const response = await this.simulateApiCall('/auth/register', data);
            
            if (response.success) {
                this.showAlert('success', 'Compte créé avec succès', 'Vous pouvez maintenant vous connecter');
                this.switchForm('loginForm');
                
                // Pré-remplir l'email
                document.getElementById('loginEmail').value = data.email;
            } else {
                this.showAlert('error', 'Erreur d\'inscription', response.message);
            }
        } catch (error) {
            this.showAlert('error', 'Erreur d\'inscription', 'Une erreur inattendue s\'est produite');
            console.error('Erreur d\'inscription:', error);
        } finally {
            this.setButtonLoading('registerSubmit', false);
        }
    }

    /**
     * Validation du formulaire d'inscription
     */
    validateRegisterForm(data) {
        let isValid = true;
        
        // Validation des champs obligatoires
        const requiredFields = ['firstName', 'lastName', 'email', 'password', 'confirmPassword'];
        requiredFields.forEach(field => {
            const input = document.getElementById('register' + field.charAt(0).toUpperCase() + field.slice(1));
            if (!this.validateField(input)) {
                isValid = false;
            }
        });
        
        // Validation de la confirmation de mot de passe
        if (data.password !== data.confirmPassword) {
            this.showFieldError(document.getElementById('registerConfirmPassword'), 'Les mots de passe ne correspondent pas');
            isValid = false;
        }
        
        // Validation des conditions d'utilisation
        if (!data.acceptTerms) {
            this.showFieldError(document.getElementById('acceptTerms'), 'Vous devez accepter les conditions d\'utilisation');
            isValid = false;
        }
        
        return isValid;
    }

    /**
     * Gestion du mot de passe oublié
     */
    async handleForgotPassword(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);

        // Validation
        if (!data.email || !this.validateEmail(document.getElementById('forgotEmail'))) {
            return;
        }

        // Affichage du loading
        this.setButtonLoading('forgotSubmit', true);

        try {
            // Simulation d'appel API
            const response = await this.simulateApiCall('/auth/forgot-password', data);
            
            if (response.success) {
                this.showAlert('success', 'Email envoyé', 'Vérifiez votre boîte de réception pour le lien de réinitialisation');
            } else {
                this.showAlert('error', 'Erreur', response.message);
            }
        } catch (error) {
            this.showAlert('error', 'Erreur', 'Une erreur inattendue s\'est produite');
            console.error('Erreur mot de passe oublié:', error);
        } finally {
            this.setButtonLoading('forgotSubmit', false);
        }
    }

    /**
     * Gestion de la réinitialisation de mot de passe
     */
    async handleResetPassword(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);

        // Validation
        if (!this.validateResetForm(data)) {
            return;
        }

        // Affichage du loading
        this.setButtonLoading('resetSubmit', true);

        try {
            // Récupération du token depuis l'URL
            const urlParams = new URLSearchParams(window.location.search);
            const token = urlParams.get('token');
            
            if (!token) {
                this.showAlert('error', 'Token invalide', 'Le lien de réinitialisation n\'est pas valide');
                return;
            }

            // Simulation d'appel API
            const response = await this.simulateApiCall('/auth/reset-password', {
                ...data,
                token: token
            });
            
            if (response.success) {
                this.showAlert('success', 'Mot de passe modifié', 'Vous pouvez maintenant vous connecter');
                this.switchForm('loginForm');
            } else {
                this.showAlert('error', 'Erreur', response.message);
            }
        } catch (error) {
            this.showAlert('error', 'Erreur', 'Une erreur inattendue s\'est produite');
            console.error('Erreur réinitialisation:', error);
        } finally {
            this.setButtonLoading('resetSubmit', false);
        }
    }

    /**
     * Validation du formulaire de réinitialisation
     */
    validateResetForm(data) {
        let isValid = true;
        
        const passwordInput = document.getElementById('newPassword');
        const confirmInput = document.getElementById('confirmNewPassword');
        
        if (!this.validateField(passwordInput)) {
            isValid = false;
        }
        
        if (data.password !== data.confirmPassword) {
            this.showFieldError(confirmInput, 'Les mots de passe ne correspondent pas');
            isValid = false;
        }
        
        return isValid;
    }

    /**
     * Gestion de la connexion sociale
     */
    handleSocialLogin(provider) {
        // Simulation de redirection vers le provider OAuth
        this.showAlert('info', 'Redirection', `Redirection vers ${provider} en cours...`);
        
        // Dans un vrai projet, ceci redirigerait vers l'URL OAuth du provider
        setTimeout(() => {
            // Simulation d'une connexion réussie
            const mockUserData = {
                token: 'mock-social-token',
                user: {
                    id: 'social-user-123',
                    email: `user@${provider}.com`,
                    firstName: 'Utilisateur',
                    lastName: provider.charAt(0).toUpperCase() + provider.slice(1),
                    avatar: `https://ui-avatars.com/api/?name=User+${provider}&background=3b82f6&color=fff`
                }
            };
            
            this.storeAuthData(mockUserData);
            this.showAlert('success', 'Connexion réussie', 'Redirection en cours...');
            
            setTimeout(() => {
                window.location.href = this.redirectUrl;
            }, 1500);
        }, 2000);
    }

    /**
     * Stockage des données d'authentification
     */
    storeAuthData(data) {
        // Stockage sécurisé du token
        localStorage.setItem('auth_token', data.token);
        localStorage.setItem('user_data', JSON.stringify(data.user));
        
        // Stockage de la date d'expiration (24h par défaut)
        const expirationTime = new Date().getTime() + (24 * 60 * 60 * 1000);
        localStorage.setItem('auth_expires', expirationTime.toString());
        
        console.log('Données d\'authentification stockées');
    }

    /**
     * Vérification de l'état d'authentification
     */
    checkAuthState() {
        const token = localStorage.getItem('auth_token');
        const expirationTime = localStorage.getItem('auth_expires');
        
        if (token && expirationTime) {
            const now = new Date().getTime();
            if (now < parseInt(expirationTime)) {
                // L'utilisateur est déjà connecté, redirection
                window.location.href = this.redirectUrl;
                return;
            } else {
                // Token expiré, nettoyage
                this.clearAuthData();
            }
        }
    }

    /**
     * Nettoyage des données d'authentification
     */
    clearAuthData() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        localStorage.removeItem('auth_expires');
    }

    /**
     * Gestion des paramètres d'URL
     */
    handleUrlParams() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // Gestion du token de réinitialisation
        if (urlParams.get('token')) {
            this.switchForm('resetPasswordForm');
        }
        
        // Gestion des messages d'erreur ou de succès
        const message = urlParams.get('message');
        const type = urlParams.get('type') || 'info';
        
        if (message) {
            this.showAlert(type, 'Information', decodeURIComponent(message));
        }
    }

    /**
     * Gestion de l'état de loading des boutons
     */
    setButtonLoading(buttonId, loading) {
        const button = document.getElementById(buttonId);
        if (button) {
            if (loading) {
                button.classList.add('loading');
                button.disabled = true;
            } else {
                button.classList.remove('loading');
                button.disabled = false;
            }
        }
    }

    /**
     * Simulation d'appel API
     */
    async simulateApiCall(endpoint, data) {
        // Simulation d'un délai réseau
        await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
        
        // Simulation de réponses API
        if (endpoint === '/auth/login') {
            if (data.email === 'demo@finagent.com' && data.password === 'demo123') {
                return {
                    success: true,
                    data: {
                        token: 'mock-jwt-token-' + Date.now(),
                        user: {
                            id: 'user-123',
                            email: data.email,
                            firstName: 'Demo',
                            lastName: 'User',
                            avatar: 'https://ui-avatars.com/api/?name=Demo+User&background=3b82f6&color=fff'
                        }
                    }
                };
            } else {
                return {
                    success: false,
                    message: 'Email ou mot de passe incorrect'
                };
            }
        }
        
        if (endpoint === '/auth/register') {
            // Simulation d'une inscription réussie
            return {
                success: true,
                data: {
                    message: 'Compte créé avec succès'
                }
            };
        }
        
        if (endpoint === '/auth/forgot-password') {
            return {
                success: true,
                data: {
                    message: 'Email de réinitialisation envoyé'
                }
            };
        }
        
        if (endpoint === '/auth/reset-password') {
            return {
                success: true,
                data: {
                    message: 'Mot de passe réinitialisé avec succès'
                }
            };
        }
        
        return {
            success: false,
            message: 'Endpoint non trouvé'
        };
    }

    /**
     * Affichage d'alertes
     */
    showAlert(type, title, message) {
        const container = document.getElementById('alert-container');
        if (!container) return;

        const alertId = 'alert-' + Date.now();
        const alertHtml = `
            <div id="${alertId}" class="alert ${type}">
                <i class="fas fa-${this.getAlertIcon(type)}"></i>
                <div class="alert-content">
                    <div class="alert-title">${title}</div>
                    <p class="alert-message">${message}</p>
                </div>
                <button class="alert-close" onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        container.insertAdjacentHTML('beforeend', alertHtml);

        // Auto-suppression après 5 secondes
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }

    /**
     * Récupération de l'icône d'alerte selon le type
     */
    getAlertIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        
        return icons[type] || 'info-circle';
    }

    /**
     * Nettoyage et destruction
     */
    destroy() {
        // Nettoyage des écouteurs d'événements si nécessaire
        console.log('Auth Manager détruit');
    }
}

// Export global pour utilisation
window.AuthManager = AuthManager;