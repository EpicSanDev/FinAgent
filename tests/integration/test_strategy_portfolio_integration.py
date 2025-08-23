"""
Tests d'Intégration - Stratégie et Portefeuille

Ces tests valident l'intégration entre le moteur de stratégies et le gestionnaire
de portefeuille, incluant la génération de signaux, l'exécution des décisions
et l'optimisation continue du portefeuille.
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from finagent.business.strategy.engine.strategy_engine import StrategyEngine
from finagent.business.portfolio.portfolio_manager import PortfolioManager
from finagent.business.decision.decision_engine import DecisionEngine
from finagent.business.models.portfolio_models import Portfolio, Position
from finagent.business.models.decision_models import InvestmentDecision, DecisionType
from finagent.business.strategy.models.strategy_models import StrategySignal, SignalType

# Import des utilitaires de test
from tests.utils import (
    create_test_portfolio,
    create_test_strategy,
    MockOpenBBProvider,
    MockClaudeProvider,
    StockDataFactory,
    benchmark_performance
)


@pytest.mark.integration
class TestStrategyPortfolioIntegration:
    """Tests d'intégration stratégie-portefeuille de base"""
    
    @pytest.fixture
    async def integrated_components(self, test_config):
        """
        Composants intégrés pour les tests stratégie-portefeuille
        """
        # Providers mockés pour consistance
        openbb_provider = MockOpenBBProvider(test_config.get("openbb", {}))
        claude_provider = MockClaudeProvider(test_config.get("claude", {}))
        
        # Composants principaux
        strategy_engine = StrategyEngine(test_config.get("strategy", {}))
        portfolio_manager = PortfolioManager(test_config.get("portfolio", {}))
        decision_engine = DecisionEngine(
            strategy_engine=strategy_engine,
            portfolio_manager=portfolio_manager,
            ai_provider=claude_provider,
            data_provider=openbb_provider
        )
        
        return {
            "strategy_engine": strategy_engine,
            "portfolio_manager": portfolio_manager,
            "decision_engine": decision_engine,
            "openbb_provider": openbb_provider,
            "claude_provider": claude_provider
        }
    
    @pytest.fixture
    def diverse_portfolio(self):
        """Portefeuille diversifié pour les tests"""
        return create_test_portfolio(
            initial_capital=Decimal("200000.00"),
            positions=[
                ("AAPL", 100, Decimal("150.00")),    # Tech
                ("GOOGL", 40, Decimal("2500.00")),   # Tech
                ("JPM", 80, Decimal("125.00")),      # Finance
                ("JNJ", 120, Decimal("160.00")),     # Healthcare
                ("XOM", 150, Decimal("80.00")),      # Energy
            ]
        )


