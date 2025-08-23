"""
Test d'intégration des composants core de l'agent IA financier.

Ce script teste l'intégration complète des modules :
- Decision Engine (moteur de décision)
- Portfolio Management (gestion de portefeuille)
- Market Analysis (analyse de marché)
- Risk Evaluation (évaluation des risques)
"""

import asyncio
import logging
import sys
from decimal import Decimal
from datetime import datetime, timedelta
from pathlib import Path

# Ajouter le projet au path
sys.path.insert(0, str(Path(__file__).parent))

from finagent.business.decision import (
    DecisionEngine,
    MarketAnalyzer,
    SignalAggregator,
    RiskEvaluator
)
from finagent.business.portfolio import (
    PortfolioManager,
    PositionManager,
    PerformanceTracker,
    Rebalancer
)
from finagent.business.models.decision_models import DecisionContext
from finagent.business.models.portfolio_models import Portfolio, Transaction, TransactionType
from finagent.data.providers.openbb_provider import OpenBBProvider
from finagent.ai.services.analysis_service import AnalysisService
from finagent.ai.services.decision_service import DecisionService
from finagent.ai.memory.memory_manager import MemoryManager
from finagent.strategies.strategy_manager import StrategyManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CoreIntegrationTest:
    """Test d'intégration des composants core."""
    
    def __init__(self):
        """Initialise le test d'intégration."""
        logger.info("Initialisation du test d'intégration")
        
        # Providers et services
        self.openbb_provider = None
        self.analysis_service = None
        self.decision_service = None
        self.memory_manager = None
        self.strategy_manager = None
        
        # Composants decision
        self.market_analyzer = None
        self.signal_aggregator = None
        self.risk_evaluator = None
        self.decision_engine = None
        
        # Composants portfolio
        self.position_manager = None
        self.performance_tracker = None
        self.rebalancer = None
        self.portfolio_manager = None
        
        # Données de test
        self.test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        self.test_portfolio = None
        
        logger.info("Test d'intégration initialisé")
    
    async def setup_services(self):
        """Configure les services de base."""
        logger.info("Configuration des services de base...")
        
        try:
            # Initialiser OpenBB Provider
            self.openbb_provider = OpenBBProvider()
            await self.openbb_provider.initialize()
            logger.info("✓ OpenBB Provider initialisé")
            
            # Services IA (simulation - en prod ils utiliseraient OpenRouter)
            self.analysis_service = AnalysisService()
            self.decision_service = DecisionService()
            logger.info("✓ Services IA initialisés")
            
            # Memory Manager
            self.memory_manager = MemoryManager()
            logger.info("✓ Memory Manager initialisé")
            
            # Strategy Manager
            self.strategy_manager = StrategyManager()
            logger.info("✓ Strategy Manager initialisé")
            
        except Exception as e:
            logger.error(f"Erreur configuration services: {e}")
            raise
    
    async def setup_decision_components(self):
        """Configure les composants de décision."""
        logger.info("Configuration des composants de décision...")
        
        try:
            # Market Analyzer
            self.market_analyzer = MarketAnalyzer(self.openbb_provider)
            logger.info("✓ Market Analyzer initialisé")
            
            # Signal Aggregator
            self.signal_aggregator = SignalAggregator()
            logger.info("✓ Signal Aggregator initialisé")
            
            # Risk Evaluator
            self.risk_evaluator = RiskEvaluator(self.openbb_provider)
            logger.info("✓ Risk Evaluator initialisé")
            
            # Decision Engine
            self.decision_engine = DecisionEngine(
                openbb_provider=self.openbb_provider,
                analysis_service=self.analysis_service,
                decision_service=self.decision_service,
                memory_manager=self.memory_manager,
                strategy_manager=self.strategy_manager,
                market_analyzer=self.market_analyzer,
                signal_aggregator=self.signal_aggregator,
                risk_evaluator=self.risk_evaluator
            )
            logger.info("✓ Decision Engine initialisé")
            
        except Exception as e:
            logger.error(f"Erreur configuration composants décision: {e}")
            raise
    
    async def setup_portfolio_components(self):
        """Configure les composants de portefeuille."""
        logger.info("Configuration des composants de portefeuille...")
        
        try:
            # Position Manager
            self.position_manager = PositionManager()
            logger.info("✓ Position Manager initialisé")
            
            # Performance Tracker
            self.performance_tracker = PerformanceTracker()
            logger.info("✓ Performance Tracker initialisé")
            
            # Rebalancer
            self.rebalancer = Rebalancer(self.openbb_provider)
            logger.info("✓ Rebalancer initialisé")
            
            # Portfolio Manager
            self.portfolio_manager = PortfolioManager(
                openbb_provider=self.openbb_provider,
                position_manager=self.position_manager,
                performance_tracker=self.performance_tracker,
                rebalancer=self.rebalancer
            )
            logger.info("✓ Portfolio Manager initialisé")
            
        except Exception as e:
            logger.error(f"Erreur configuration composants portefeuille: {e}")
            raise
    
    async def create_test_portfolio(self):
        """Crée un portefeuille de test."""
        logger.info("Création du portefeuille de test...")
        
        try:
            # Créer un portefeuille avec allocation cible
            target_allocation = {
                'AAPL': 0.25,   # 25%
                'MSFT': 0.20,   # 20%
                'GOOGL': 0.20,  # 20%
                'TSLA': 0.15,   # 15%
                'NVDA': 0.20    # 20%
            }
            
            self.test_portfolio = await self.portfolio_manager.create_portfolio(
                name="Test Integration Portfolio",
                initial_cash=Decimal("100000"),  # 100k USD
                target_allocation=target_allocation,
                rebalance_threshold=0.05,  # 5%
                risk_tolerance="moderate"
            )
            
            logger.info(f"✓ Portefeuille créé: {self.test_portfolio.name}")
            logger.info(f"  Capital initial: ${self.test_portfolio.cash:,.2f}")
            logger.info(f"  Allocation cible: {target_allocation}")
            
        except Exception as e:
            logger.error(f"Erreur création portefeuille: {e}")
            raise
    
    async def test_market_analysis(self):
        """Test l'analyse de marché."""
        logger.info("\n🔍 Test de l'analyse de marché...")
        
        try:
            results = {}
            
            for symbol in self.test_symbols:
                logger.info(f"Analyse de {symbol}...")
                
                # Analyse technique
                analysis = await self.market_analyzer.analyze_symbol(symbol)
                
                if analysis:
                    results[symbol] = {
                        'trend': analysis.trend_direction,
                        'strength': analysis.trend_strength,
                        'support': analysis.support_level,
                        'resistance': analysis.resistance_level,
                        'indicators': {
                            'rsi': analysis.technical_indicators.get('rsi'),
                            'macd_signal': analysis.technical_indicators.get('macd_signal')
                        }
                    }
                    
                    logger.info(f"  ✓ {symbol}: Tendance {analysis.trend_direction} "
                              f"(force: {analysis.trend_strength:.2f})")
                
                # Pause pour éviter le rate limiting
                await asyncio.sleep(0.5)
            
            logger.info(f"✓ Analyse de marché terminée pour {len(results)} symboles")
            return results
            
        except Exception as e:
            logger.error(f"Erreur test analyse marché: {e}")
            return {}
    
    async def test_decision_making(self):
        """Test le processus de décision."""
        logger.info("\n🧠 Test du processus de décision...")
        
        try:
            decisions = {}
            
            for symbol in self.test_symbols:
                logger.info(f"Décision pour {symbol}...")
                
                # Créer le contexte de décision
                context = DecisionContext(
                    symbol=symbol,
                    portfolio_id=self.test_portfolio.id,
                    amount=Decimal("10000"),  # 10k USD
                    decision_type="investment",
                    risk_tolerance="moderate",
                    time_horizon="medium_term",
                    current_allocation=self.test_portfolio.target_allocation
                )
                
                # Obtenir une décision
                decision = await self.decision_engine.make_decision(context)
                
                if decision:
                    decisions[symbol] = {
                        'action': decision.recommended_action,
                        'confidence': decision.confidence_score,
                        'reasoning': decision.reasoning[:100] + "..." if len(decision.reasoning) > 100 else decision.reasoning
                    }
                    
                    logger.info(f"  ✓ {symbol}: {decision.recommended_action} "
                              f"(confiance: {decision.confidence_score:.2f})")
                
                # Pause pour éviter le rate limiting
                await asyncio.sleep(0.5)
            
            logger.info(f"✓ Processus de décision terminé pour {len(decisions)} symboles")
            return decisions
            
        except Exception as e:
            logger.error(f"Erreur test décision: {e}")
            return {}
    
    async def test_portfolio_operations(self):
        """Test les opérations de portefeuille."""
        logger.info("\n💼 Test des opérations de portefeuille...")
        
        try:
            # Simulation d'achats initiaux
            logger.info("Simulation d'achats initiaux...")
            
            transactions = []
            
            for symbol, weight in self.test_portfolio.target_allocation.items():
                # Calculer le montant d'achat basé sur l'allocation cible
                target_amount = float(self.test_portfolio.cash) * weight
                
                # Récupérer le prix actuel
                try:
                    quote = await self.openbb_provider.get_quote(symbol)
                    price = Decimal(str(quote.get('price', 100)))
                    quantity = Decimal(str(target_amount)) / price
                    
                    # Créer la transaction
                    transaction = Transaction(
                        portfolio_id=self.test_portfolio.id,
                        symbol=symbol,
                        transaction_type=TransactionType.BUY,
                        quantity=quantity,
                        price=price,
                        timestamp=datetime.now(),
                        fees=Decimal("9.99")  # Frais fixes
                    )
                    
                    # Exécuter la transaction
                    await self.portfolio_manager.execute_transaction(
                        self.test_portfolio.id, 
                        transaction
                    )
                    
                    transactions.append(transaction)
                    logger.info(f"  ✓ Achat {symbol}: {quantity:.2f} @ ${price:.2f}")
                    
                except Exception as e:
                    logger.warning(f"Erreur achat {symbol}: {e}")
                    continue
                
                # Pause pour éviter le rate limiting
                await asyncio.sleep(0.5)
            
            # Mettre à jour les prix du portefeuille
            logger.info("Mise à jour des prix...")
            await self.portfolio_manager.update_portfolio_prices(self.test_portfolio.id)
            
            # Calculer les métriques
            logger.info("Calcul des métriques...")
            await self.portfolio_manager.calculate_portfolio_metrics(self.test_portfolio.id)
            
            logger.info(f"✓ {len(transactions)} transactions exécutées")
            logger.info(f"  Valeur totale: ${self.test_portfolio.total_value:,.2f}")
            logger.info(f"  Positions actives: {len(self.test_portfolio.active_positions)}")
            
            return transactions
            
        except Exception as e:
            logger.error(f"Erreur test opérations portefeuille: {e}")
            return []
    
    async def test_performance_tracking(self):
        """Test le suivi de performance."""
        logger.info("\n📊 Test du suivi de performance...")
        
        try:
            # Calculer les métriques de performance
            metrics = await self.performance_tracker.calculate_performance_metrics(
                self.test_portfolio.id
            )
            
            if metrics:
                logger.info("Métriques de performance calculées:")
                logger.info(f"  ✓ Rendement total: {metrics.total_return:.2%}")
                logger.info(f"  ✓ Rendement annualisé: {metrics.annualized_return:.2%}")
                logger.info(f"  ✓ Volatilité: {metrics.volatility:.2%}")
                logger.info(f"  ✓ Ratio de Sharpe: {metrics.sharpe_ratio:.3f}")
                logger.info(f"  ✓ Maximum Drawdown: {metrics.max_drawdown:.2%}")
                
                return metrics
            else:
                logger.warning("Pas de métriques de performance calculées")
                return None
                
        except Exception as e:
            logger.error(f"Erreur test performance: {e}")
            return None
    
    async def test_rebalancing(self):
        """Test le rééquilibrage."""
        logger.info("\n⚖️ Test du rééquilibrage...")
        
        try:
            # Analyser les besoins de rééquilibrage
            recommendation = await self.rebalancer.analyze_portfolio(self.test_portfolio)
            
            if recommendation:
                logger.info("Recommandation de rééquilibrage générée:")
                logger.info(f"  ✓ Type: {recommendation.rebalance_type}")
                logger.info(f"  ✓ Priorité: {recommendation.priority}")
                logger.info(f"  ✓ Actions recommandées: {len(recommendation.actions)}")
                logger.info(f"  ✓ Coût estimé: ${recommendation.estimated_cost:.2f}")
                logger.info(f"  ✓ Raison: {recommendation.reason}")
                
                # Afficher les déviations principales
                major_deviations = {k: v for k, v in recommendation.deviations.items() 
                                  if abs(v) > 0.02}  # > 2%
                
                if major_deviations:
                    logger.info("  Déviations principales:")
                    for symbol, deviation in major_deviations.items():
                        logger.info(f"    {symbol}: {deviation:+.1%}")
                
                return recommendation
            else:
                logger.info("✓ Aucun rééquilibrage nécessaire")
                return None
                
        except Exception as e:
            logger.error(f"Erreur test rééquilibrage: {e}")
            return None
    
    async def run_integration_test(self):
        """Lance le test d'intégration complet."""
        logger.info("🚀 Début du test d'intégration des composants core")
        
        start_time = datetime.now()
        
        try:
            # Configuration des services
            await self.setup_services()
            await self.setup_decision_components()
            await self.setup_portfolio_components()
            
            # Création du portefeuille de test
            await self.create_test_portfolio()
            
            # Tests des composants
            market_analysis = await self.test_market_analysis()
            decisions = await self.test_decision_making()
            transactions = await self.test_portfolio_operations()
            performance = await self.test_performance_tracking()
            rebalancing = await self.test_rebalancing()
            
            # Résumé des résultats
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"\n✅ Test d'intégration terminé avec succès!")
            logger.info(f"⏱️ Durée: {duration.total_seconds():.1f} secondes")
            logger.info(f"📈 Symboles analysés: {len(market_analysis)}")
            logger.info(f"🧠 Décisions prises: {len(decisions)}")
            logger.info(f"💼 Transactions: {len(transactions)}")
            logger.info(f"📊 Performance trackée: {'Oui' if performance else 'Non'}")
            logger.info(f"⚖️ Rééquilibrage: {'Recommandé' if rebalancing else 'Non nécessaire'}")
            
            return {
                'success': True,
                'duration': duration.total_seconds(),
                'market_analysis': market_analysis,
                'decisions': decisions,
                'transactions': len(transactions),
                'performance': performance is not None,
                'rebalancing': rebalancing is not None
            }
            
        except Exception as e:
            logger.error(f"❌ Échec du test d'intégration: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration': (datetime.now() - start_time).total_seconds()
            }
    
    async def cleanup(self):
        """Nettoie les ressources après le test."""
        logger.info("Nettoyage des ressources...")
        
        try:
            if self.openbb_provider:
                await self.openbb_provider.close()
                logger.info("✓ OpenBB Provider fermé")
                
        except Exception as e:
            logger.warning(f"Erreur nettoyage: {e}")


async def main():
    """Point d'entrée principal du test."""
    
    # Créer et lancer le test d'intégration
    test = CoreIntegrationTest()
    
    try:
        result = await test.run_integration_test()
        
        if result['success']:
            logger.info("🎉 Tous les composants core fonctionnent correctement!")
            return 0
        else:
            logger.error("💥 Le test d'intégration a échoué")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Test interrompu par l'utilisateur")
        return 1
        
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return 1
        
    finally:
        await test.cleanup()


if __name__ == "__main__":
    # Lancer le test d'intégration
    exit_code = asyncio.run(main())
    sys.exit(exit_code)