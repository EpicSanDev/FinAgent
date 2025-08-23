"""
Tests d'Intégration - Workflows Complets FinAgent

Ces tests valident les workflows bout-en-bout complets du système FinAgent,
depuis l'analyse de marché jusqu'à l'exécution des décisions d'investissement.

Les workflows testés incluent :
- Analyse complète d'un symbole avec recommandations
- Génération de décisions d'investissement basées sur les stratégies
- Exécution et suivi des transactions
- Mise à jour et rééquilibrage du portefeuille
- Intégration entre tous les composants du système
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from finagent.ai.providers.claude_provider import ClaudeProvider
from finagent.data.providers.openbb_provider import OpenBBProvider
from finagent.business.strategy.engine.strategy_engine import StrategyEngine
from finagent.business.portfolio.portfolio_manager import PortfolioManager
from finagent.business.decision.decision_engine import DecisionEngine
from finagent.business.models.decision_models import InvestmentDecision, DecisionType
from finagent.business.models.portfolio_models import Portfolio, Position, Transaction

# Import des utilitaires de test
from tests.utils import (
    create_test_portfolio,
    create_test_strategy,
    benchmark_performance,
    MockOpenBBProvider,
    MockClaudeProvider
)


@pytest.mark.integration
@pytest.mark.slow
class TestWorkflowIntegration:
    """Tests d'intégration pour les workflows complets FinAgent"""
    
    @pytest.fixture
    async def integrated_system(self, test_config):
        """
        Fixture qui configure un système FinAgent complet pour les tests
        d'intégration avec composants réels et mocks selon la configuration
        """
        # Décider si utiliser vraies APIs ou mocks selon config
        use_real_apis = test_config.get("use_real_apis", False)
        
        if use_real_apis:
            # Providers réels (nécessite clés API valides)
            openbb_provider = OpenBBProvider(test_config["openbb"])
            claude_provider = ClaudeProvider(test_config["claude"])
        else:
            # Providers mockés pour tests sans APIs externes
            openbb_provider = MockOpenBBProvider(test_config["openbb"])
            claude_provider = MockClaudeProvider(test_config["claude"])
        
        # Composants système
        strategy_engine = StrategyEngine(test_config["strategy"])
        portfolio_manager = PortfolioManager(test_config["portfolio"])
        decision_engine = DecisionEngine(
            strategy_engine=strategy_engine,
            portfolio_manager=portfolio_manager,
            ai_provider=claude_provider,
            data_provider=openbb_provider
        )
        
        return {
            "openbb": openbb_provider,
            "claude": claude_provider,
            "strategy_engine": strategy_engine,
            "portfolio_manager": portfolio_manager,
            "decision_engine": decision_engine,
            "config": test_config
        }
    
    @pytest.fixture
    def sample_portfolio(self):
        """Portfolio de test avec positions diversifiées"""
        return create_test_portfolio(
            initial_capital=Decimal("100000.00"),
            positions=[
                ("AAPL", 50, Decimal("150.00")),
                ("GOOGL", 20, Decimal("2500.00")),
                ("MSFT", 30, Decimal("300.00")),
                ("TSLA", 10, Decimal("800.00"))
            ]
        )