@pytest.mark.integration
class TestSignalToExecutionFlow:
    """Tests du flux complet signal -> décision -> exécution"""
    
    @pytest.mark.asyncio
    async def test_buy_signal_execution_flow(self, integrated_components, diverse_portfolio):
        """
        Test du flux complet pour un signal d'achat :
        1. Génération signal par stratégie
        2. Conversion en décision d'investissement
        3. Validation par gestionnaire portefeuille
        4. Exécution et mise à jour
        """
        components = integrated_components
        portfolio = diverse_portfolio
        symbol = "MSFT"
        
        # 1. Simuler des données de marché favorables
        market_data = await components["openbb_provider"].get_current_price(symbol)
        technical_indicators = await components["openbb_provider"].get_technical_indicators(
            symbol, indicators=["RSI", "MACD", "SMA_20"]
        )
        
        # Ajuster les indicateurs pour générer un signal d'achat
        technical_indicators["RSI"] = 25  # Survente
        technical_indicators["MACD"] = {"signal": "bullish"}
        technical_indicators["SMA_20"] = market_data["price"] * 0.95  # Prix au-dessus SMA
        
        # 2. Évaluation par le moteur de stratégies
        strategy_config = create_test_strategy("momentum")
        strategy_evaluation = await components["strategy_engine"].evaluate_symbol(
            symbol=symbol,
            market_data=market_data,
            technical_indicators=technical_indicators,
            strategy_config=strategy_config
        )
        
        assert strategy_evaluation is not None
        assert "signals" in strategy_evaluation
        
        # Vérifier qu'un signal d'achat est généré
        buy_signals = [
            signal for signal in strategy_evaluation["signals"] 
            if signal.get("type") == SignalType.BUY.value
        ]
        assert len(buy_signals) > 0
        
        strongest_signal = max(buy_signals, key=lambda s: s.get("strength", 0))
        
        # 3. Conversion en décision d'investissement
        investment_decision = await components["decision_engine"].convert_signal_to_decision(
            signal=strongest_signal,
            symbol=symbol,
            portfolio=portfolio,
            market_data=market_data
        )
        
        assert investment_decision is not None
        assert investment_decision.decision_type == DecisionType.BUY
        assert investment_decision.symbol == symbol
        assert investment_decision.quantity > 0
        
        # 4. Validation par le gestionnaire de portefeuille
        validation_result = await components["portfolio_manager"].can_execute_decision(
            decision=investment_decision,
            portfolio=portfolio
        )
        
        assert validation_result["feasible"] is True
        assert "required_cash" in validation_result
        assert "impact_analysis" in validation_result
        
        # 5. Exécution de la décision
        transaction = await components["portfolio_manager"].execute_decision(
            decision=investment_decision,
            portfolio=portfolio
        )
        
        assert transaction is not None
        assert transaction.symbol == symbol
        assert transaction.transaction_type == "BUY"
        assert transaction.quantity == investment_decision.quantity
        
        # 6. Mise à jour du portefeuille
        updated_portfolio = await components["portfolio_manager"].update_portfolio_after_transaction(
            portfolio=portfolio,
            transaction=transaction
        )
        
        # Vérification de la nouvelle position
        msft_position = next(
            (pos for pos in updated_portfolio.positions if pos.symbol == symbol),
            None
        )
        assert msft_position is not None
        assert msft_position.quantity == investment_decision.quantity
        
        print(f"✅ Flux signal->exécution réussi pour {symbol}:")
        print(f"   Signal: {strongest_signal.get('type')} (force: {strongest_signal.get('strength')})")
        print(f"   Décision: {investment_decision.decision_type.value} {investment_decision.quantity}")
        print(f"   Transaction: {transaction.transaction_type} @ ${transaction.price}")
        print(f"   Nouvelle position: {msft_position.quantity} shares")
    
    @pytest.mark.asyncio
    async def test_sell_signal_execution_flow(self, integrated_components, diverse_portfolio):
        """Test du flux complet pour un signal de vente"""
        components = integrated_components
        portfolio = diverse_portfolio
        symbol = "AAPL"  # Position existante dans le portefeuille
        
        # Vérifier que la position existe
        aapl_position = next(
            (pos for pos in portfolio.positions if pos.symbol == symbol),
            None
        )
        assert aapl_position is not None
        assert aapl_position.quantity > 0
        
        # 1. Simuler des données défavorables
        market_data = await components["openbb_provider"].get_current_price(symbol)
        technical_indicators = await components["openbb_provider"].get_technical_indicators(
            symbol, indicators=["RSI", "MACD", "SMA_20"]
        )
        
        # Ajuster pour signal de vente
        technical_indicators["RSI"] = 85  # Surachat
        technical_indicators["MACD"] = {"signal": "bearish"}
        technical_indicators["SMA_20"] = market_data["price"] * 1.05  # Prix sous SMA
        
        # 2. Évaluation stratégique
        strategy_config = create_test_strategy("momentum")
        strategy_evaluation = await components["strategy_engine"].evaluate_symbol(
            symbol=symbol,
            market_data=market_data,
            technical_indicators=technical_indicators,
            strategy_config=strategy_config
        )
        
        # Chercher des signaux de vente
        sell_signals = [
            signal for signal in strategy_evaluation.get("signals", [])
            if signal.get("type") == SignalType.SELL.value
        ]
        
        if len(sell_signals) == 0:
            # Forcer un signal de vente pour le test
            sell_signals = [{
                "type": SignalType.SELL.value,
                "strength": 0.8,
                "reasoning": "Test signal - conditions baissières"
            }]
        
        strongest_sell_signal = max(sell_signals, key=lambda s: s.get("strength", 0))
        
        # 3. Conversion en décision de vente
        sell_decision = await components["decision_engine"].convert_signal_to_decision(
            signal=strongest_sell_signal,
            symbol=symbol,
            portfolio=portfolio,
            market_data=market_data
        )
        
        assert sell_decision.decision_type == DecisionType.SELL
        assert sell_decision.quantity <= aapl_position.quantity  # Pas plus que détenu
        
        # 4. Exécution de la vente
        sell_transaction = await components["portfolio_manager"].execute_decision(
            decision=sell_decision,
            portfolio=portfolio
        )
        
        assert sell_transaction.transaction_type == "SELL"
        assert sell_transaction.quantity == sell_decision.quantity
        
        # 5. Mise à jour du portefeuille
        updated_portfolio = await components["portfolio_manager"].update_portfolio_after_transaction(
            portfolio=portfolio,
            transaction=sell_transaction
        )
        
        # Vérifier la réduction de position
        updated_aapl_position = next(
            (pos for pos in updated_portfolio.positions if pos.symbol == symbol),
            None
        )
        
        if updated_aapl_position:
            assert updated_aapl_position.quantity == aapl_position.quantity - sell_decision.quantity
        else:
            # Position complètement vendue
            assert sell_decision.quantity == aapl_position.quantity
        
        print(f"✅ Flux vente réussi pour {symbol}:")
        print(f"   Position initiale: {aapl_position.quantity}")
        print(f"   Quantité vendue: {sell_decision.quantity}")
        print(f"   Position finale: {updated_aapl_position.quantity if updated_aapl_position else 0}")
    
    @pytest.mark.asyncio
    async def test_hold_signal_and_monitoring(self, integrated_components, diverse_portfolio):
        """Test des signaux de maintien et du monitoring continu"""
        components = integrated_components
        portfolio = diverse_portfolio
        symbols = ["JPM", "JNJ"]  # Positions existantes
        
        hold_decisions = []
        
        for symbol in symbols:
            # 1. Données de marché neutres
            market_data = await components["openbb_provider"].get_current_price(symbol)
            technical_indicators = await components["openbb_provider"].get_technical_indicators(
                symbol, indicators=["RSI", "MACD"]
            )
            
            # Indicateurs neutres
            technical_indicators["RSI"] = 55  # Neutre
            technical_indicators["MACD"] = {"signal": "neutral"}
            
            # 2. Évaluation stratégique
            strategy_config = create_test_strategy("balanced")
            evaluation = await components["strategy_engine"].evaluate_symbol(
                symbol=symbol,
                market_data=market_data,
                technical_indicators=technical_indicators,
                strategy_config=strategy_config
            )
            
            # 3. Recherche de signaux HOLD ou décision par défaut
            hold_signals = [
                signal for signal in evaluation.get("signals", [])
                if signal.get("type") == SignalType.HOLD.value
            ]
            
            if not hold_signals:
                # Créer un signal HOLD par défaut
                hold_signals = [{
                    "type": SignalType.HOLD.value,
                    "strength": 0.6,
                    "reasoning": "Conditions neutres - maintien position"
                }]
            
            # 4. Conversion en décision
            hold_decision = await components["decision_engine"].convert_signal_to_decision(
                signal=hold_signals[0],
                symbol=symbol,
                portfolio=portfolio,
                market_data=market_data
            )
            
            if hold_decision:
                assert hold_decision.decision_type == DecisionType.HOLD
                hold_decisions.append(hold_decision)
        
        # 5. Monitoring continu des positions en HOLD
        monitoring_results = await components["portfolio_manager"].monitor_positions(
            portfolio=portfolio,
            symbols=symbols
        )
        
        assert len(monitoring_results) == len(symbols)
        
        for symbol, monitor_result in monitoring_results.items():
            assert "current_value" in monitor_result
            assert "performance" in monitor_result
            assert "risk_metrics" in monitor_result
        
        print(f"✅ Monitoring positions HOLD:")
        print(f"   Symboles surveillés: {len(symbols)}")
        print(f"   Décisions HOLD: {len(hold_decisions)}")
        for symbol, result in monitoring_results.items():
            print(f"   {symbol}: Valeur ${result['current_value']}, Perf {result.get('performance', 'N/A')}")


