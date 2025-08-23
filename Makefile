# =============================================================================
# FINAGENT - Makefile
# =============================================================================
# Automatisation des tâches de développement pour FinAgent

.PHONY: help install install-dev test test-unit test-integration test-cov lint format clean docs build release deploy

# Variables
PYTHON := python
POETRY := poetry
PYTEST := pytest
BLACK := black
RUFF := ruff
MYPY := mypy

# Couleurs pour l'affichage
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# =============================================================================
# AIDE
# =============================================================================

help: ## Affiche cette aide
	@echo "$(GREEN)🤖 FinAgent - Commandes Make Disponibles$(NC)"
	@echo ""
	@echo "$(YELLOW)📦 Installation:$(NC)"
	@grep -E '^install.*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🧪 Tests:$(NC)"
	@grep -E '^test.*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🎨 Qualité de Code:$(NC)"
	@grep -E '^(lint|format|check).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)📚 Documentation:$(NC)"
	@grep -E '^docs.*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🚀 Build & Release:$(NC)"
	@grep -E '^(build|clean|release).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)🔧 Utilitaires:$(NC)"
	@grep -E '^(setup|init|check).*:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# INSTALLATION
# =============================================================================

install: ## Installation complète avec Poetry
	@echo "$(GREEN)📦 Installation de FinAgent...$(NC)"
	$(POETRY) install
	@echo "$(GREEN)✅ Installation terminée!$(NC)"

install-dev: install ## Installation avec dépendances de développement
	@echo "$(GREEN)🛠️ Installation des outils de développement...$(NC)"
	$(POETRY) install --with dev
	pre-commit install
	@echo "$(GREEN)✅ Environnement de développement prêt!$(NC)"

install-pip: ## Installation avec pip (alternative)
	@echo "$(YELLOW)⚠️ Installation avec pip (Poetry recommandé)$(NC)"
	pip install -r requirements.txt
	pip install -e .

# =============================================================================
# TESTS
# =============================================================================

test: ## Lance tous les tests
	@echo "$(GREEN)🧪 Lancement de tous les tests...$(NC)"
	$(POETRY) run $(PYTEST) tests/ -v

test-unit: ## Lance les tests unitaires seulement
	@echo "$(GREEN)🔬 Tests unitaires...$(NC)"
	$(POETRY) run $(PYTEST) tests/unit/ -v

test-integration: ## Lance les tests d'intégration seulement
	@echo "$(GREEN)🔗 Tests d'intégration...$(NC)"
	$(POETRY) run $(PYTEST) tests/integration/ -v

test-security: ## Lance les tests de sécurité
	@echo "$(GREEN)🛡️ Tests de sécurité...$(NC)"
	$(POETRY) run $(PYTEST) tests/security/ -v

test-cov: ## Lance les tests avec couverture de code
	@echo "$(GREEN)📊 Tests avec couverture...$(NC)"
	$(POETRY) run $(PYTEST) --cov=finagent --cov-report=html --cov-report=term-missing
	@echo "$(YELLOW)📈 Rapport de couverture généré dans htmlcov/$(NC)"

test-watch: ## Lance les tests en mode watch (relance automatique)
	@echo "$(GREEN)👀 Tests en mode watch...$(NC)"
	$(POETRY) run $(PYTEST) tests/ -v --watch

# =============================================================================
# QUALITÉ DE CODE
# =============================================================================

lint: ## Lance tous les outils de linting
	@echo "$(GREEN)🔍 Linting du code...$(NC)"
	$(POETRY) run $(RUFF) check finagent tests
	$(POETRY) run $(MYPY) finagent
	@echo "$(GREEN)✅ Linting terminé!$(NC)"

format: ## Formate automatiquement le code
	@echo "$(GREEN)🎨 Formatage du code...$(NC)"
	$(POETRY) run $(BLACK) finagent tests
	$(POETRY) run $(RUFF) check --fix finagent tests
	@echo "$(GREEN)✅ Code formaté!$(NC)"

check: lint test-unit ## Vérification complète (lint + tests unitaires)
	@echo "$(GREEN)✅ Vérification complète terminée!$(NC)"

check-all: lint test ## Vérification exhaustive (lint + tous les tests)
	@echo "$(GREEN)✅ Vérification exhaustive terminée!$(NC)"

# =============================================================================
# DOCUMENTATION
# =============================================================================

docs: ## Génère la documentation
	@echo "$(GREEN)📚 Génération de la documentation...$(NC)"
	# TODO: Implémenter la génération de docs (Sphinx/MkDocs)
	@echo "$(YELLOW)💡 Documentation à implémenter$(NC)"