@pytest.mark.integration
class TestCompleteAnalysisWorkflow:
    """Test du workflow complet d'analyse d'un symbole"""
    
    @pytest.mark.asyncio
    async def test_complete_symbol_analysis_workflow(self, integrated_system):
        """
        Test du workflow complet d'analyse d'un symbole :
        1. Récupération données de marché
        2. Analyse technique et fondamentale
        3. Génération d'insights IA
        4. Évaluation des stratégies
        5. Production de recommandations
        """
        system = integrated_system
        symbol = "AAPL"
        
        # 1. Récupération données de marché via OpenBB
        market_data = await system["openbb"].get_current_price(symbol)
        assert market_data is not None
        assert "price" in market_data
        assert market_data["price"] > 0
        
        # Récupération données historiques
        historical_data = await system["openbb"].get_historical_data(
            symbol, 
            period="1mo"
        )
        assert len(historical_data) > 0
        
        # Récupération indicateurs techniques
        technical_indicators = await system["openbb"].get_technical_indicators(
            symbol,
            indicators=["RSI", "MACD", "SMA_20", "SMA_50"]
        )
        assert "RSI" in technical_indicators
        assert "MACD" in technical_indicators
        
        # 2. Analyse IA via Claude
        analysis_prompt = f"""
        Analysez les données suivantes pour {symbol}:
        - Prix actuel: {market_data['price']}
        - RSI: {technical_indicators['RSI']}
        - MACD: {technical_indicators['MACD']}
        
        Fournissez une analyse technique et des recommandations.
        """
        
        ai_analysis = await system["claude"].generate_completion(analysis_prompt)
        assert ai_analysis is not None
        assert len(ai_analysis.content) > 100  # Analyse substantielle
        
        # 3. Évaluation par le moteur de stratégies
        strategy_config = create_test_strategy("momentum")
        strategy_evaluation = await system["strategy_engine"].evaluate_symbol(
            symbol=symbol,
            market_data=market_data,
            technical_indicators=technical_indicators,
            strategy_config=strategy_config
        )
        
        assert strategy_evaluation is not None
        assert "signals" in strategy_evaluation
        assert "confidence" in strategy_evaluation
        
        # 4. Validation de la cohérence des résultats
        assert isinstance(strategy_evaluation["confidence"], (int, float))
        assert 0 <= strategy_evaluation["confidence"] <= 1
        
        print(f"✅ Workflow d'analyse complet réussi pour {symbol}")
        print(f"   Prix: ${market_data['price']}")
        print(f"   Confiance stratégie: {strategy_evaluation['confidence']:.2%}")
        print(f"   Longueur analyse IA: {len(ai_analysis.content)} caractères")
    
    @pytest.mark.asyncio
    async def test_multi_symbol_analysis_workflow(self, integrated_system):
        """Test d'analyse simultanée de plusieurs symboles"""
        system = integrated_system
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        # Analyse en parallèle
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(
                self._analyze_single_symbol(system, symbol)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Validation des résultats
        successful_analyses = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_analyses) >= len(symbols) * 0.8  # 80% de succès minimum
        
        # Comparaison des résultats
        for i, result in enumerate(successful_analyses):
            symbol = symbols[i] if i < len(symbols) else "Unknown"
            assert result["symbol"] == symbol
            assert "confidence" in result
            assert "signals" in result
        
        print(f"✅ Analyses multiples réussies: {len(successful_analyses)}/{len(symbols)}")
    
    async def _analyze_single_symbol(self, system, symbol):
        """Helper pour analyser un symbole unique"""
        try:
            market_data = await system["openbb"].get_current_price(symbol)
            technical_data = await system["openbb"].get_technical_indicators(
                symbol, indicators=["RSI", "MACD"]
            )
            
            strategy_config = create_test_strategy("balanced")
            evaluation = await system["strategy_engine"].evaluate_symbol(
                symbol=symbol,
                market_data=market_data,
                technical_indicators=technical_data,
                strategy_config=strategy_config
            )
            
            return {
                "symbol": symbol,
                "confidence": evaluation["confidence"],
                "signals": evaluation["signals"]
            }
        except Exception as e:
            return e