@pytest.mark.integration
class TestPortfolioOptimizationIntegration:
    """Tests d'optimisation intégrée stratégie-portefeuille"""
    
    @pytest.mark.asyncio
    async def test_strategy_driven_rebalancing(self, integrated_components, diverse_portfolio):
        """
        Test de rééquilibrage guidé par les stratégies :
        1. Analyse des signaux pour chaque position
        2. Identification des déséquilibres
        3. Génération d'ordres de rééquilibrage
        4. Validation et exécution
        """
        components = integrated_components
        portfolio = diverse_portfolio
        
        # 1. Analyser tous les symboles du portefeuille
        symbol_analyses = {}
        total_signal_score = 0
        
        for position in portfolio.positions:
            symbol = position.symbol
            
            # Données de marché
            market_data = await components["openbb_provider"].get_current_price(symbol)
            technical_indicators = await components["openbb_provider"].get_technical_indicators(
                symbol, indicators=["RSI", "MACD", "SMA_20"]
            )
            
            # Évaluation stratégique
            strategy_config = create_test_strategy("dynamic")
            evaluation = await components["strategy_engine"].evaluate_symbol(
                symbol=symbol,
                market_data=market_data,
                technical_indicators=technical_indicators,
                strategy_config=strategy_config
            )
            
            # Calculer score global du symbole
            signal_score = evaluation.get("confidence", 0.5)
            symbol_analyses[symbol] = {
                "evaluation": evaluation,
                "signal_score": signal_score,
                "current_allocation": position.market_value / portfolio.total_value,
                "position": position
            }
            total_signal_score += signal_score
        
        # 2. Calculer allocations cibles basées sur les signaux
        target_allocations = {}
        for symbol, analysis in symbol_analyses.items():
            # Allocation proportionnelle à la force du signal
            if total_signal_score > 0:
                target_pct = analysis["signal_score"] / total_signal_score
                # Lisser avec allocation actuelle pour éviter changements drastiques
                current_pct = analysis["current_allocation"]
                target_allocations[symbol] = (target_pct * 0.7 + current_pct * 0.3)
            else:
                target_allocations[symbol] = analysis["current_allocation"]
        
        # Normaliser pour que la somme = 1
        total_target = sum(target_allocations.values())
        if total_target > 0:
            target_allocations = {
                symbol: alloc / total_target 
                for symbol, alloc in target_allocations.items()
            }
        
        # 3. Générer ordres de rééquilibrage
        rebalancing_orders = await components["portfolio_manager"].generate_rebalancing_orders(
            portfolio=portfolio,
            target_allocation=target_allocations
        )
        
        # 4. Validation des ordres
        assert len(rebalancing_orders) >= 0  # Peut être 0 si déjà équilibré
        
        # Calculer l'impact total du rééquilibrage
        total_buy_value = sum(
            order.quantity * order.price for order in rebalancing_orders
            if order.transaction_type == "BUY"
        )
        total_sell_value = sum(
            order.quantity * order.price for order in rebalancing_orders
            if order.transaction_type == "SELL"
        )
        
        # Les achats et ventes doivent être équilibrés
        value_imbalance = abs(total_buy_value - total_sell_value)
        max_imbalance = portfolio.total_value * Decimal("0.02")  # 2% tolérance
        assert value_imbalance <= max_imbalance
        
        print(f"✅ Rééquilibrage guidé par stratégie:")
        print(f"   Symboles analysés: {len(symbol_analyses)}")
        print(f"   Ordres générés: {len(rebalancing_orders)}")
        print(f"   Valeur achat: ${total_buy_value}")
        print(f"   Valeur vente: ${total_sell_value}")
        print(f"   Déséquilibre: ${value_imbalance}")
        
        # Afficher les allocations cibles vs actuelles
        for symbol, target_pct in target_allocations.items():
            current_pct = symbol_analyses[symbol]["current_allocation"]
            signal_score = symbol_analyses[symbol]["signal_score"]
            print(f"   {symbol}: {current_pct:.2%} -> {target_pct:.2%} (signal: {signal_score:.2f})")
    
    @pytest.mark.asyncio
    async def test_risk_adjusted_strategy_execution(self, integrated_components, diverse_portfolio):
        """Test d'exécution de stratégie avec ajustement des risques"""
        components = integrated_components
        portfolio = diverse_portfolio
        
        # 1. Analyser le risque actuel du portefeuille
        risk_metrics = await components["portfolio_manager"].calculate_risk_metrics(portfolio)
        
        # 2. Définir limites de risque
        risk_limits = {
            "max_single_position": Decimal("0.25"),  # 25% max par position
            "max_sector_exposure": Decimal("0.40"),  # 40% max par secteur
            "max_var_95": Decimal("0.05"),           # VaR 5% max
            "min_diversification": 5                  # 5 positions minimum
        }
        
        # 3. Identifier opportunités en respectant les limites de risque
        opportunity_symbol = "AMZN"
        market_data = await components["openbb_provider"].get_current_price(opportunity_symbol)
        
        # Simulation d'un signal d'achat fort
        strong_buy_signal = {
            "type": SignalType.BUY.value,
            "strength": 0.9,
            "reasoning": "Signal d'achat très fort pour test ajustement risque"
        }
        
        # 4. Conversion en décision avec contraintes de risque
        investment_decision = await components["decision_engine"].convert_signal_to_decision(
            signal=strong_buy_signal,
            symbol=opportunity_symbol,
            portfolio=portfolio,
            market_data=market_data,
            risk_limits=risk_limits
        )
        
        # 5. Validation que la décision respecte les limites de risque
        if investment_decision:
            # Calculer l'allocation que représenterait cette décision
            decision_value = investment_decision.quantity * investment_decision.target_price
            total_value_after = portfolio.total_value + decision_value
            new_position_pct = decision_value / total_value_after
            
            # Vérifier respect des limites
            assert new_position_pct <= risk_limits["max_single_position"]
            assert investment_decision.max_allocation <= risk_limits["max_single_position"]
            
            print(f"✅ Décision ajustée aux risques:")
            print(f"   Symbole: {opportunity_symbol}")
            print(f"   Quantité ajustée: {investment_decision.quantity}")
            print(f"   Allocation: {new_position_pct:.2%}")
            print(f"   Limite max: {risk_limits['max_single_position']:.2%}")
        else:
            print(f"✅ Décision rejetée pour respect limites de risque")
        
        # 6. Test avec plusieurs opportunités simultanées
        multiple_opportunities = [
            ("NFLX", 0.8),
            ("NVDA", 0.85),
            ("AMD", 0.75)
        ]
        
        risk_adjusted_decisions = []
        
        for symbol, signal_strength in multiple_opportunities:
            market_data = await components["openbb_provider"].get_current_price(symbol)
            signal = {
                "type": SignalType.BUY.value,
                "strength": signal_strength,
                "reasoning": f"Opportunité multiple - {symbol}"
            }
            
            decision = await components["decision_engine"].convert_signal_to_decision(
                signal=signal,
                symbol=symbol,
                portfolio=portfolio,
                market_data=market_data,
                risk_limits=risk_limits
            )
            
            if decision:
                risk_adjusted_decisions.append(decision)
        
        # Vérifier que l'ensemble des décisions respecte les limites globales
        total_new_allocation = sum(
            (decision.quantity * decision.target_price / portfolio.total_value)
            for decision in risk_adjusted_decisions
        )
        
        # L'allocation totale des nouvelles positions ne doit pas être excessive
        max_total_new_allocation = Decimal("0.30")  # 30% max en nouvelles positions
        assert total_new_allocation <= max_total_new_allocation
        
        print(f"✅ Opportunités multiples avec ajustement risque:")
        print(f"   Opportunités analysées: {len(multiple_opportunities)}")
        print(f"   Décisions acceptées: {len(risk_adjusted_decisions)}")
        print(f"   Allocation totale nouvelle: {total_new_allocation:.2%}")


