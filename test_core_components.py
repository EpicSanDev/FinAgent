"""
Test simplifié des composants core de l'agent IA financier.

Ce script teste les composants principaux sans dépendances externes complexes :
- Modèles de données (validation Pydantic)
- Logique métier des composants decision et portfolio
- Intégration des composants entre eux
"""

import asyncio
import logging
import sys
from decimal import Decimal
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from typing import Dict, Any

# Ajouter le projet au path
sys.path.insert(0, str(Path(__file__).parent))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockOpenBBProvider:
    """Mock du provider OpenBB pour les tests."""
    
    async def initialize(self):
        """Initialise le mock provider."""
        pass
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Retourne un prix simulé."""
        # Prix simulés pour les tests
        mock_prices = {
            'AAPL': 175.50,
            'MSFT': 335.20,
            'GOOGL': 125.80,
            'TSLA': 225.40,
            'NVDA': 450.30
        }
        
        return {
            'symbol': symbol,
            'price': mock_prices.get(symbol, 100.0),
            'volume': 1000000,
            'timestamp': datetime.now()
        }
    
    async def get_historical_data(self, symbol: str, period: str = "1y", interval: str = "1d"):
        """Retourne des données historiques simulées."""
        import random
        import pandas as pd
        
        # Générer 30 jours de données simulées
        dates = [datetime.now() - timedelta(days=i) for i in range(30)]
        dates.reverse()
        
        base_price = 100.0
        data = []
        
        for date in dates:
            # Simulation de données OHLCV
            open_price = base_price + random.uniform(-5, 5)
            high_price = open_price + random.uniform(0, 10)
            low_price = open_price - random.uniform(0, 10)
            close_price = open_price + random.uniform(-8, 8)
            volume = random.randint(500000, 2000000)
            
            data.append({
                'date': date,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            base_price = close_price
        
        return data
    
    async def close(self):
        """Ferme le mock provider."""
        pass


class MockAIService:
    """Mock des services IA pour les tests."""
    
    async def analyze_market_data(self, symbol: str, data: Dict[str, Any]) -> str:
        """Analyse simulée des données de marché."""
        return f"Analyse technique pour {symbol}: Tendance haussière modérée avec signal d'achat."
    
    async def make_investment_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Décision d'investissement simulée."""
        return {
            'action': 'BUY',
            'confidence': 0.75,
            'reasoning': "Analyse technique positive et fondamentaux solides."
        }