@pytest.mark.integration
class TestDecisionExecutionWorkflow:
    """Test du workflow de génération et exécution des décisions"""
    
    @pytest.mark.asyncio
    async def test_decision_generation_workflow(self, integrated_system, sample_portfolio):
        """
        Test du workflow de génération de décisions :
        1. Analyse du portefeuille actuel
        2. Identification d'opportunités
        3. Génération de décisions d'investissement
        4. Validation des décisions
        """
        system = integrated_system
        portfolio = sample_portfolio
        
        # 1. Analyse du portefeuille actuel
        portfolio_analysis = await system["portfolio_manager"].analyze_portfolio(portfolio)
        assert portfolio_analysis is not None
        assert "total_value" in portfolio_analysis
        assert "allocation" in portfolio_analysis
        assert "risk_metrics" in portfolio_analysis
        
        # 2. Identification d'opportunités
        opportunities = await system["decision_engine"].identify_opportunities(
            portfolio=portfolio,
            market_conditions={"trend": "bullish", "volatility": "medium"}
        )
        assert len(opportunities) > 0
        
        # 3. Génération de décisions d'investissement
        decisions = []
        for opportunity in opportunities[:3]:  # Limiter pour les tests
            decision = await system["decision_engine"].generate_decision(
                opportunity=opportunity,
                portfolio=portfolio,
                risk_tolerance="moderate"
            )
            if decision:
                decisions.append(decision)
        
        assert len(decisions) > 0
        
        # 4. Validation des décisions
        for decision in decisions:
            assert isinstance(decision, InvestmentDecision)
            assert decision.symbol is not None
            assert decision.decision_type in [DecisionType.BUY, DecisionType.SELL, DecisionType.HOLD]
            assert decision.quantity > 0
            assert decision.confidence >= 0
            
            # Validation spécifique selon le type de décision
            if decision.decision_type == DecisionType.BUY:
                assert decision.target_price is not None
                assert decision.max_allocation > 0
            elif decision.decision_type == DecisionType.SELL:
                assert decision.stop_loss or decision.take_profit
        
        print(f"✅ Workflow de décision réussi: {len(decisions)} décisions générées")
        for i, decision in enumerate(decisions):
            print(f"   {i+1}. {decision.symbol}: {decision.decision_type.value} "
                  f"{decision.quantity} (confiance: {decision.confidence:.2%})")
    
    @pytest.mark.asyncio
    async def test_decision_execution_workflow(self, integrated_system, sample_portfolio):
        """
        Test du workflow d'exécution des décisions :
        1. Génération d'une décision d'achat
        2. Validation des fonds disponibles
        3. Exécution de la transaction
        4. Mise à jour du portefeuille
        5. Vérification de la cohérence
        """
        system = integrated_system
        portfolio = sample_portfolio
        
        # 1. Génération d'une décision d'achat
        buy_decision = InvestmentDecision(
            symbol="META",
            decision_type=DecisionType.BUY,
            quantity=20,
            target_price=Decimal("350.00"),
            confidence=Decimal("0.75"),
            reasoning="Test d'intégration - achat META",
            max_allocation=Decimal("0.10"),  # 10% max du portefeuille
            created_at=datetime.now()
        )
        
        # 2. Validation des fonds disponibles
        can_execute = await system["portfolio_manager"].can_execute_decision(
            decision=buy_decision,
            portfolio=portfolio
        )
        assert can_execute["feasible"] is True
        
        # 3. Exécution de la transaction
        transaction = await system["portfolio_manager"].execute_decision(
            decision=buy_decision,
            portfolio=portfolio
        )
        
        assert transaction is not None
        assert isinstance(transaction, Transaction)
        assert transaction.symbol == buy_decision.symbol
        assert transaction.quantity == buy_decision.quantity
        assert transaction.transaction_type == "BUY"
        
        # 4. Mise à jour du portefeuille
        updated_portfolio = await system["portfolio_manager"].update_portfolio_after_transaction(
            portfolio=portfolio,
            transaction=transaction
        )
        
        # 5. Vérification de la cohérence
        # Vérifier que la nouvelle position existe
        meta_position = next(
            (pos for pos in updated_portfolio.positions if pos.symbol == "META"), 
            None
        )
        assert meta_position is not None
        assert meta_position.quantity == buy_decision.quantity
        
        # Vérifier que le cash a diminué
        initial_cash = portfolio.available_cash
        updated_cash = updated_portfolio.available_cash
        expected_cost = buy_decision.quantity * buy_decision.target_price
        assert updated_cash == initial_cash - expected_cost
        
        print(f"✅ Workflow d'exécution réussi:")
        print(f"   Transaction: {transaction.transaction_type} {transaction.quantity} {transaction.symbol}")
        print(f"   Coût: ${expected_cost}")
        print(f"   Cash restant: ${updated_cash}")


