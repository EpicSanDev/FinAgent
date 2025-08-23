"""
Exemple d'utilisation du système de stratégies FinAgent.

Ce fichier démontre comment utiliser le système complet de stratégies,
depuis le chargement des templates jusqu'à l'exécution en temps réel.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Imports du système de stratégies
from finagent.business.strategy.manager import StrategyManager
from finagent.business.strategy.parser import StrategyYAMLParser, StrategyValidator
from finagent.business.strategy.engine import StrategyEngine

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StrategyExampleRunner:
    """
    Classe d'exemple pour démontrer l'utilisation du système de stratégies.
    """
    
    def __init__(self):
        self.strategy_manager = None
        self.templates_dir = Path(__file__).parent.parent / "templates"
        self.strategies_dir = Path("user_strategies")
        
        # Création du répertoire utilisateur
        self.strategies_dir.mkdir(exist_ok=True)
    
    async def initialize(self):
        """Initialise le système de stratégies."""
        logger.info("=== Initialisation du système de stratégies ===")
        
        # Initialisation du gestionnaire
        self.strategy_manager = StrategyManager(
            strategies_directory=str(self.strategies_dir),
            max_concurrent_strategies=5,
            execution_interval_seconds=60,
            enable_auto_allocation=True
        )
        
        await self.strategy_manager.initialize()
        logger.info("Gestionnaire de stratégies initialisé")
    
    async def demonstrate_template_loading(self):
        """Démontre le chargement et la validation des templates."""
        logger.info("\n=== Démonstration du chargement des templates ===")
        
        # Liste des templates disponibles
        template_files = list(self.templates_dir.glob("*.yaml"))
        logger.info(f"Templates disponibles : {[f.name for f in template_files]}")
        
        # Chargement et validation d'un template
        momentum_template = self.templates_dir / "basic_momentum_strategy.yaml"
        
        if momentum_template.exists():
            logger.info(f"Chargement du template : {momentum_template.name}")
            
            # Parsing du template
            parser = StrategyYAMLParser()
            strategy = await parser.parse_file(str(momentum_template))
            logger.info(f"Template parsé : {strategy.strategy.name}")
            
            # Validation du template
            validator = StrategyValidator()
            validation_result = await validator.validate_strategy(strategy)
            
            if validation_result.is_valid:
                logger.info("✅ Template valide !")
                logger.info(f"Score de validation : {validation_result.overall_score:.2f}")
            else:
                logger.warning("❌ Template invalide :")
                for error in validation_result.errors:
                    logger.warning(f"  - {error}")
            
            return strategy
        else:
            logger.error(f"Template non trouvé : {momentum_template}")
            return None
    
    async def demonstrate_strategy_customization(self, base_strategy):
        """Démontre la personnalisation d'une stratégie."""
        logger.info("\n=== Démonstration de la personnalisation ===")
        
        if not base_strategy:
            logger.error("Pas de stratégie de base pour la personnalisation")
            return None
        
        # Copie et modification de la stratégie
        custom_strategy = base_strategy.copy(deep=True)
        
        # Personnalisation
        custom_strategy.strategy.name = "Mon Momentum Personnalisé"
        custom_strategy.strategy.description = "Version personnalisée du momentum"
        
        # Modification des instruments (ETFs au lieu d'actions individuelles)
        custom_strategy.instruments = [
            {
                "symbol": "SPY",
                "name": "SPDR S&P 500 ETF",
                "sector": "ETF",
                "weight": 0.40
            },
            {
                "symbol": "QQQ",
                "name": "Invesco QQQ ETF",
                "sector": "ETF",
                "weight": 0.30
            },
            {
                "symbol": "VTI",
                "name": "Vanguard Total Stock Market ETF",
                "sector": "ETF",
                "weight": 0.30
            }
        ]
        
        # Ajustement de la gestion des risques (plus conservateur)
        custom_strategy.risk_management.stop_loss.value = 0.03  # 3% au lieu de 5%
        custom_strategy.risk_management.position_sizing.value = 0.03  # 3% par position
        
        # Sauvegarde de la stratégie personnalisée
        custom_file = self.strategies_dir / "my_custom_momentum.yaml"
        
        # Ici vous pourriez sauvegarder la stratégie modifiée
        logger.info(f"Stratégie personnalisée créée : {custom_strategy.strategy.name}")
        logger.info(f"Nouveaux instruments : {[i['symbol'] for i in custom_strategy.instruments]}")
        logger.info(f"Stop-loss ajusté : {custom_strategy.risk_management.stop_loss.value:.1%}")
        
        return custom_strategy
    
    async def demonstrate_strategy_execution(self, strategy):
        """Démontre l'exécution d'une stratégie."""
        logger.info("\n=== Démonstration de l'exécution ===")
        
        if not strategy:
            logger.error("Pas de stratégie pour l'exécution")
            return
        
        try:
            # Ajout de la stratégie au gestionnaire
            strategy_config = {
                "strategy": strategy.strategy.dict(),
                "instruments": strategy.instruments,
                "buy_conditions": strategy.buy_conditions.dict(),
                "sell_conditions": strategy.sell_conditions.dict(),
                "risk_management": strategy.risk_management.dict(),
                "execution": strategy.execution.dict() if strategy.execution else {},
                "data_requirements": strategy.data_requirements.dict() if strategy.data_requirements else {}
            }
            
            strategy_id = await self.strategy_manager.add_strategy_from_config(strategy_config)
            logger.info(f"Stratégie ajoutée avec ID : {strategy_id}")
            
            # Démarrage de la stratégie
            logger.info("Démarrage de la stratégie...")
            await self.strategy_manager.start_strategy(strategy_id)
            
            # Simulation d'exécution pendant quelques cycles
            logger.info("Simulation d'exécution (3 cycles)...")
            for i in range(3):
                logger.info(f"Cycle {i+1}/3")
                
                # Exécution manuelle d'un cycle
                signals = await self.strategy_manager.execute_strategy(strategy_id)
                logger.info(f"  Signaux générés : {len(signals)}")
                
                if signals:
                    for signal in signals:
                        logger.info(f"  Signal {signal.signal_type.value} pour {signal.symbol} "
                                  f"(confiance: {signal.confidence:.2%})")
                
                # Pause entre les cycles
                await asyncio.sleep(2)
            
            # Arrêt de la stratégie
            logger.info("Arrêt de la stratégie...")
            await self.strategy_manager.stop_strategy(strategy_id)
            
            # Informations finales
            strategy_info = await self.strategy_manager.get_strategy_info(strategy_id)
            logger.info(f"Exécutions totales : {strategy_info['execution_count']}")
            logger.info(f"Signaux actifs : {strategy_info['active_signals_count']}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution : {e}")
    
    async def demonstrate_portfolio_management(self):
        """Démontre la gestion de portefeuille."""
        logger.info("\n=== Démonstration de la gestion de portefeuille ===")
        
        # État simulé du portefeuille
        portfolio_state = {
            "total_value": 100000.0,
            "available_cash": 20000.0,
            "invested_value": 80000.0,
            "positions": {
                "SPY": 15000.0,
                "QQQ": 10000.0,
                "VTI": 8000.0,
                "AAPL": 12000.0,
                "GOOGL": 10000.0
            },
            "allocations": {
                "SPY": 0.15,
                "QQQ": 0.10,
                "VTI": 0.08,
                "AAPL": 0.12,
                "GOOGL": 0.10
            },
            "sector_exposures": {
                "Technology": 0.22,
                "ETF": 0.33,
                "Healthcare": 0.05
            },
            "strategy_allocations": {
                "momentum_strategy": 0.25,
                "mean_reversion_strategy": 0.15
            }
        }
        
        # Affichage de l'état du portefeuille
        logger.info(f"Valeur totale du portefeuille : ${portfolio_state['total_value']:,.2f}")
        logger.info(f"Cash disponible : ${portfolio_state['available_cash']:,.2f}")
        logger.info("Positions actuelles :")
        for symbol, value in portfolio_state['positions'].items():
            weight = portfolio_state['allocations'].get(symbol, 0)
            logger.info(f"  {symbol}: ${value:,.2f} ({weight:.1%})")
        
        # Test d'allocation avec l'allocateur
        allocator = self.strategy_manager.portfolio_allocator
        
        # Simulation d'un signal d'achat
        from finagent.business.strategy.engine.signal_generator import TradingSignal, SignalType
        
        test_signal = TradingSignal(
            signal_id="test_signal_001",
            strategy_id="test_strategy",
            symbol="MSFT",
            signal_type=SignalType.BUY,
            timestamp=datetime.now(),
            confidence=0.75,
            price_target=300.0,
            quantity=50.0
        )
        
        # Test d'allocation
        allocation_result = await allocator.allocate_signal(test_signal, portfolio_state)
        
        logger.info(f"Test d'allocation pour signal {test_signal.symbol} :")
        logger.info(f"  Statut : {allocation_result.status.value}")
        logger.info(f"  Montant alloué : ${allocation_result.allocated_amount:,.2f}")
        logger.info(f"  Pourcentage : {allocation_result.allocation_percentage:.2%}")
        
        if allocation_result.rejection_reason:
            logger.info(f"  Raison du rejet : {allocation_result.rejection_reason}")
    
    async def demonstrate_risk_management(self):
        """Démontre la gestion des risques."""
        logger.info("\n=== Démonstration de la gestion des risques ===")
        
        # État du portefeuille pour l'évaluation des risques
        portfolio_state = {
            "total_value": 100000.0,
            "positions": {
                "TSLA": 15000.0,  # Position concentrée
                "NVDA": 12000.0,
                "AMD": 8000.0
            },
            "sector_exposures": {
                "Technology": 0.35  # Forte exposition tech
            }
        }
        
        # Test du gestionnaire de risques
        risk_manager = self.strategy_manager.risk_manager
        
        # Simulation d'un signal risqué
        from finagent.business.strategy.engine.signal_generator import TradingSignal, SignalType
        
        risky_signal = TradingSignal(
            signal_id="risky_signal_001",
            strategy_id="test_strategy",
            symbol="TSLA",  # Ajout à une position déjà importante
            signal_type=SignalType.BUY,
            timestamp=datetime.now(),
            confidence=0.65,
            price_target=800.0,
            quantity=25.0  # Position importante
        )
        
        # Évaluation des risques
        risk_assessment = await risk_manager.assess_signal_risk(risky_signal, portfolio_state)
        
        logger.info(f"Évaluation des risques pour {risky_signal.symbol} :")
        logger.info(f"  Niveau de risque : {risk_assessment.overall_risk_level.value}")
        logger.info(f"  Acceptable : {'✅ Oui' if risk_assessment.is_acceptable else '❌ Non'}")
        logger.info(f"  Usage du budget de risque : {risk_assessment.risk_budget_usage:.1%}")
        
        if risk_assessment.rejection_reason:
            logger.info(f"  Raison du rejet : {risk_assessment.rejection_reason}")
        
        if risk_assessment.recommendations:
            logger.info("  Recommandations :")
            for rec in risk_assessment.recommendations:
                logger.info(f"    - {rec}")
        
        # Métriques de risque détaillées
        logger.info("  Métriques de risque :")
        for metric in risk_assessment.risk_metrics:
            status = "🔴 Dépassé" if metric.is_breached else "🟢 OK"
            logger.info(f"    {metric.metric_name}: {metric.current_value:.3f} "
                       f"(limite: {metric.limit_value:.3f}) {status}")
    
    async def demonstrate_monitoring_and_statistics(self):
        """Démontre le monitoring et les statistiques."""
        logger.info("\n=== Démonstration du monitoring ===")
        
        # Statut du gestionnaire
        manager_status = self.strategy_manager.get_manager_status()
        logger.info("Statut du gestionnaire :")
        logger.info(f"  Statut : {manager_status['status']}")
        logger.info(f"  Stratégies totales : {manager_status['strategies_count']}")
        logger.info(f"  Stratégies actives : {manager_status['active_strategies']}")
        
        # Métriques de performance
        performance_metrics = self.strategy_manager.get_performance_metrics()
        metrics = performance_metrics['metrics']
        
        logger.info("Métriques de performance :")
        logger.info(f"  Signaux générés : {metrics['total_signals_generated']}")
        logger.info(f"  Signaux exécutés : {metrics['signals_executed']}")
        logger.info(f"  Temps d'exécution moyen : {metrics['average_execution_time_ms']:.1f}ms")
        
        # Statistiques d'allocation
        allocation_stats = self.strategy_manager.portfolio_allocator.get_allocation_stats()
        logger.info("Statistiques d'allocation :")
        logger.info(f"  Allocations totales : {allocation_stats['total_allocations']}")
        logger.info(f"  Taux de succès : {allocation_stats['success_rate']:.1%}")
        logger.info(f"  Allocation moyenne : ${allocation_stats['average_allocation_size']:,.2f}")
        
        # Statistiques de risque
        risk_stats = self.strategy_manager.risk_manager.get_risk_stats()
        logger.info("Statistiques de risque :")
        logger.info(f"  Évaluations totales : {risk_stats['total_assessments']}")
        logger.info(f"  Signaux rejetés : {risk_stats['rejected_signals']}")
        logger.info(f"  Niveau de risque moyen : {risk_stats['average_risk_level']:.1f}")
    
    async def cleanup(self):
        """Nettoie les ressources."""
        if self.strategy_manager:
            await self.strategy_manager.shutdown()
            logger.info("Gestionnaire de stratégies arrêté")
    
    async def run_complete_demo(self):
        """Exécute la démonstration complète."""
        try:
            await self.initialize()
            
            # Chargement des templates
            strategy = await self.demonstrate_template_loading()
            
            # Personnalisation
            custom_strategy = await self.demonstrate_strategy_customization(strategy)
            
            # Exécution
            await self.demonstrate_strategy_execution(custom_strategy)
            
            # Gestion de portefeuille
            await self.demonstrate_portfolio_management()
            
            # Gestion des risques
            await self.demonstrate_risk_management()
            
            # Monitoring
            await self.demonstrate_monitoring_and_statistics()
            
            logger.info("\n=== Démonstration terminée avec succès ! ===")
            
        except Exception as e:
            logger.error(f"Erreur durant la démonstration : {e}")
            raise
        finally:
            await self.cleanup()


async def main():
    """Point d'entrée principal."""
    logger.info("🚀 Démarrage de la démonstration du système de stratégies FinAgent")
    
    runner = StrategyExampleRunner()
    await runner.run_complete_demo()


if __name__ == "__main__":
    # Configuration pour éviter les warnings asyncio sur Windows
    import platform
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Exécution de la démonstration
    asyncio.run(main())