class CoreComponentsTest:
    """Test des composants core."""
    
    def __init__(self):
        """Initialise le test."""
        logger.info("Initialisation du test des composants core")
        
        # Mocks
        self.openbb_provider = MockOpenBBProvider()
        self.ai_service = MockAIService()
        
        # Test symbols
        self.test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        
        logger.info("Test initialisé")
    
    async def test_data_models(self):
        """Test les modèles de données Pydantic."""
        logger.info("\n🔍 Test des modèles de données...")
        
        try:
            from finagent.business.models.decision_models import (
                DecisionSignal, DecisionContext, DecisionResult, 
                MarketAnalysis, RiskAssessment
            )
            from finagent.business.models.portfolio_models import (
                Position, Transaction, Portfolio, PortfolioMetrics,
                PerformanceMetrics, RebalanceRecommendation
            )
            
            # Test DecisionSignal
            signal = DecisionSignal(
                symbol="AAPL",
                signal_type="technical",
                action="BUY",
                strength=0.8,
                confidence=0.75,
                reasoning="RSI oversold",
                timestamp=datetime.now(),
                source="market_analyzer"
            )
            logger.info(f"✓ DecisionSignal créé: {signal.symbol} {signal.action}")
            
            # Test DecisionContext
            context = DecisionContext(
                symbol="AAPL",
                portfolio_id=uuid4(),
                amount=Decimal("10000"),
                decision_type="investment",
                risk_tolerance="moderate",
                time_horizon="medium_term"
            )
            logger.info(f"✓ DecisionContext créé: {context.symbol} ${context.amount}")
            
            # Test Position
            position = Position(
                portfolio_id=uuid4(),
                symbol="AAPL",
                quantity=Decimal("100"),
                average_cost=Decimal("150.00"),
                current_price=Decimal("175.50"),
                market_value=Decimal("17550.00"),
                unrealized_pnl=Decimal("2550.00"),
                realized_pnl=Decimal("0.00"),
                weight=0.25,
                last_updated=datetime.now()
            )
            logger.info(f"✓ Position créée: {position.symbol} {position.quantity} @ ${position.current_price}")
            
            # Test Portfolio
            portfolio = Portfolio(
                id=uuid4(),
                name="Test Portfolio",
                cash=Decimal("50000"),
                total_value=Decimal("100000"),
                positions={},
                target_allocation={'AAPL': 0.25, 'MSFT': 0.25, 'GOOGL': 0.25, 'TSLA': 0.25},
                rebalance_threshold=0.05,
                risk_tolerance="moderate",
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            logger.info(f"✓ Portfolio créé: {portfolio.name} ${portfolio.total_value}")
            
            logger.info("✅ Tous les modèles de données sont valides")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur test modèles: {e}")
            return False
    
    async def test_market_analyzer(self):
        """Test le MarketAnalyzer."""
        logger.info("\n📈 Test du MarketAnalyzer...")
        
        try:
            from finagent.business.decision.market_analyzer import MarketAnalyzer
            
            analyzer = MarketAnalyzer(self.openbb_provider)
            
            # Test analyse d'un symbole
            analysis = await analyzer.analyze_symbol("AAPL")
            
            if analysis:
                logger.info(f"✓ Analyse AAPL: tendance {analysis.trend_direction}")
                logger.info(f"  Support: ${analysis.support_level:.2f}")
                logger.info(f"  Résistance: ${analysis.resistance_level:.2f}")
                logger.info(f"  Indicateurs: {len(analysis.technical_indicators)} calculés")
                return True
            else:
                logger.warning("⚠️ Aucune analyse retournée")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur test MarketAnalyzer: {e}")
            return False
    
    async def test_signal_aggregator(self):
        """Test le SignalAggregator."""
        logger.info("\n🎯 Test du SignalAggregator...")
        
        try:
            from finagent.business.decision.signal_aggregator import SignalAggregator
            from finagent.business.models.decision_models import DecisionSignal
            
            aggregator = SignalAggregator()
            
            # Créer des signaux de test
            signals = [
                DecisionSignal(
                    symbol="AAPL",
                    signal_type="technical",
                    action="BUY",
                    strength=0.8,
                    confidence=0.75,
                    reasoning="RSI oversold",
                    timestamp=datetime.now(),
                    source="technical_analysis"
                ),
                DecisionSignal(
                    symbol="AAPL",
                    signal_type="fundamental",
                    action="BUY",
                    strength=0.6,
                    confidence=0.65,
                    reasoning="Strong earnings",
                    timestamp=datetime.now(),
                    source="fundamental_analysis"
                )
            ]
            
            # Agréger les signaux
            aggregation = await aggregator.aggregate_signals(signals)
            
            if aggregation:
                logger.info(f"✓ Agrégation: {aggregation.final_action} "
                          f"(confiance: {aggregation.consensus_confidence:.2f})")
                logger.info(f"  Signaux traités: {len(aggregation.processed_signals)}")
                return True
            else:
                logger.warning("⚠️ Aucune agrégation retournée")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur test SignalAggregator: {e}")
            return False
    
    async def test_risk_evaluator(self):
        """Test le RiskEvaluator."""
        logger.info("\n⚠️ Test du RiskEvaluator...")
        
        try:
            from finagent.business.decision.risk_evaluator import RiskEvaluator
            from finagent.business.models.portfolio_models import Portfolio
            
            evaluator = RiskEvaluator(self.openbb_provider)
            
            # Créer un portefeuille de test
            portfolio = Portfolio(
                id=uuid4(),
                name="Test Portfolio",
                cash=Decimal("50000"),
                total_value=Decimal("100000"),
                positions={},
                target_allocation={'AAPL': 0.4, 'MSFT': 0.3, 'GOOGL': 0.3},
                rebalance_threshold=0.05,
                risk_tolerance="moderate",
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            # Évaluer le risque
            assessment = await evaluator.evaluate_portfolio_risk(portfolio)
            
            if assessment:
                logger.info(f"✓ Évaluation risque: niveau {assessment.risk_level}")
                logger.info(f"  Score: {assessment.risk_score:.2f}")
                logger.info(f"  VaR: {assessment.value_at_risk:.2%}")
                logger.info(f"  Recommandations: {len(assessment.recommendations)}")
                return True
            else:
                logger.warning("⚠️ Aucune évaluation retournée")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur test RiskEvaluator: {e}")
            return False
    
    async def test_position_manager(self):
        """Test le PositionManager."""
        logger.info("\n💼 Test du PositionManager...")
        
        try:
            from finagent.business.portfolio.position_manager import PositionManager
            from finagent.business.models.portfolio_models import Transaction, TransactionType
            
            manager = PositionManager()
            
            # Créer des transactions de test
            portfolio_id = uuid4()
            
            transactions = [
                Transaction(
                    portfolio_id=portfolio_id,
                    symbol="AAPL",
                    transaction_type=TransactionType.BUY,
                    quantity=Decimal("100"),
                    price=Decimal("150.00"),
                    timestamp=datetime.now() - timedelta(days=30),
                    fees=Decimal("9.99")
                ),
                Transaction(
                    portfolio_id=portfolio_id,
                    symbol="AAPL",
                    transaction_type=TransactionType.BUY,
                    quantity=Decimal("50"),
                    price=Decimal("160.00"),
                    timestamp=datetime.now() - timedelta(days=15),
                    fees=Decimal("9.99")
                )
            ]
            
            # Calculer les positions
            positions = await manager.calculate_positions(transactions)
            
            if positions and "AAPL" in positions:
                position = positions["AAPL"]
                logger.info(f"✓ Position AAPL: {position.quantity} @ ${position.average_cost:.2f}")
                logger.info(f"  Coût total: ${position.total_cost:.2f}")
                logger.info(f"  P&L réalisé: ${position.realized_pnl:.2f}")
                return True
            else:
                logger.warning("⚠️ Aucune position calculée")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur test PositionManager: {e}")
            return False
    
    async def test_performance_tracker(self):
        """Test le PerformanceTracker."""
        logger.info("\n📊 Test du PerformanceTracker...")
        
        try:
            from finagent.business.portfolio.performance_tracker import PerformanceTracker
            
            tracker = PerformanceTracker()
            
            # Créer des données de performance simulées
            portfolio_id = uuid4()
            
            # Simuler des valeurs historiques
            historical_values = []
            base_value = 100000.0
            
            for i in range(30):  # 30 jours
                date = datetime.now() - timedelta(days=30-i)
                # Simulation d'une croissance avec volatilité
                daily_return = (i * 0.003) + ((-1) ** i) * 0.01  # +0.3% par jour avec volatilité
                base_value *= (1 + daily_return)
                
                historical_values.append({
                    'date': date,
                    'total_value': Decimal(str(base_value)),
                    'cash': Decimal("10000"),
                    'positions_value': Decimal(str(base_value - 10000))
                })
            
            # Calculer les métriques
            metrics = await tracker.calculate_performance_metrics(portfolio_id, historical_values)
            
            if metrics:
                logger.info(f"✓ Métriques calculées:")
                logger.info(f"  Rendement total: {metrics.total_return:.2%}")
                logger.info(f"  Volatilité: {metrics.volatility:.2%}")
                logger.info(f"  Ratio Sharpe: {metrics.sharpe_ratio:.3f}")
                logger.info(f"  Drawdown max: {metrics.max_drawdown:.2%}")
                return True
            else:
                logger.warning("⚠️ Aucune métrique calculée")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur test PerformanceTracker: {e}")
            return False
    
    async def test_rebalancer(self):
        """Test le Rebalancer."""
        logger.info("\n⚖️ Test du Rebalancer...")
        
        try:
            from finagent.business.portfolio.rebalancer import Rebalancer
            from finagent.business.models.portfolio_models import Portfolio, Position
            
            rebalancer = Rebalancer(self.openbb_provider)
            
            # Créer un portefeuille déséquilibré pour le test
            portfolio_id = uuid4()
            
            # Positions actuelles (déséquilibrées)
            positions = {
                "AAPL": Position(
                    portfolio_id=portfolio_id,
                    symbol="AAPL",
                    quantity=Decimal("200"),
                    average_cost=Decimal("150.00"),
                    current_price=Decimal("175.50"),
                    market_value=Decimal("35100.00"),
                    unrealized_pnl=Decimal("5100.00"),
                    realized_pnl=Decimal("0.00"),
                    weight=0.35,  # 35% au lieu de 25% cible
                    last_updated=datetime.now()
                )
            }
            
            portfolio = Portfolio(
                id=portfolio_id,
                name="Test Rebalance Portfolio",
                cash=Decimal("40000"),
                total_value=Decimal("100000"),
                positions=positions,
                active_positions=positions,
                target_allocation={'AAPL': 0.25, 'MSFT': 0.25, 'GOOGL': 0.25, 'TSLA': 0.25},
                rebalance_threshold=0.05,
                risk_tolerance="moderate",
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            # Analyser le rééquilibrage
            recommendation = await rebalancer.analyze_portfolio(portfolio)
            
            if recommendation:
                logger.info(f"✓ Recommandation de rééquilibrage:")
                logger.info(f"  Type: {recommendation.rebalance_type}")
                logger.info(f"  Actions: {len(recommendation.actions)}")
                logger.info(f"  Coût estimé: ${recommendation.estimated_cost:.2f}")
                logger.info(f"  Raison: {recommendation.reason}")
                return True
            else:
                logger.info("✓ Aucun rééquilibrage nécessaire")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur test Rebalancer: {e}")
            return False
    
    async def run_all_tests(self):
        """Lance tous les tests."""
        logger.info("🚀 Début des tests des composants core")
        
        start_time = datetime.now()
        results = {}
        
        try:
            # Initialiser les mocks
            await self.openbb_provider.initialize()
            
            # Lancer les tests
            tests = [
                ("Modèles de données", self.test_data_models),
                ("MarketAnalyzer", self.test_market_analyzer),
                ("SignalAggregator", self.test_signal_aggregator),
                ("RiskEvaluator", self.test_risk_evaluator),
                ("PositionManager", self.test_position_manager),
                ("PerformanceTracker", self.test_performance_tracker),
                ("Rebalancer", self.test_rebalancer),
            ]
            
            for test_name, test_func in tests:
                try:
                    result = await test_func()
                    results[test_name] = result
                except Exception as e:
                    logger.error(f"❌ Échec {test_name}: {e}")
                    results[test_name] = False
            
            # Résumé
            end_time = datetime.now()
            duration = end_time - start_time
            
            passed = sum(1 for r in results.values() if r)
            total = len(results)
            
            logger.info(f"\n📋 Résumé des tests:")
            logger.info(f"⏱️ Durée: {duration.total_seconds():.1f} secondes")
            logger.info(f"✅ Réussis: {passed}/{total}")
            
            for test_name, result in results.items():
                status = "✅" if result else "❌"
                logger.info(f"  {status} {test_name}")
            
            if passed == total:
                logger.info("\n🎉 Tous les tests sont passés avec succès!")
                return True
            else:
                logger.warning(f"\n⚠️ {total - passed} test(s) ont échoué")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors des tests: {e}")
            return False
        
        finally:
            await self.openbb_provider.close()


async def main():
    """Point d'entrée principal."""
    
    test = CoreComponentsTest()
    
    try:
        success = await test.run_all_tests()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Tests interrompus par l'utilisateur")
        return 1
        
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)