@pytest.mark.integration
class TestPortfolioManagementWorkflow:
    """Test du workflow complet de gestion de portefeuille"""
    
    @pytest.mark.asyncio
    async def test_portfolio_rebalancing_workflow(self, integrated_system, sample_portfolio):
        """
        Test du workflow de rééquilibrage de portefeuille :
        1. Analyse de l'allocation actuelle
        2. Définition des allocations cibles
        3. Génération des ordres de rééquilibrage
        4. Exécution et validation
        """
        system = integrated_system
        portfolio = sample_portfolio
        
        # 1. Analyse de l'allocation actuelle
        current_allocation = await system["portfolio_manager"].get_current_allocation(portfolio)
        assert isinstance(current_allocation, dict)
        assert sum(current_allocation.values()) <= 1.01  # Tolérance pour arrondis
        
        # 2. Définition des allocations cibles
        target_allocation = {
            "AAPL": Decimal("0.30"),  # 30%
            "GOOGL": Decimal("0.25"), # 25%
            "MSFT": Decimal("0.25"),  # 25%
            "TSLA": Decimal("0.20")   # 20%
        }
        
        # 3. Génération des ordres de rééquilibrage
        rebalancing_orders = await system["portfolio_manager"].generate_rebalancing_orders(
            portfolio=portfolio,
            target_allocation=target_allocation
        )
        
        assert len(rebalancing_orders) > 0
        
        # 4. Validation des ordres
        total_buy_value = Decimal("0")
        total_sell_value = Decimal("0")
        
        for order in rebalancing_orders:
            if order.transaction_type == "BUY":
                total_buy_value += order.quantity * order.price
            elif order.transaction_type == "SELL":
                total_sell_value += order.quantity * order.price
        
        # Les achats et ventes doivent être équilibrés (à quelques frais près)
        value_difference = abs(total_buy_value - total_sell_value)
        assert value_difference <= portfolio.total_value * Decimal("0.02")  # 2% de tolérance
        
        # 5. Simulation d'exécution
        simulated_portfolio = portfolio.copy()
        for order in rebalancing_orders:
            transaction = Transaction(
                symbol=order.symbol,
                quantity=order.quantity,
                price=order.price,
                transaction_type=order.transaction_type,
                timestamp=datetime.now()
            )
            simulated_portfolio = await system["portfolio_manager"].update_portfolio_after_transaction(
                portfolio=simulated_portfolio,
                transaction=transaction
            )
        
        # Vérification de l'allocation finale
        final_allocation = await system["portfolio_manager"].get_current_allocation(simulated_portfolio)
        
        for symbol, target_pct in target_allocation.items():
            actual_pct = final_allocation.get(symbol, Decimal("0"))
            difference = abs(actual_pct - target_pct)
            assert difference <= Decimal("0.05")  # 5% de tolérance
        
        print(f"✅ Workflow de rééquilibrage réussi:")
        print(f"   Ordres générés: {len(rebalancing_orders)}")
        print(f"   Valeur achat: ${total_buy_value}")
        print(f"   Valeur vente: ${total_sell_value}")
        
        for symbol, target in target_allocation.items():
            actual = final_allocation.get(symbol, Decimal("0"))
            print(f"   {symbol}: {actual:.2%} (cible: {target:.2%})")
    
    @pytest.mark.asyncio
    async def test_risk_monitoring_workflow(self, integrated_system, sample_portfolio):
        """
        Test du workflow de surveillance des risques :
        1. Calcul des métriques de risque
        2. Détection des dépassements de limites
        3. Génération d'alertes
        4. Propositions d'actions correctives
        """
        system = integrated_system
        portfolio = sample_portfolio
        
        # 1. Calcul des métriques de risque
        risk_metrics = await system["portfolio_manager"].calculate_risk_metrics(portfolio)
        
        assert "var_95" in risk_metrics  # Value at Risk 95%
        assert "sharpe_ratio" in risk_metrics
        assert "max_drawdown" in risk_metrics
        assert "beta" in risk_metrics
        assert "concentration_risk" in risk_metrics
        
        # 2. Définition des limites de risque
        risk_limits = {
            "max_var_95": Decimal("0.05"),      # VaR max 5%
            "min_sharpe_ratio": Decimal("0.8"), # Sharpe min 0.8
            "max_concentration": Decimal("0.40"), # Concentration max 40%
            "max_beta": Decimal("1.5")          # Beta max 1.5
        }
        
        # 3. Détection des dépassements
        violations = await system["portfolio_manager"].check_risk_violations(
            risk_metrics=risk_metrics,
            risk_limits=risk_limits
        )
        
        # 4. Si violations détectées, générer actions correctives
        if violations:
            corrective_actions = await system["portfolio_manager"].generate_corrective_actions(
                portfolio=portfolio,
                violations=violations
            )
            
            assert len(corrective_actions) > 0
            
            for action in corrective_actions:
                assert "type" in action  # reduce_position, diversify, hedge
                if action["type"] == "reduce_position":
                    assert "symbol" in action
                assert "reasoning" in action
            
            print(f"⚠️  Violations de risque détectées: {len(violations)}")
            for violation in violations:
                print(f"   {violation['metric']}: {violation['value']} > {violation['limit']}")
            
            print(f"🔧 Actions correctives proposées: {len(corrective_actions)}")
            for action in corrective_actions:
                print(f"   {action['type']}: {action['reasoning']}")
        else:
            print("✅ Aucune violation de risque détectée")
        
        # Validation des métriques
        assert isinstance(risk_metrics["var_95"], (int, float, Decimal))
        assert risk_metrics["var_95"] >= 0
        
        if "sharpe_ratio" in risk_metrics and risk_metrics["sharpe_ratio"] is not None:
            assert isinstance(risk_metrics["sharpe_ratio"], (int, float, Decimal))


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndWorkflow:
    """Test du workflow complet bout-en-bout"""
    
    @pytest.mark.asyncio
    async def test_complete_investment_cycle(self, integrated_system):
        """
        Test d'un cycle d'investissement complet :
        1. Création d'un portefeuille vide
        2. Analyse du marché et identification d'opportunités
        3. Génération et exécution de premières positions
        4. Surveillance continue et ajustements
        5. Rééquilibrage périodique
        6. Évaluation de performance
        """
        system = integrated_system
        
        # 1. Création d'un portefeuille initial
        initial_capital = Decimal("50000.00")
        portfolio = Portfolio(
            id="integration-test-portfolio",
            name="Portfolio Test Intégration",
            initial_capital=initial_capital,
            available_cash=initial_capital,
            positions=[],
            created_at=datetime.now()
        )
        
        print(f"📊 Démarrage cycle d'investissement avec ${initial_capital}")
        
        # 2. Analyse du marché
        market_symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        opportunities = []
        
        for symbol in market_symbols:
            try:
                market_data = await system["openbb"].get_current_price(symbol)
                technical_data = await system["openbb"].get_technical_indicators(
                    symbol, indicators=["RSI", "MACD"]
                )
                
                # Évaluation par stratégie
                strategy_config = create_test_strategy("growth")
                evaluation = await system["strategy_engine"].evaluate_symbol(
                    symbol=symbol,
                    market_data=market_data,
                    technical_indicators=technical_data,
                    strategy_config=strategy_config
                )
                
                if evaluation["confidence"] > 0.6:  # Seuil de confiance
                    opportunities.append({
                        "symbol": symbol,
                        "confidence": evaluation["confidence"],
                        "price": market_data["price"],
                        "signals": evaluation["signals"]
                    })
            except Exception as e:
                print(f"⚠️  Erreur analyse {symbol}: {e}")
                continue
        
        print(f"🔍 Opportunités identifiées: {len(opportunities)}")
        
        # 3. Génération et exécution des premières positions
        executed_transactions = []
        
        # Trier par confiance décroissante
        opportunities.sort(key=lambda x: x["confidence"], reverse=True)
        
        for i, opp in enumerate(opportunities[:4]):  # Top 4 opportunités
            allocation_pct = Decimal("0.20")  # 20% par position
            position_value = portfolio.total_value * allocation_pct
            quantity = int(position_value / Decimal(str(opp["price"])))
            
            if quantity > 0:
                decision = InvestmentDecision(
                    symbol=opp["symbol"],
                    decision_type=DecisionType.BUY,
                    quantity=quantity,
                    target_price=Decimal(str(opp["price"])),
                    confidence=Decimal(str(opp["confidence"])),
                    reasoning=f"Opportunité #{i+1} avec confiance {opp['confidence']:.2%}",
                    max_allocation=allocation_pct,
                    created_at=datetime.now()
                )
                
                # Exécution
                can_execute = await system["portfolio_manager"].can_execute_decision(
                    decision=decision,
                    portfolio=portfolio
                )
                
                if can_execute["feasible"]:
                    transaction = await system["portfolio_manager"].execute_decision(
                        decision=decision,
                        portfolio=portfolio
                    )
                    
                    if transaction:
                        executed_transactions.append(transaction)
                        portfolio = await system["portfolio_manager"].update_portfolio_after_transaction(
                            portfolio=portfolio,
                            transaction=transaction
                        )
        
        print(f"💰 Transactions exécutées: {len(executed_transactions)}")
        for trans in executed_transactions:
            cost = trans.quantity * trans.price
            print(f"   {trans.symbol}: {trans.quantity} @ ${trans.price} = ${cost}")
        
        # 4. Évaluation initiale du portefeuille
        initial_analysis = await system["portfolio_manager"].analyze_portfolio(portfolio)
        print(f"📈 Analyse initiale:")
        print(f"   Valeur totale: ${initial_analysis['total_value']}")
        print(f"   Cash restant: ${portfolio.available_cash}")
        print(f"   Positions: {len(portfolio.positions)}")
        
        # 5. Simulation d'évolution temporelle et ajustements
        # (Ici on simulerait le passage du temps et les changements de prix)
        
        # Simulation de changements de prix (+/- 5% aléatoire)
        import random
        for position in portfolio.positions:
            price_change = random.uniform(-0.05, 0.05)  # ±5%
            new_price = position.average_price * (1 + Decimal(str(price_change)))
            position.current_price = new_price
        
        # 6. Réévaluation et rééquilibrage si nécessaire
        updated_analysis = await system["portfolio_manager"].analyze_portfolio(portfolio)
        
        # Vérifier si rééquilibrage nécessaire
        allocation = await system["portfolio_manager"].get_current_allocation(portfolio)
        needs_rebalancing = any(
            abs(alloc - Decimal("0.25")) > Decimal("0.10")  # Dérive de plus de 10%
            for alloc in allocation.values()
        )
        
        if needs_rebalancing:
            print("🔄 Rééquilibrage nécessaire détecté")
            target_allocation = {symbol: Decimal("0.25") for symbol in allocation.keys()}
            rebalancing_orders = await system["portfolio_manager"].generate_rebalancing_orders(
                portfolio=portfolio,
                target_allocation=target_allocation
            )
            print(f"   Ordres de rééquilibrage: {len(rebalancing_orders)}")
        
        # 7. Métriques de performance finales
        performance_metrics = {
            "initial_value": initial_capital,
            "final_value": updated_analysis["total_value"],
            "absolute_return": updated_analysis["total_value"] - initial_capital,
            "return_pct": ((updated_analysis["total_value"] / initial_capital) - 1) * 100,
            "positions_count": len(portfolio.positions),
            "cash_utilization": (1 - (portfolio.available_cash / initial_capital)) * 100
        }
        
        print(f"📊 Métriques finales:")
        print(f"   Rendement absolu: ${performance_metrics['absolute_return']}")
        print(f"   Rendement %: {performance_metrics['return_pct']:.2f}%")
        print(f"   Utilisation cash: {performance_metrics['cash_utilization']:.1f}%")
        
        # Assertions de validation
        assert len(executed_transactions) > 0
        assert len(portfolio.positions) > 0
        assert portfolio.available_cash >= 0
        assert updated_analysis["total_value"] > 0
        
        print("✅ Cycle d'investissement complet terminé avec succès")
        
        return {
            "portfolio": portfolio,
            "transactions": executed_transactions,
            "performance": performance_metrics,
            "analysis": updated_analysis
        }


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short"])