docs-serve: ## Lance le serveur de documentation
	@echo "$(GREEN)🌐 Serveur de documentation...$(NC)"
	# TODO: Implémenter le serveur de docs
	@echo "$(YELLOW)💡 Serveur de documentation à implémenter$(NC)"

# =============================================================================
# NETTOYAGE
# =============================================================================

clean: ## Nettoie les fichiers temporaires
	@echo "$(GREEN)🧹 Nettoyage...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	@echo "$(GREEN)✅ Nettoyage terminé!$(NC)"

clean-data: ## Nettoie les données locales (ATTENTION: perte de données!)
	@echo "$(RED)⚠️ ATTENTION: Suppression des données locales!$(NC)"
	@read -p "Êtes-vous sûr? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		echo "$(YELLOW)🗑️ Suppression des données...$(NC)"; \
		rm -rf data/cache/* data/logs/* data/exports/* data/backups/*; \
		echo "$(GREEN)✅ Données supprimées!$(NC)"; \
	else \
		echo ""; \
		echo "$(GREEN)❌ Suppression annulée$(NC)"; \
	fi

# =============================================================================
# BUILD ET RELEASE
# =============================================================================

build: clean ## Build le package
	@echo "$(GREEN)🏗️ Build du package...$(NC)"
	$(POETRY) build
	@echo "$(GREEN)✅ Package créé dans dist/$(NC)"

release-check: ## Vérifie que tout est prêt pour une release
	@echo "$(GREEN)🔍 Vérification pre-release...$(NC)"
	$(POETRY) run $(PYTEST) tests/
	$(POETRY) run $(RUFF) check finagent tests
	$(POETRY) run $(MYPY) finagent
	@echo "$(GREEN)✅ Prêt pour la release!$(NC)"

release: release-check build ## Prépare une release complète
	@echo "$(GREEN)🚀 Préparation de la release...$(NC)"
	# TODO: Ajouter les étapes de release (git tag, upload PyPI, etc.)
	@echo "$(GREEN)✅ Release préparée!$(NC)"

# =============================================================================
# DÉVELOPPEMENT
# =============================================================================

setup: install-dev ## Configuration complète de l'environnement de développement
	@echo "$(GREEN)⚙️ Configuration de l'environnement...$(NC)"
	mkdir -p data/{cache,logs,backups,exports,strategies}
	cp .env.example .env || echo "$(YELLOW)⚠️ .env existe déjà$(NC)"
	@echo "$(GREEN)✅ Environnement configuré!$(NC)"
	@echo "$(YELLOW)💡 N'oubliez pas de configurer vos clés API dans .env$(NC)"

init: setup ## Initialisation complète du projet (alias pour setup)

run: ## Lance FinAgent
	@echo "$(GREEN)🚀 Lancement de FinAgent...$(NC)"
	$(POETRY) run finagent

run-dev: ## Lance FinAgent en mode développement
	@echo "$(GREEN)🛠️ Lancement en mode développement...$(NC)"
	$(POETRY) run finagent --debug

# =============================================================================
# VALIDATION ET SÉCURITÉ
# =============================================================================

security-check: ## Vérifie les vulnérabilités de sécurité
	@echo "$(GREEN)🔒 Vérification de sécurité...$(NC)"
	$(POETRY) run safety check
	$(POETRY) run bandit -r finagent/

deps-check: ## Vérifie les dépendances
	@echo "$(GREEN)📦 Vérification des dépendances...$(NC)"
	$(POETRY) show --outdated

# =============================================================================
# UTILITAIRES
# =============================================================================

shell: ## Lance un shell Poetry
	$(POETRY) shell

version: ## Affiche la version
	@echo "$(GREEN)FinAgent version:$(NC)"
	$(POETRY) run finagent --version

info: ## Affiche les informations du projet
	@echo "$(GREEN)📋 Informations du projet:$(NC)"
	@echo "Python: $$(python --version)"
	@echo "Poetry: $$(poetry --version)"
	@echo "Répertoire: $$(pwd)"
	@echo "Git branch: $$(git branch --show-current 2>/dev/null || echo 'Non-git')"

# =============================================================================
# HOOKS ET AUTOMATION
# =============================================================================

pre-commit: format lint test-unit ## Exécute les vérifications pre-commit

ci: lint test test-cov ## Pipeline CI/CD complet
	@echo "$(GREEN)✅ Pipeline CI terminé avec succès!$(NC)"

# =============================================================================
# AIDE CONTEXTUELLE
# =============================================================================

# Affiche l'aide par défaut si aucune cible n'est spécifiée
.DEFAULT_GOAL := help