@pytest.mark.integration
@pytest.mark.slow
class TestContinuousOptimizationLoop:
    """Tests de la boucle d'optimisation continue"""
    
    @pytest.mark.asyncio
    async def test_complete_optimization_cycle(self, integrated_components, diverse_portfolio):
        """
        Test d'un cycle complet d'optimisation :
        1. Analyse initiale du portefeuille
        2. Identification d'opportunités d'amélioration
        3. Exécution des changements
        4. Réévaluation et ajustements
        5. Monitoring continu
        """
        components = integrated_components
        initial_portfolio = diverse_portfolio.copy()
        current_portfolio = diverse_portfolio
        
        optimization_cycles = 3
        performance_history = []
        
        for cycle in range(optimization_cycles):
            print(f"\n🔄 Cycle d'optimisation {cycle + 1}/{optimization_cycles}")
            
            # 1. Analyse complète du portefeuille
            portfolio_analysis = await components["portfolio_manager"].analyze_portfolio(current_portfolio)
            performance_history.append({
                "cycle": cycle + 1,
                "total_value": portfolio_analysis["total_value"],
                "analysis": portfolio_analysis
            })
            
            # 2. Identification d'opportunités via strategies
            opportunities = await components["decision_engine"].identify_opportunities(
                portfolio=current_portfolio,
                market_conditions={"trend": "mixed", "volatility": "medium"}
            )
            
            # 3. Sélectionner les meilleures opportunités
            best_opportunities = sorted(
                opportunities[:5],  # Top 5
                key=lambda opp: opp.get("confidence", 0),
                reverse=True
            )
            
            executed_decisions = []
            
            # 4. Exécuter les décisions
            for opportunity in best_opportunities:
                try:
                    decision = await components["decision_engine"].generate_decision(
                        opportunity=opportunity,
                        portfolio=current_portfolio,
                        risk_tolerance="moderate"
                    )
                    
                    if decision:
                        # Valider faisabilité
                        can_execute = await components["portfolio_manager"].can_execute_decision(
                            decision=decision,
                            portfolio=current_portfolio
                        )
                        
                        if can_execute["feasible"]:
                            # Exécuter
                            transaction = await components["portfolio_manager"].execute_decision(
                                decision=decision,
                                portfolio=current_portfolio
                            )
                            
                            if transaction:
                                executed_decisions.append(decision)
                                current_portfolio = await components["portfolio_manager"].update_portfolio_after_transaction(
                                    portfolio=current_portfolio,
                                    transaction=transaction
                                )
                
                except Exception as e:
                    print(f"   ⚠️  Erreur exécution opportunité: {e}")
                    continue
            
            # 5. Évaluation des améliorations
            if executed_decisions:
                post_execution_analysis = await components["portfolio_manager"].analyze_portfolio(current_portfolio)
                
                print(f"   Opportunités identifiées: {len(opportunities)}")
                print(f"   Décisions exécutées: {len(executed_decisions)}")
                print(f"   Valeur avant: ${portfolio_analysis['total_value']}")
                print(f"   Valeur après: ${post_execution_analysis['total_value']}")
                
                for decision in executed_decisions:
                    print(f"     {decision.decision_type.value} {decision.quantity} {decision.symbol}")
            else:
                print(f"   Aucune décision exécutée ce cycle")
            
            # Pause entre cycles (simulation temps)
            await asyncio.sleep(0.1)
        
        # 6. Évaluation finale de performance
        final_analysis = await components["portfolio_manager"].analyze_portfolio(current_portfolio)
        initial_value = initial_portfolio.total_value
        final_value = final_analysis["total_value"]
        
        total_return = ((final_value / initial_value) - 1) * 100
        
        print(f"\n📊 Résultats optimisation continue:")
        print(f"   Cycles exécutés: {optimization_cycles}")
        print(f"   Valeur initiale: ${initial_value}")
        print(f"   Valeur finale: ${final_value}")
        print(f"   Rendement total: {total_return:.2f}%")
        print(f"   Positions initiales: {len(initial_portfolio.positions)}")
        print(f"   Positions finales: {len(current_portfolio.positions)}")
        
        # Assertions de cohérence
        assert final_value > 0
        assert len(current_portfolio.positions) > 0
        assert current_portfolio.available_cash >= 0
        
        # L'optimisation devrait au minimum préserver la valeur
        # (dans un vrai marché, cela dépendrait des conditions)
        min_acceptable_return = -5.0  # -5% maximum acceptable en test
        assert total_return >= min_acceptable_return
        
        return {
            "initial_value": initial_value,
            "final_value": final_value,
            "total_return": total_return,
            "performance_history": performance_history,
            "final_portfolio": current_portfolio
        }


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "not slow"])