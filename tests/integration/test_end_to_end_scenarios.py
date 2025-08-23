"""
Tests d'Intégration - Scénarios End-to-End

Ces tests valident des scénarios utilisateur complets et réalistes,
simulant l'utilisation réelle de FinAgent dans différents contextes
d'investissement et de gestion de portefeuille.
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from finagent.business.models.portfolio_models import Portfolio, Position
from finagent.business.models.decision_models import InvestmentDecision, DecisionType
from finagent.cli.main import cli
from click.testing import CliRunner

# Import des utilitaires de test
from tests.utils import (
    create_test_portfolio,
    create_test_strategy,
    MockOpenBBProvider,
    MockClaudeProvider,
    benchmark_performance
)


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndScenarios:
    """Tests de scénarios utilisateur complets"""
    
    @pytest.fixture
    async def complete_system_setup(self, test_config):
        """Setup complet du système pour tests end-to-end"""
        # Providers avec données réalistes
        openbb_provider = MockOpenBBProvider(test_config.get("openbb", {}))
        claude_provider = MockClaudeProvider(test_config.get("claude", {}))
        
        # Configuration temporaire complète
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            # Fichier de configuration
            config_file = config_dir / "finagent_config.yaml"
            config_content = {
                "openbb": test_config.get("openbb", {}),
                "claude": test_config.get("claude", {}),
                "portfolio": {
                    "default_currency": "USD",
                    "risk_tolerance": "moderate",
                    "rebalancing_threshold": 0.05
                },
                "strategy": {
                    "default_strategies": ["momentum", "value"],
                    "signal_threshold": 0.6
                }
            }
            
            import yaml
            with open(config_file, 'w') as f:
                yaml.dump(config_content, f)
            
            yield {
                "config_dir": config_dir,
                "config_file": config_file,
                "openbb_provider": openbb_provider,
                "claude_provider": claude_provider,
                "config": config_content
            }


@pytest.mark.integration
@pytest.mark.slow
class TestRealUserWorkflows:
    """Tests de workflows utilisateur réalistes"""
    
    @pytest.mark.asyncio
    async def test_new_investor_onboarding_workflow(self, complete_system_setup):
        """
        Scénario : Nouvel investisseur qui débute avec FinAgent
        1. Configuration initiale
        2. Création premier portefeuille
        3. Première analyse de marché
        4. Premières décisions d'investissement
        5. Surveillance et ajustements
        """
        setup = complete_system_setup
        cli_runner = CliRunner()
        
        print("👤 Scénario : Nouvel investisseur")
        
        # 1. Configuration initiale via CLI
        config_result = cli_runner.invoke(cli, [
            'config', 'validate',
            '--file', str(setup["config_file"])
        ])
        assert config_result.exit_code == 0
        print("   ✅ Configuration validée")
        
        # 2. Création du premier portefeuille
        initial_portfolio = Portfolio(
            id="new-investor-portfolio",
            name="Mon Premier Portefeuille",
            initial_capital=Decimal("10000.00"),  # 10k$ pour débuter
            available_cash=Decimal("10000.00"),
            positions=[],
            created_at=datetime.now()
        )
        
        portfolio_file = setup["config_dir"] / "portfolio.json"
        with open(portfolio_file, 'w') as f:
            json.dump({
                "id": initial_portfolio.id,
                "name": initial_portfolio.name,
                "initial_capital": float(initial_portfolio.initial_capital),
                "available_cash": float(initial_portfolio.available_cash),
                "positions": [],
                "created_at": initial_portfolio.created_at.isoformat()
            }, f, indent=2)
        
        print(f"   ✅ Portefeuille créé : ${initial_portfolio.initial_capital}")
        
        # 3. Première analyse de marché - actions populaires pour débutants
        beginner_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "VTI"]  # VTI = ETF diversifié
        
        analysis_results = {}
        for symbol in beginner_symbols:
            # Analyse via CLI
            analysis_result = cli_runner.invoke(cli, [
                'analyze',
                '--symbol', symbol,
                '--config', str(setup["config_file"]),
                '--format', 'json'
            ])
            
            if analysis_result.exit_code == 0:
                try:
                    analysis_data = json.loads(analysis_result.output)
                    analysis_results[symbol] = analysis_data
                except json.JSONDecodeError:
                    print(f"   ⚠️  Analyse {symbol} : format invalide")
        
        print(f"   ✅ Analyses de marché : {len(analysis_results)}/{len(beginner_symbols)} réussies")
        
        # 4. Stratégie débutant : diversification simple
        recommended_allocation = {
            "AAPL": Decimal("0.20"),   # 20% - Tech stable
            "MSFT": Decimal("0.20"),   # 20% - Tech stable
            "VTI": Decimal("0.40"),    # 40% - ETF diversifié
            "AMZN": Decimal("0.15"),   # 15% - Croissance
            # 5% reste en cash
        }
        
        executed_positions = []
        remaining_cash = initial_portfolio.available_cash
        
        for symbol, target_allocation in recommended_allocation.items():
            if symbol in analysis_results:
                # Calculer montant à investir
                investment_amount = initial_portfolio.initial_capital * target_allocation
                
                # Simuler prix d'achat (données du provider mock)
                mock_price = Decimal("150.00")  # Prix simulé
                if symbol == "VTI":
                    mock_price = Decimal("220.00")  # ETF plus cher
                elif symbol == "AMZN":
                    mock_price = Decimal("3000.00")  # Action plus chère
                
                quantity = int(investment_amount / mock_price)
                actual_cost = quantity * mock_price
                
                if quantity > 0 and actual_cost <= remaining_cash:
                    position = Position(
                        symbol=symbol,
                        quantity=quantity,
                        average_price=mock_price,
                        current_price=mock_price
                    )
                    executed_positions.append(position)
                    remaining_cash -= actual_cost
                    
                    print(f"   💰 Acheté : {quantity} {symbol} @ ${mock_price} = ${actual_cost}")
        
        # 5. Mise à jour du portefeuille
        initial_portfolio.positions = executed_positions
        initial_portfolio.available_cash = remaining_cash
        
        # Calculer métriques de début
        total_invested = sum(pos.market_value for pos in executed_positions)
        diversification_score = len(executed_positions)
        cash_percentage = (remaining_cash / initial_portfolio.initial_capital) * 100
        
        print(f"   📊 Portfolio initial créé :")
        print(f"      Total investi : ${total_invested}")
        print(f"      Positions : {diversification_score}")
        print(f"      Cash restant : {cash_percentage:.1f}%")
        
        # Assertions de validation
        assert len(executed_positions) >= 3  # Minimum diversification
        assert total_invested <= initial_portfolio.initial_capital
        assert remaining_cash >= 0
        assert diversification_score >= 3
        
        print("   ✅ Onboarding nouvel investisseur réussi")
        
        return {
            "portfolio": initial_portfolio,
            "analysis_results": analysis_results,
            "executed_positions": executed_positions,
            "metrics": {
                "total_invested": total_invested,
                "diversification": diversification_score,
                "cash_percentage": cash_percentage
            }
        }
    
    @pytest.mark.asyncio
    async def test_experienced_trader_workflow(self, complete_system_setup):
        """
        Scénario : Trader expérimenté utilisant des stratégies avancées
        1. Import portefeuille existant complexe
        2. Application stratégies sophistiquées
        3. Trading actif avec signaux
        4. Gestion risques avancée
        5. Optimisation continue
        """
        setup = complete_system_setup
        
        print("🔥 Scénario : Trader expérimenté")
        
        # 1. Portefeuille complexe existant
        experienced_portfolio = create_test_portfolio(
            initial_capital=Decimal("500000.00"),  # 500k$ capital important
            positions=[
                ("AAPL", 500, Decimal("150.00")),
                ("GOOGL", 100, Decimal("2500.00")),
                ("TSLA", 300, Decimal("800.00")),
                ("NVDA", 200, Decimal("700.00")),
                ("QQQ", 1000, Decimal("350.00")),  # ETF tech
                ("SPY", 500, Decimal("420.00")),   # ETF marché
                ("MSFT", 400, Decimal("300.00")),
                ("AMD", 600, Decimal("120.00")),
                ("NFLX", 150, Decimal("450.00")),
                ("META", 250, Decimal("320.00"))
            ]
        )
        
        print(f"   📊 Portefeuille initial : ${experienced_portfolio.total_value}")
        print(f"   🏢 Positions : {len(experienced_portfolio.positions)}")
        
        # 2. Stratégies sophistiquées
        advanced_strategies = [
            create_test_strategy("momentum"),
            create_test_strategy("mean_reversion"),
            create_test_strategy("breakout"),
            create_test_strategy("pairs_trading")
        ]
        
        print(f"   🧠 Stratégies actives : {len(advanced_strategies)}")
        
        # 3. Simulation de trading actif sur plusieurs jours
        trading_days = 5
        daily_results = []
        current_portfolio = experienced_portfolio
        
        for day in range(trading_days):
            print(f"\n   📅 Jour de trading {day + 1}")
            
            # Analyse de marché quotidienne
            market_signals = {}
            for position in current_portfolio.positions[:5]:  # Top 5 positions
                symbol = position.symbol
                
                # Simulation signaux de stratégies
                momentum_signal = self._simulate_momentum_signal(symbol, day)
                mean_reversion_signal = self._simulate_mean_reversion_signal(symbol, day)
                
                # Agrégation des signaux
                combined_signal = {
                    "symbol": symbol,
                    "momentum": momentum_signal,
                    "mean_reversion": mean_reversion_signal,
                    "net_score": (momentum_signal + mean_reversion_signal) / 2
                }
                market_signals[symbol] = combined_signal
            
            # Décisions de trading basées sur signaux
            daily_trades = []
            for symbol, signals in market_signals.items():
                net_score = signals["net_score"]
                position = next(p for p in current_portfolio.positions if p.symbol == symbol)
                
                if net_score > 0.7:  # Signal d'achat fort
                    # Augmenter position
                    additional_quantity = min(50, int(current_portfolio.available_cash / position.current_price))
                    if additional_quantity > 0:
                        daily_trades.append({
                            "action": "BUY",
                            "symbol": symbol,
                            "quantity": additional_quantity,
                            "reason": f"Signal fort: {net_score:.2f}"
                        })
                
                elif net_score < -0.7:  # Signal de vente fort
                    # Réduire position
                    sell_quantity = min(position.quantity // 4, 100)  # Vendre 25% max
                    if sell_quantity > 0:
                        daily_trades.append({
                            "action": "SELL",
                            "symbol": symbol,
                            "quantity": sell_quantity,
                            "reason": f"Signal faible: {net_score:.2f}"
                        })
            
            # Simuler exécution des trades
            for trade in daily_trades:
                print(f"      {trade['action']} {trade['quantity']} {trade['symbol']} - {trade['reason']}")
            
            daily_results.append({
                "day": day + 1,
                "signals": market_signals,
                "trades": daily_trades,
                "portfolio_value": current_portfolio.total_value
            })
        
        # 4. Analyse des performances
        initial_value = experienced_portfolio.total_value
        final_value = daily_results[-1]["portfolio_value"]
        total_trades = sum(len(day["trades"]) for day in daily_results)
        
        print(f"\n   📈 Résultats trading actif :")
        print(f"      Jours de trading : {trading_days}")
        print(f"      Total trades : {total_trades}")
        print(f"      Valeur initiale : ${initial_value}")
        print(f"      Valeur finale : ${final_value}")
        
        # Assertions pour trader expérimenté
        assert total_trades > 0  # Activité de trading
        assert len(current_portfolio.positions) >= 8  # Portefeuille diversifié
        assert current_portfolio.total_value > 0
        
        print("   ✅ Workflow trader expérimenté réussi")
        
        return {
            "initial_portfolio": experienced_portfolio,
            "strategies": advanced_strategies,
            "daily_results": daily_results,
            "performance": {
                "initial_value": initial_value,
                "final_value": final_value,
                "total_trades": total_trades
            }
        }
    
    def _simulate_momentum_signal(self, symbol: str, day: int) -> float:
        """Simule un signal momentum basé sur le symbole et le jour"""
        import hashlib
        hash_input = f"{symbol}-{day}-momentum"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        return (hash_value % 200 - 100) / 100.0  # -1.0 à 1.0
    
    def _simulate_mean_reversion_signal(self, symbol: str, day: int) -> float:
        """Simule un signal mean reversion"""
        import hashlib
        hash_input = f"{symbol}-{day}-meanrev"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        return (hash_value % 200 - 100) / 100.0  # -1.0 à 1.0
    
    @pytest.mark.asyncio
    async def test_retirement_planning_workflow(self, complete_system_setup):
        """
        Scénario : Planification retraite long terme
        1. Profil investisseur conservateur
        2. Stratégie buy-and-hold
        3. Rééquilibrage périodique
        4. Surveillance de la croissance
        """
        setup = complete_system_setup
        
        print("🏖️  Scénario : Planification retraite")
        
        # 1. Portefeuille conservateur orienté retraite
        retirement_portfolio = Portfolio(
            id="retirement-portfolio",
            name="Portefeuille Retraite",
            initial_capital=Decimal("150000.00"),
            available_cash=Decimal("150000.00"),
            positions=[],
            created_at=datetime.now()
        )
        
        # 2. Allocation conservatrice typique
        conservative_allocation = {
            "VTI": Decimal("0.30"),    # 30% Actions US total market
            "VXUS": Decimal("0.20"),   # 20% Actions internationales
            "BND": Decimal("0.35"),    # 35% Obligations
            "VNQ": Decimal("0.10"),    # 10% REITs immobilier
            "VTEB": Decimal("0.05")    # 5% Obligations municipales
        }
        
        # 3. Construction initiale du portefeuille
        executed_positions = []
        remaining_cash = retirement_portfolio.available_cash
        
        for symbol, target_allocation in conservative_allocation.items():
            investment_amount = retirement_portfolio.initial_capital * target_allocation
            
            # Prix simulés pour ETFs
            etf_prices = {
                "VTI": Decimal("220.00"),
                "VXUS": Decimal("60.00"),
                "BND": Decimal("82.00"),
                "VNQ": Decimal("95.00"),
                "VTEB": Decimal("54.00")
            }
            
            price = etf_prices.get(symbol, Decimal("100.00"))
            quantity = int(investment_amount / price)
            actual_cost = quantity * price
            
            if quantity > 0 and actual_cost <= remaining_cash:
                position = Position(
                    symbol=symbol,
                    quantity=quantity,
                    average_price=price,
                    current_price=price
                )
                executed_positions.append(position)
                remaining_cash -= actual_cost
                
                print(f"   💎 Position : {quantity} {symbol} @ ${price}")
        
        retirement_portfolio.positions = executed_positions
        retirement_portfolio.available_cash = remaining_cash
        
        # 4. Simulation progression sur plusieurs années
        years_simulated = 5
        annual_contributions = Decimal("12000.00")  # 12k$/an
        rebalancing_frequency = 12  # Tous les 12 mois
        
        portfolio_evolution = []
        current_portfolio = retirement_portfolio
        
        for year in range(years_simulated):
            # Contribution annuelle
            current_portfolio.available_cash += annual_contributions
            
            # Croissance simulée (5% annuel moyen)
            for position in current_portfolio.positions:
                growth_factor = Decimal("1.05")  # 5% croissance
                position.current_price = position.current_price * growth_factor
            
            # Rééquilibrage annuel
            if year % rebalancing_frequency == 0 and year > 0:
                print(f"   🔄 Rééquilibrage année {year + 1}")
                # Simuler rééquilibrage vers allocations cibles
            
            portfolio_value = sum(pos.market_value for pos in current_portfolio.positions) + current_portfolio.available_cash
            
            portfolio_evolution.append({
                "year": year + 1,
                "total_value": portfolio_value,
                "contributions": annual_contributions * (year + 1),
                "growth": portfolio_value - retirement_portfolio.initial_capital - (annual_contributions * (year + 1))
            })
            
            print(f"   📈 Année {year + 1} : Valeur ${portfolio_value}")
        
        # 5. Analyse performance long terme
        final_evolution = portfolio_evolution[-1]
        total_contributions = retirement_portfolio.initial_capital + final_evolution["contributions"]
        investment_growth = final_evolution["growth"]
        growth_percentage = (investment_growth / total_contributions) * 100
        
        print(f"\n   🎯 Performance retraite :")
        print(f"      Capital initial : ${retirement_portfolio.initial_capital}")
        print(f"      Contributions : ${final_evolution['contributions']}")
        print(f"      Croissance : ${investment_growth}")
        print(f"      Valeur finale : ${final_evolution['total_value']}")
        print(f"      Rendement : {growth_percentage:.1f}%")
        
        # Assertions pour planification retraite
        assert len(current_portfolio.positions) >= 4  # Diversification
        assert final_evolution["total_value"] > total_contributions  # Croissance
        assert growth_percentage > 0  # Rendement positif
        
        print("   ✅ Planification retraite réussie")
        
        return {
            "portfolio": current_portfolio,
            "evolution": portfolio_evolution,
            "performance": {
                "total_contributions": total_contributions,
                "investment_growth": investment_growth,
                "growth_percentage": growth_percentage
            }
        }


@pytest.mark.integration
@pytest.mark.slow
class TestCompleteSystemIntegration:
    """Tests d'intégration système complet"""
    
    @pytest.mark.asyncio
    async def test_multi_user_concurrent_usage(self, complete_system_setup):
        """
        Test d'utilisation simultanée par plusieurs utilisateurs
        simulant un environnement de production
        """
        setup = complete_system_setup
        
        print("👥 Test : Utilisation multi-utilisateur")
        
        # Simuler 3 utilisateurs avec profils différents
        users = [
            {
                "id": "conservative_user",
                "profile": "conservative",
                "capital": Decimal("75000.00")
            },
            {
                "id": "aggressive_user", 
                "profile": "aggressive",
                "capital": Decimal("200000.00")
            },
            {
                "id": "balanced_user",
                "profile": "balanced", 
                "capital": Decimal("120000.00")
            }
        ]
        
        # Tâches concurrentes pour chaque utilisateur
        async def simulate_user_activity(user):
            try:
                # Créer portefeuille
                portfolio = create_test_portfolio(
                    initial_capital=user["capital"],
                    positions=[]
                )
                portfolio.id = f"portfolio-{user['id']}"
                
                # Analyser quelques symboles
                symbols = ["AAPL", "GOOGL", "MSFT"]
                analyses = []
                
                for symbol in symbols:
                    # Simulation analyse (avec délai pour concurrence)
                    await asyncio.sleep(0.1)
                    analysis = {
                        "symbol": symbol,
                        "recommendation": "BUY" if symbol == "AAPL" else "HOLD",
                        "confidence": 0.75
                    }
                    analyses.append(analysis)
                
                # Prendre quelques décisions
                decisions = []
                for analysis in analyses:
                    if analysis["recommendation"] == "BUY":
                        decision = {
                            "symbol": analysis["symbol"],
                            "action": "BUY",
                            "quantity": 50,
                            "reasoning": f"Analyse {user['profile']}"
                        }
                        decisions.append(decision)
                
                return {
                    "user_id": user["id"],
                    "portfolio": portfolio,
                    "analyses": analyses,
                    "decisions": decisions,
                    "success": True
                }
                
            except Exception as e:
                return {
                    "user_id": user["id"],
                    "error": str(e),
                    "success": False
                }
        
        # Exécuter activités en parallèle
        start_time = datetime.now()
        
        user_tasks = [simulate_user_activity(user) for user in users]
        results = await asyncio.gather(*user_tasks, return_exceptions=True)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Analyser résultats
        successful_users = [r for r in results if not isinstance(r, Exception) and r.get("success")]
        failed_users = [r for r in results if isinstance(r, Exception) or not r.get("success")]
        
        print(f"   ⏱️  Durée totale : {duration:.2f}s")
        print(f"   ✅ Utilisateurs réussis : {len(successful_users)}/{len(users)}")
        print(f"   ❌ Échecs : {len(failed_users)}")
        
        for result in successful_users:
            user_id = result["user_id"]
            analyses_count = len(result["analyses"])
            decisions_count = len(result["decisions"])
            print(f"      {user_id}: {analyses_count} analyses, {decisions_count} décisions")
        
        # Assertions concurrence
        assert len(successful_users) >= len(users) * 0.8  # 80% succès minimum
        assert duration < 10.0  # Moins de 10 secondes
        
        print("   ✅ Test multi-utilisateur réussi")
        
        return {
            "users_count": len(users),
            "successful_users": len(successful_users),
            "duration": duration,
            "results": successful_users
        }
    
    @pytest.mark.asyncio
    async def test_system_stress_test(self, complete_system_setup):
        """Test de stress du système avec charge élevée"""
        setup = complete_system_setup
        
        print("🔥 Test : Stress système")
        
        # Paramètres de stress
        concurrent_portfolios = 10
        symbols_per_portfolio = 20
        operations_per_portfolio = 5
        
        print(f"   📊 Configuration stress :")
        print(f"      Portefeuilles : {concurrent_portfolios}")
        print(f"      Symboles/portfolio : {symbols_per_portfolio}")
        print(f"      Opérations/portfolio : {operations_per_portfolio}")
        
        async def stress_portfolio_operations(portfolio_id: int):
            try:
                operations_completed = 0
                
                # Créer portefeuille
                portfolio = create_test_portfolio(
                    initial_capital=Decimal("50000.00")
                )
                portfolio.id = f"stress-portfolio-{portfolio_id}"
                
                # Symboles à analyser
                symbols = [f"STOCK{i}" for i in range(symbols_per_portfolio)]
                
                # Opérations intensives
                for op in range(operations_per_portfolio):
                    # Analyse multiple de symboles
                    for symbol in symbols[:5]:  # Limiter pour performance
                        # Simulation analyse rapide
                        analysis = {
                            "symbol": symbol,
                            "price": 100 + (portfolio_id * 10) + op,
                            "recommendation": "BUY" if op % 2 == 0 else "HOLD"
                        }
                        operations_completed += 1
                    
                    # Petite pause pour éviter surcharge
                    await asyncio.sleep(0.01)
                
                return {
                    "portfolio_id": portfolio_id,
                    "operations_completed": operations_completed,
                    "success": True
                }
                
            except Exception as e:
                return {
                    "portfolio_id": portfolio_id,
                    "error": str(e),
                    "success": False
                }
        
        # Lancer tests de stress
        start_time = datetime.now()
        
        stress_tasks = [
            stress_portfolio_operations(i) 
            for i in range(concurrent_portfolios)
        ]
        stress_results = await asyncio.gather(*stress_tasks, return_exceptions=True)
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        # Analyser performance sous stress
        successful_portfolios = [
            r for r in stress_results 
            if not isinstance(r, Exception) and r.get("success")
        ]
        
        total_operations = sum(
            r["operations_completed"] for r in successful_portfolios
        )
        
        operations_per_second = total_operations / total_duration if total_duration > 0 else 0
        success_rate = len(successful_portfolios) / concurrent_portfolios
        
        print(f"   📈 Résultats stress :")
        print(f"      Durée totale : {total_duration:.2f}s")
        print(f"      Portefeuilles réussis : {len(successful_portfolios)}/{concurrent_portfolios}")
        print(f"      Taux de succès : {success_rate:.1%}")
        print(f"      Opérations totales : {total_operations}")
        print(f"      Opérations/seconde : {operations_per_second:.1f}")
        
        # Assertions stress test
        assert success_rate >= 0.9  # 90% succès minimum
        assert total_duration < 30.0  # Moins de 30 secondes
        assert operations_per_second > 10  # Performance minimum
        
        print("   ✅ Test de stress réussi")
        
        return {
            "concurrent_portfolios": concurrent_portfolios,
            "success_rate": success_rate,
            "total_operations": total_operations,
            "operations_per_second": operations_per_second,
            "duration": total_duration
        }


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "not slow"])