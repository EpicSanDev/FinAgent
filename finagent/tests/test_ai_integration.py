"""
Tests d'intégration du système IA avec OpenRouter.
"""

import asyncio
import os
import sys
from pathlib import Path
import structlog

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from finagent.core.config import Config
from finagent.ai import (
    initialize_ai_system, shutdown_ai_system, get_ai_config,
    FinancialAnalysisRequest, TradingDecisionRequest
)
from finagent.ai.models.base import AIRequest

logger = structlog.get_logger(__name__)


class AIIntegrationTester:
    """Testeur d'intégration IA."""
    
    def __init__(self):
        self.config = None
        self.ai_config = None
    
    async def setup(self):
        """Initialise les composants de test."""
        try:
            # Charger la configuration
            self.config = Config()
            
            # Vérifier les variables d'environnement nécessaires
            if not os.getenv("OPENROUTER_API_KEY"):
                print("❌ Variable d'environnement OPENROUTER_API_KEY manquante")
                print("   Veuillez définir votre clé API OpenRouter:")
                print("   export OPENROUTER_API_KEY=your_key_here")
                return False
            
            # Initialiser le système IA
            print("🔧 Initialisation du système IA...")
            self.ai_config = await initialize_ai_system(self.config)
            
            print("✅ Système IA initialisé avec succès")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    
    async def test_provider_connection(self):
        """Teste la connexion au provider Claude."""
        try:
            print("\n🔍 Test de connexion au provider Claude...")
            
            provider = self.ai_config.get_provider()
            
            # Test simple de connexion
            request = AIRequest(
                prompt="Réponds simplement 'OK' pour confirmer la connexion.",
                model="anthropic/claude-3-haiku-20240307",
                max_tokens=10,
                temperature=0.1
            )
            
            response = await provider.send_request(request)
            
            if response and response.content:
                print(f"✅ Connexion réussie - Réponse: {response.content[:50]}...")
                return True
            else:
                print("❌ Pas de réponse du provider")
                return False
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    async def test_analysis_service(self):
        """Teste le service d'analyse financière."""
        try:
            print("\n📊 Test du service d'analyse financière...")
            
            analysis_service = self.ai_config.get_analysis_service()
            
            # Données de test
            test_data = {
                "symbol": "AAPL",
                "price": 150.00,
                "volume": 1000000,
                "market_cap": 2500000000000,
                "pe_ratio": 25.5,
                "moving_averages": {
                    "ma_20": 148.5,
                    "ma_50": 145.2,
                    "ma_200": 140.8
                }
            }
            
            request = FinancialAnalysisRequest(
                symbol="AAPL",
                market_data=test_data,
                analysis_type="comprehensive",
                time_horizon="medium_term"
            )
            
            response = await analysis_service.analyze_financial_data(request)
            
            if response and response.technical_analysis:
                print("✅ Analyse financière réussie")
                print(f"   - Tendance: {response.technical_analysis.trend}")
                print(f"   - Score: {response.technical_analysis.score}")
                return True
            else:
                print("❌ Échec de l'analyse financière")
                return False
                
        except Exception as e:
            print(f"❌ Erreur d'analyse: {e}")
            return False
    
    async def test_decision_service(self):
        """Teste le service de décision de trading."""
        try:
            print("\n🎯 Test du service de décision de trading...")
            
            decision_service = self.ai_config.get_decision_service()
            
            # Données de test
            analysis_data = {
                "symbol": "AAPL",
                "current_price": 150.00,
                "technical_indicators": {
                    "rsi": 65,
                    "macd": "bullish",
                    "moving_averages": "uptrend"
                },
                "fundamental_metrics": {
                    "pe_ratio": 25.5,
                    "revenue_growth": 0.08
                }
            }
            
            request = TradingDecisionRequest(
                symbol="AAPL",
                analysis_data=analysis_data,
                risk_tolerance="medium",
                investment_horizon="medium_term",
                portfolio_context={}
            )
            
            response = await decision_service.make_trading_decision(request)
            
            if response and response.action:
                print("✅ Décision de trading réussie")
                print(f"   - Action: {response.action}")
                print(f"   - Confiance: {response.confidence}")
                print(f"   - Retour attendu: {response.expected_return:.2%}")
                return True
            else:
                print("❌ Échec de la décision de trading")
                return False
                
        except Exception as e:
            print(f"❌ Erreur de décision: {e}")
            return False
    
    async def test_sentiment_service(self):
        """Teste le service d'analyse de sentiment."""
        try:
            print("\n💭 Test du service d'analyse de sentiment...")
            
            sentiment_service = self.ai_config.get_sentiment_service()
            
            # Données de test
            news_data = [
                "Apple reports strong quarterly earnings beating expectations",
                "Tech stocks rally as market confidence grows",
                "Apple announces new product line with innovative features"
            ]
            
            response = await sentiment_service.analyze_market_sentiment(
                symbol="AAPL",
                news_data=news_data,
                social_media_data=[],
                time_window_hours=24
            )
            
            if response and response.overall_sentiment:
                print("✅ Analyse de sentiment réussie")
                print(f"   - Sentiment global: {response.overall_sentiment}")
                print(f"   - Score: {response.sentiment_score:.2f}")
                return True
            else:
                print("❌ Échec de l'analyse de sentiment")
                return False
                
        except Exception as e:
            print(f"❌ Erreur d'analyse de sentiment: {e}")
            return False
    
    async def test_strategy_service(self):
        """Teste le service d'interprétation de stratégie."""
        try:
            print("\n📋 Test du service d'interprétation de stratégie...")
            
            strategy_service = self.ai_config.get_strategy_service()
            
            # Stratégie de test
            strategy_text = """
            Stratégie Momentum Tech:
            - Acheter des actions tech avec RSI < 30
            - Vendre quand RSI > 70
            - Stop loss à -5%
            - Take profit à +15%
            """
            
            response = await strategy_service.interpret_strategy(
                strategy_text=strategy_text,
                strategy_name="Momentum Tech"
            )
            
            if response and response.parsed_rules:
                print("✅ Interprétation de stratégie réussie")
                print(f"   - Nombre de règles: {len(response.parsed_rules)}")
                print(f"   - Type: {response.strategy_type}")
                return True
            else:
                print("❌ Échec de l'interprétation de stratégie")
                return False
                
        except Exception as e:
            print(f"❌ Erreur d'interprétation: {e}")
            return False
    
    async def test_memory_system(self):
        """Teste le système de mémoire."""
        try:
            print("\n🧠 Test du système de mémoire...")
            
            memory_manager = self.ai_config.get_memory_manager()
            
            # Obtenir les statistiques
            stats = await memory_manager.get_memory_stats()
            
            if stats:
                print("✅ Système de mémoire opérationnel")
                print(f"   - Cache: {stats.get('cache_size', 0)} entrées")
                print(f"   - Persistence: {'activée' if stats.get('persistence_enabled') else 'désactivée'}")
                return True
            else:
                print("❌ Système de mémoire non opérationnel")
                return False
                
        except Exception as e:
            print(f"❌ Erreur du système de mémoire: {e}")
            return False
    
    async def run_integration_tests(self):
        """Lance tous les tests d'intégration."""
        print("🚀 Lancement des tests d'intégration IA/OpenRouter")
        print("=" * 60)
        
        # Initialisation
        setup_success = await self.setup()
        if not setup_success:
            return False
        
        # Tests individuels
        tests = [
            ("Connexion Provider", self.test_provider_connection),
            ("Service d'Analyse", self.test_analysis_service),
            ("Service de Décision", self.test_decision_service),
            ("Service de Sentiment", self.test_sentiment_service),
            ("Service de Stratégie", self.test_strategy_service),
            ("Système de Mémoire", self.test_memory_system),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ Erreur dans {test_name}: {e}")
                results.append((test_name, False))
        
        # Résultats finaux
        print("\n" + "=" * 60)
        print("📋 RÉSULTATS DES TESTS")
        print("=" * 60)
        
        success_count = 0
        for test_name, success in results:
            status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
            print(f"{test_name:.<30} {status}")
            if success:
                success_count += 1
        
        total_tests = len(results)
        success_rate = (success_count / total_tests) * 100
        
        print("-" * 60)
        print(f"Résultat global: {success_count}/{total_tests} tests réussis ({success_rate:.1f}%)")
        
        if success_count == total_tests:
            print("🎉 INTÉGRATION IA/OPENROUTER RÉUSSIE !")
        else:
            print("⚠️  Certains tests ont échoué. Vérifiez la configuration.")
        
        return success_count == total_tests
    
    async def cleanup(self):
        """Nettoie les ressources."""
        try:
            if self.ai_config:
                await shutdown_ai_system()
            print("\n🧹 Nettoyage terminé")
        except Exception as e:
            print(f"⚠️  Erreur lors du nettoyage: {e}")


async def main():
    """Point d'entrée principal."""
    tester = AIIntegrationTester()
    
    try:
        success = await tester.run_integration_tests()
        return 0 if success else 1
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)