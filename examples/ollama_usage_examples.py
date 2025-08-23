#!/usr/bin/env python3
"""
Exemples d'usage de l'intégration Ollama dans FinAgent

Ce fichier contient des exemples pratiques d'utilisation des différents
modèles Ollama pour diverses tâches financières.
"""

import asyncio
import logging
from typing import Dict, List
from datetime import datetime

from finagent.ai import create_ai_provider, get_ai_factory
from finagent.ai.models.base import ModelType, ProviderType
from finagent.ai.config import AIConfig, OllamaConfig, FallbackStrategy


# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaExamples:
    """Classe contenant les exemples d'usage d'Ollama."""
    
    def __init__(self):
        self.factory = None
    
    async def initialize(self):
        """Initialise la factory AI."""
        self.factory = await get_ai_factory()
        logger.info("Factory AI initialisée")
    
    async def example_basic_usage(self):
        """Exemple d'usage basique avec Ollama."""
        print("\n" + "="*60)
        print("EXEMPLE 1: Usage basique d'Ollama")
        print("="*60)
        
        try:
            # Création d'un provider Ollama
            provider = await create_ai_provider(ProviderType.OLLAMA)
            
            # Test de connectivité
            is_connected = await provider.validate_connection()
            if not is_connected:
                print("❌ Ollama n'est pas disponible")
                return
            
            print("✅ Connexion Ollama établie")
            
            # Génération d'une réponse simple
            prompt = "Qu'est-ce que la diversification d'un portefeuille ?"
            
            print(f"\n📝 Prompt: {prompt}")
            print("\n🤖 Réponse Ollama:")
            
            response = await provider.generate_response(
                prompt,
                model=ModelType.LLAMA3_1_8B,
                max_tokens=500,
                temperature=0.7
            )
            
            print(response)
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    async def example_model_comparison(self):
        """Compare différents modèles Ollama sur la même tâche."""
        print("\n" + "="*60)
        print("EXEMPLE 2: Comparaison de modèles")
        print("="*60)
        
        # Modèles à tester
        models_to_test = [
            ModelType.LLAMA3_1_8B,
            ModelType.MISTRAL_7B,
            ModelType.GEMMA_7B,
            ModelType.PHI3_MINI
        ]
        
        prompt = """
        Analyse les risques d'un investissement en crypto-monnaies.
        Fournis 3 points clés en moins de 100 mots.
        """
        
        provider = await create_ai_provider(ProviderType.OLLAMA)
        
        for model in models_to_test:
            print(f"\n🔍 Test avec {model.value}:")
            print("-" * 40)
            
            try:
                start_time = datetime.now()
                
                response = await provider.generate_response(
                    prompt,
                    model=model,
                    max_tokens=200,
                    temperature=0.5
                )
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                print(f"⏱️  Durée: {duration:.2f}s")
                print(f"📄 Réponse: {response[:200]}...")
                
            except Exception as e:
                print(f"❌ Erreur avec {model.value}: {e}")
    
    async def example_financial_analysis(self):
        """Exemple d'analyse financière complète."""
        print("\n" + "="*60)
        print("EXEMPLE 3: Analyse financière avec Ollama")
        print("="*60)
        
        # Configuration pour analyse financière
        provider = await create_ai_provider(task_type="analysis")
        
        analysis_prompt = """
        Analyse l'action Tesla (TSLA) selon ces critères :

        1. **Performance récente** : Évolution du cours sur 6 mois
        2. **Position concurrentielle** : Avantages vs autres constructeurs EV
        3. **Risques** : Principaux défis et menaces
        4. **Opportunités** : Catalyseurs de croissance potentiels
        5. **Recommandation** : Achat, conservation ou vente avec justification

        Fournis une analyse structurée et objective en français.
        """
        
        print("📊 Analyse de Tesla (TSLA) en cours...")
        
        try:
            response = await provider.generate_response(
                analysis_prompt,
                max_tokens=1200,
                temperature=0.3  # Plus déterministe pour l'analyse
            )
            
            print("\n" + "="*50)
            print("ANALYSE TESLA (TSLA)")
            print("="*50)
            print(response)
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse: {e}")
    
    async def example_portfolio_optimization(self):
        """Exemple d'optimisation de portefeuille."""
        print("\n" + "="*60)
        print("EXEMPLE 4: Optimisation de portefeuille")
        print("="*60)
        
        provider = await create_ai_provider(ProviderType.OLLAMA)
        
        portfolio_prompt = """
        J'ai un portefeuille de 50,000€ avec cette répartition actuelle :
        - Actions tech US: 40% (AAPL, MSFT, GOOGL)
        - Actions européennes: 20% (ASML, SAP)
        - Obligations: 25%
        - Cash: 15%

        Mon profil : 35 ans, horizon 15 ans, tolérance au risque modérée.

        Propose une répartition optimisée avec justifications :
        1. Allocation d'actifs recommandée
        2. Secteurs à renforcer ou réduire
        3. Stratégie de rééquilibrage
        4. Instruments à considérer (ETF, etc.)
        """
        
        print("🎯 Optimisation de portefeuille en cours...")
        
        try:
            response = await provider.generate_response(
                portfolio_prompt,
                model=ModelType.LLAMA3_1_8B,
                max_tokens=1500,
                temperature=0.4
            )
            
            print("\n" + "="*50)
            print("RECOMMANDATIONS D'OPTIMISATION")
            print("="*50)
            print(response)
            
        except Exception as e:
            print(f"❌ Erreur lors de l'optimisation: {e}")
    
    async def example_coding_assistant(self):
        """Exemple d'assistance au développement avec CodeLlama."""
        print("\n" + "="*60)
        print("EXEMPLE 5: Assistant de développement")
        print("="*60)
        
        provider = await create_ai_provider(ProviderType.OLLAMA)
        
        coding_prompt = """
        Écris une fonction Python qui calcule les indicateurs techniques suivants
        pour une série de prix :
        
        1. Moyenne mobile simple (SMA) sur N périodes
        2. RSI (Relative Strength Index)
        3. Bandes de Bollinger
        
        La fonction doit :
        - Accepter une liste de prix et les paramètres
        - Retourner un dictionnaire avec les indicateurs
        - Inclure la gestion d'erreurs
        - Être bien documentée
        """
        
        print("💻 Génération de code avec CodeLlama...")
        
        try:
            response = await provider.generate_response(
                coding_prompt,
                model=ModelType.CODELLAMA_7B,
                max_tokens=1500,
                temperature=0.2  # Très déterministe pour le code
            )
            
            print("\n" + "="*50)
            print("CODE GÉNÉRÉ")
            print("="*50)
            print(response)
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération de code: {e}")
    
    async def example_fallback_strategy(self):
        """Exemple de stratégie de fallback Claude <-> Ollama."""
        print("\n" + "="*60)
        print("EXEMPLE 6: Stratégie de fallback")
        print("="*60)
        
        # Test avec différentes stratégies
        strategies = [
            FallbackStrategy.OLLAMA_TO_CLAUDE,
            FallbackStrategy.CLAUDE_TO_OLLAMA,
            FallbackStrategy.AUTO
        ]
        
        prompt = "Explique l'effet de l'inflation sur les investissements."
        
        for strategy in strategies:
            print(f"\n🔄 Test stratégie: {strategy.value}")
            print("-" * 40)
            
            try:
                # Configuration personnalisée
                config = AIConfig(
                    fallback_strategy=strategy,
                    enable_auto_discovery=True
                )
                
                # Provider avec configuration personnalisée
                provider = await create_ai_provider(
                    task_type="analysis",
                    config=config
                )
                
                response = await provider.generate_response(
                    prompt,
                    max_tokens=300
                )
                
                # Affichage du provider utilisé
                provider_info = getattr(provider, '_provider_type', 'unknown')
                print(f"✅ Provider utilisé: {provider_info}")
                print(f"📝 Réponse (extrait): {response[:150]}...")
                
            except Exception as e:
                print(f"❌ Erreur avec stratégie {strategy.value}: {e}")
    
    async def example_model_discovery(self):
        """Exemple d'utilisation du service de discovery."""
        print("\n" + "="*60)
        print("EXEMPLE 7: Discovery des modèles")
        print("="*60)
        
        try:
            from finagent.ai.services import get_discovery_service
            
            discovery = await get_discovery_service()
            
            # Rafraîchissement des modèles
            print("🔍 Découverte des modèles disponibles...")
            models_info = await discovery.refresh_models()
            
            if models_info:
                print(f"✅ {len(models_info)} modèles détectés:")
                for model_type, info in models_info.items():
                    status = "✅ Disponible" if info.available else "❌ Non disponible"
                    print(f"  - {model_type.value}: {status}")
                    if info.size_mb:
                        print(f"    Taille: {info.size_mb} MB")
            else:
                print("❌ Aucun modèle détecté")
            
            # Recommandations par tâche
            print("\n💡 Recommandations par tâche:")
            tasks = ["analysis", "coding", "conversation", "summarization"]
            
            for task in tasks:
                recommended = discovery.get_recommended_models_for_task(task)
                print(f"  - {task}: {[m.value for m in recommended[:3]]}")
            
            # Test de téléchargement (simulation)
            print("\n📥 Test de téléchargement de modèle...")
            model_to_pull = ModelType.GEMMA_7B
            
            if model_to_pull in [m for m in discovery.get_available_models()]:
                print(f"✅ {model_to_pull.value} déjà disponible")
            else:
                print(f"📥 Téléchargement de {model_to_pull.value}...")
                # success = await discovery.pull_model(model_to_pull)
                # Note: Commenté pour éviter de télécharger automatiquement
                print("💭 (Téléchargement simulé - décommentez pour exécuter)")
        
        except Exception as e:
            print(f"❌ Erreur lors de la discovery: {e}")
    
    async def example_health_monitoring(self):
        """Exemple de monitoring de santé des providers."""
        print("\n" + "="*60)
        print("EXEMPLE 8: Monitoring de santé")
        print("="*60)
        
        try:
            # Statut de santé des providers
            health_status = self.factory.get_provider_health_status()
            
            print("🏥 État de santé des providers:")
            print("-" * 40)
            
            for provider_name, status in health_status.items():
                if status.get("available", False):
                    response_time = status.get("response_time_ms", 0)
                    print(f"✅ {provider_name}: Disponible ({response_time:.1f}ms)")
                    
                    # Informations spécifiques à Ollama
                    if provider_name == "ollama":
                        models_count = status.get("models_available", 0)
                        print(f"   📚 Modèles disponibles: {models_count}")
                else:
                    print(f"❌ {provider_name}: Non disponible")
            
            # Test de connectivité détaillé
            print("\n🔧 Tests de connectivité détaillés:")
            
            # Test Ollama
            try:
                ollama_provider = await create_ai_provider(ProviderType.OLLAMA)
                is_connected = await ollama_provider.validate_connection()
                print(f"  Ollama: {'✅ OK' if is_connected else '❌ Échec'}")
            except Exception as e:
                print(f"  Ollama: ❌ Erreur - {e}")
            
            # Test Claude
            try:
                claude_provider = await create_ai_provider(ProviderType.CLAUDE)
                # Note: Le test de Claude nécessite une API key valide
                print("  Claude: 💭 (Nécessite API key)")
            except Exception as e:
                print(f"  Claude: ❌ Erreur - {e}")
        
        except Exception as e:
            print(f"❌ Erreur lors du monitoring: {e}")
    
    async def run_all_examples(self):
        """Exécute tous les exemples."""
        print("🚀 Démarrage des exemples d'usage Ollama")
        print("=" * 60)
        
        await self.initialize()
        
        examples = [
            self.example_basic_usage,
            self.example_model_comparison,
            self.example_financial_analysis,
            self.example_portfolio_optimization,
            self.example_coding_assistant,
            self.example_fallback_strategy,
            self.example_model_discovery,
            self.example_health_monitoring
        ]
        
        for i, example in enumerate(examples, 1):
            try:
                print(f"\n🔄 Exécution exemple {i}/{len(examples)}...")
                await example()
                print(f"✅ Exemple {i} terminé")
            except Exception as e:
                print(f"❌ Erreur exemple {i}: {e}")
                continue
        
        print("\n" + "="*60)
        print("✅ Tous les exemples ont été exécutés")
