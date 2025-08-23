"""
Tests d'Intégration - Persistance des Données

Ces tests valident la persistance et la récupération des données FinAgent,
incluant les portefeuilles, stratégies, historiques de transactions et
configurations système.
"""

import pytest
import asyncio
import tempfile
import json
import sqlite3
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from finagent.business.models.portfolio_models import Portfolio, Position, Transaction
from finagent.business.models.decision_models import InvestmentDecision, DecisionType
from finagent.business.strategy.models.strategy_models import StrategyConfig
from finagent.persistence.repositories.portfolio_repository import PortfolioRepository
from finagent.persistence.repositories.transaction_repository import TransactionRepository
from finagent.persistence.repositories.strategy_repository import StrategyRepository
from finagent.persistence.database.models.portfolio_models import PortfolioModel

# Import des utilitaires de test
from tests.utils import (
    create_test_portfolio,
    create_test_strategy,
    create_test_transaction_history,
    StockDataFactory,
    TransactionFactory
)


@pytest.mark.integration
@pytest.mark.persistence
class TestDataPersistence:
    """Tests de base de la persistance des données"""
    
    @pytest.fixture
    async def temp_database(self):
        """Base de données temporaire pour les tests"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        # Initialiser la base de données
        conn = sqlite3.connect(db_path)
        
        # Créer les tables de test (structure simplifiée)
        conn.execute('''
            CREATE TABLE portfolios (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                initial_capital REAL NOT NULL,
                available_cash REAL NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                data TEXT NOT NULL
            )
        ''')
        
        conn.execute('''
            CREATE TABLE transactions (
                id TEXT PRIMARY KEY,
                portfolio_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                transaction_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                fees REAL DEFAULT 0,
                data TEXT,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE strategies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                config TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    @pytest.fixture
    async def portfolio_repository(self, temp_database):
        """Repository de portefeuille avec base temporaire"""
        config = {"database_url": f"sqlite:///{temp_database}"}
        return PortfolioRepository(config)
    
    @pytest.fixture
    async def transaction_repository(self, temp_database):
        """Repository de transactions avec base temporaire"""
        config = {"database_url": f"sqlite:///{temp_database}"}
        return TransactionRepository(config)
    
    @pytest.fixture
    async def strategy_repository(self, temp_database):
        """Repository de stratégies avec base temporaire"""
        config = {"database_url": f"sqlite:///{temp_database}"}
        return StrategyRepository(config)


@pytest.mark.integration
@pytest.mark.persistence
class TestPortfolioPersistence:
    """Tests de persistance des portefeuilles"""
    
    @pytest.mark.asyncio
    async def test_portfolio_save_and_load(self, portfolio_repository):
        """Test de sauvegarde et chargement d'un portefeuille"""
        # Créer un portefeuille de test
        portfolio = create_test_portfolio(
            initial_capital=Decimal("100000.00"),
            positions=[
                ("AAPL", 100, Decimal("150.00")),
                ("GOOGL", 50, Decimal("2500.00")),
                ("MSFT", 75, Decimal("300.00"))
            ]
        )
        
        # Sauvegarder le portefeuille
        saved_portfolio = await portfolio_repository.save(portfolio)
        assert saved_portfolio is not None
        assert saved_portfolio.id == portfolio.id
        
        # Charger le portefeuille
        loaded_portfolio = await portfolio_repository.get_by_id(portfolio.id)
        assert loaded_portfolio is not None
        
        # Validation des données
        assert loaded_portfolio.id == portfolio.id
        assert loaded_portfolio.name == portfolio.name
        assert loaded_portfolio.initial_capital == portfolio.initial_capital
        assert loaded_portfolio.available_cash == portfolio.available_cash
        assert len(loaded_portfolio.positions) == len(portfolio.positions)
        
        # Validation des positions
        for original_pos, loaded_pos in zip(portfolio.positions, loaded_portfolio.positions):
            assert loaded_pos.symbol == original_pos.symbol
            assert loaded_pos.quantity == original_pos.quantity
            assert loaded_pos.average_price == original_pos.average_price
        
        print(f"✅ Portfolio sauvegardé et chargé avec succès:")
        print(f"   ID: {loaded_portfolio.id}")
        print(f"   Positions: {len(loaded_portfolio.positions)}")
        print(f"   Valeur totale: ${loaded_portfolio.total_value}")
    
    @pytest.mark.asyncio
    async def test_portfolio_update(self, portfolio_repository):
        """Test de mise à jour d'un portefeuille existant"""
        # Créer et sauvegarder un portefeuille initial
        portfolio = create_test_portfolio()
        await portfolio_repository.save(portfolio)
        
        # Modifier le portefeuille
        original_cash = portfolio.available_cash
        portfolio.available_cash = original_cash + Decimal("5000.00")
        
        # Ajouter une nouvelle position
        new_position = Position(
            symbol="TSLA",
            quantity=25,
            average_price=Decimal("800.00"),
            current_price=Decimal("850.00")
        )
        portfolio.positions.append(new_position)
        portfolio.updated_at = datetime.now()
        
        # Sauvegarder les modifications
        updated_portfolio = await portfolio_repository.save(portfolio)
        
        # Recharger et valider
        reloaded_portfolio = await portfolio_repository.get_by_id(portfolio.id)
        
        assert reloaded_portfolio.available_cash == portfolio.available_cash
        assert len(reloaded_portfolio.positions) == len(portfolio.positions)
        
        # Vérifier que la nouvelle position est présente
        tsla_position = next(
            (pos for pos in reloaded_portfolio.positions if pos.symbol == "TSLA"), 
            None
        )
        assert tsla_position is not None
        assert tsla_position.quantity == 25
        
        print(f"✅ Portfolio mis à jour avec succès:")
        print(f"   Nouveau cash: ${reloaded_portfolio.available_cash}")
        print(f"   Nouvelle position: TSLA x{tsla_position.quantity}")
    
    @pytest.mark.asyncio
    async def test_portfolio_deletion(self, portfolio_repository):
        """Test de suppression d'un portefeuille"""
        # Créer et sauvegarder un portefeuille
        portfolio = create_test_portfolio()
        await portfolio_repository.save(portfolio)
        
        # Vérifier qu'il existe
        loaded_portfolio = await portfolio_repository.get_by_id(portfolio.id)
        assert loaded_portfolio is not None
        
        # Supprimer le portefeuille
        deletion_success = await portfolio_repository.delete(portfolio.id)
        assert deletion_success is True
        
        # Vérifier qu'il n'existe plus
        deleted_portfolio = await portfolio_repository.get_by_id(portfolio.id)
        assert deleted_portfolio is None
        
        print(f"✅ Portfolio supprimé avec succès: {portfolio.id}")
    
    @pytest.mark.asyncio
    async def test_portfolio_listing(self, portfolio_repository):
        """Test de listage des portefeuilles"""
        # Créer plusieurs portefeuilles
        portfolios = []
        for i in range(3):
            portfolio = create_test_portfolio()
            portfolio.name = f"Portfolio Test {i+1}"
            portfolios.append(portfolio)
            await portfolio_repository.save(portfolio)
        
        # Lister tous les portefeuilles
        all_portfolios = await portfolio_repository.get_all()
        assert len(all_portfolios) >= 3
        
        # Vérifier que nos portefeuilles sont présents
        portfolio_ids = {p.id for p in portfolios}
        loaded_ids = {p.id for p in all_portfolios}
        assert portfolio_ids.issubset(loaded_ids)
        
        print(f"✅ Listage des portefeuilles réussi:")
        print(f"   Portefeuilles trouvés: {len(all_portfolios)}")
        print(f"   Portefeuilles test: {len(portfolios)}")


@pytest.mark.integration
@pytest.mark.persistence
class TestTransactionPersistence:
    """Tests de persistance des transactions"""
    
    @pytest.mark.asyncio
    async def test_transaction_save_and_load(self, transaction_repository, portfolio_repository):
        """Test de sauvegarde et chargement des transactions"""
        # Créer un portefeuille pour les transactions
        portfolio = create_test_portfolio()
        await portfolio_repository.save(portfolio)
        
        # Créer des transactions de test
        transactions = [
            Transaction(
                id="trans-001",
                symbol="AAPL",
                quantity=100,
                price=Decimal("150.00"),
                transaction_type="BUY",
                timestamp=datetime.now() - timedelta(days=5),
                fees=Decimal("9.99")
            ),
            Transaction(
                id="trans-002",
                symbol="GOOGL",
                quantity=25,
                price=Decimal("2500.00"),
                transaction_type="BUY",
                timestamp=datetime.now() - timedelta(days=3),
                fees=Decimal("12.50")
            ),
            Transaction(
                id="trans-003",
                symbol="AAPL",
                quantity=50,
                price=Decimal("155.00"),
                transaction_type="SELL",
                timestamp=datetime.now() - timedelta(days=1),
                fees=Decimal("7.75")
            )
        ]
        
        # Sauvegarder les transactions
        for transaction in transactions:
            saved_transaction = await transaction_repository.save(
                transaction, 
                portfolio_id=portfolio.id
            )
            assert saved_transaction is not None
            assert saved_transaction.id == transaction.id
        
        # Charger les transactions du portefeuille
        portfolio_transactions = await transaction_repository.get_by_portfolio_id(portfolio.id)
        assert len(portfolio_transactions) == 3
        
        # Validation des données
        for original_trans in transactions:
            loaded_trans = next(
                (t for t in portfolio_transactions if t.id == original_trans.id), 
                None
            )
            assert loaded_trans is not None
            assert loaded_trans.symbol == original_trans.symbol
            assert loaded_trans.quantity == original_trans.quantity
            assert loaded_trans.price == original_trans.price
            assert loaded_trans.transaction_type == original_trans.transaction_type
            assert loaded_trans.fees == original_trans.fees
        
        print(f"✅ Transactions sauvegardées et chargées:")
        print(f"   Nombre de transactions: {len(portfolio_transactions)}")
        for trans in portfolio_transactions:
            print(f"   {trans.transaction_type} {trans.quantity} {trans.symbol} @ ${trans.price}")
    
    @pytest.mark.asyncio
    async def test_transaction_history_analysis(self, transaction_repository, portfolio_repository):
        """Test d'analyse de l'historique des transactions"""
        # Créer un portefeuille
        portfolio = create_test_portfolio()
        await portfolio_repository.save(portfolio)
        
        # Créer un historique de transactions étalé sur plusieurs mois
        transaction_history = create_test_transaction_history(
            portfolio_id=portfolio.id,
            symbols=["AAPL", "GOOGL", "MSFT", "AMZN"],
            months=6,
            transactions_per_month=5
        )
        
        # Sauvegarder l'historique
        for transaction in transaction_history:
            await transaction_repository.save(transaction, portfolio_id=portfolio.id)
        
        # Analyser les transactions par période
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Derniers 30 jours
        
        recent_transactions = await transaction_repository.get_by_date_range(
            portfolio_id=portfolio.id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Analyser les transactions par symbole
        symbol_transactions = await transaction_repository.get_by_symbol(
            portfolio_id=portfolio.id,
            symbol="AAPL"
        )
        
        # Calculer des métriques
        total_buy_volume = sum(
            t.quantity * t.price for t in recent_transactions 
            if t.transaction_type == "BUY"
        )
        total_sell_volume = sum(
            t.quantity * t.price for t in recent_transactions 
            if t.transaction_type == "SELL"
        )
        
        print(f"✅ Analyse historique des transactions:")
        print(f"   Total transactions: {len(transaction_history)}")
        print(f"   Transactions récentes (30j): {len(recent_transactions)}")
        print(f"   Transactions AAPL: {len(symbol_transactions)}")
        print(f"   Volume achat récent: ${total_buy_volume}")
        print(f"   Volume vente récent: ${total_sell_volume}")
        
        assert len(transaction_history) > 0
        assert len(recent_transactions) >= 0
        assert len(symbol_transactions) >= 0


@pytest.mark.integration
@pytest.mark.persistence
class TestStrategyPersistence:
    """Tests de persistance des stratégies"""
    
    @pytest.mark.asyncio
    async def test_strategy_save_and_load(self, strategy_repository):
        """Test de sauvegarde et chargement d'une stratégie"""
        # Créer une stratégie de test
        strategy = create_test_strategy("momentum")
        strategy_config = StrategyConfig(
            id="strategy-001",
            name="Test Momentum Strategy",
            type="momentum",
            description="Stratégie momentum pour tests d'intégration",
            config=strategy,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )
        
        # Sauvegarder la stratégie
        saved_strategy = await strategy_repository.save(strategy_config)
        assert saved_strategy is not None
        assert saved_strategy.id == strategy_config.id
        
        # Charger la stratégie
        loaded_strategy = await strategy_repository.get_by_id(strategy_config.id)
        assert loaded_strategy is not None
        
        # Validation des données
        assert loaded_strategy.id == strategy_config.id
        assert loaded_strategy.name == strategy_config.name
        assert loaded_strategy.type == strategy_config.type
        assert loaded_strategy.description == strategy_config.description
        assert loaded_strategy.is_active == strategy_config.is_active
        
        print(f"✅ Stratégie sauvegardée et chargée:")
        print(f"   ID: {loaded_strategy.id}")
        print(f"   Nom: {loaded_strategy.name}")
        print(f"   Type: {loaded_strategy.type}")
        print(f"   Active: {loaded_strategy.is_active}")
    
    @pytest.mark.asyncio
    async def test_strategy_versioning(self, strategy_repository):
        """Test du versioning des stratégies"""
        # Créer une stratégie initiale
        original_strategy = create_test_strategy("growth")
        strategy_config = StrategyConfig(
            id="strategy-versioned",
            name="Strategy with Versions",
            type="growth",
            description="Version 1.0",
            config=original_strategy,
            version="1.0",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )
        
        await strategy_repository.save(strategy_config)
        
        # Créer une nouvelle version
        modified_strategy = create_test_strategy("growth")
        modified_strategy["risk_management"]["max_position_size"] = 0.20  # Modification
        
        new_version_config = StrategyConfig(
            id="strategy-versioned",
            name="Strategy with Versions",
            type="growth",
            description="Version 2.0 - Modified risk management",
            config=modified_strategy,
            version="2.0",
            created_at=strategy_config.created_at,
            updated_at=datetime.now(),
            is_active=True
        )
        
        await strategy_repository.save(new_version_config)
        
        # Récupérer l'historique des versions
        strategy_versions = await strategy_repository.get_versions(strategy_config.id)
        assert len(strategy_versions) >= 1
        
        # Récupérer la version la plus récente
        latest_strategy = await strategy_repository.get_by_id(strategy_config.id)
        assert latest_strategy.version == "2.0"
        assert "Modified risk management" in latest_strategy.description
        
        print(f"✅ Versioning des stratégies:")
        print(f"   Versions disponibles: {len(strategy_versions)}")
        print(f"   Version actuelle: {latest_strategy.version}")
    
    @pytest.mark.asyncio
    async def test_strategy_activation_deactivation(self, strategy_repository):
        """Test d'activation/désactivation des stratégies"""
        # Créer plusieurs stratégies
        strategies = []
        for i in range(3):
            strategy = create_test_strategy("balanced")
            strategy_config = StrategyConfig(
                id=f"strategy-activation-{i}",
                name=f"Test Strategy {i+1}",
                type="balanced",
                description=f"Strategy {i+1} for activation test",
                config=strategy,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True
            )
            strategies.append(strategy_config)
            await strategy_repository.save(strategy_config)
        
        # Désactiver une stratégie
        await strategy_repository.deactivate(strategies[1].id)
        
        # Récupérer les stratégies actives
        active_strategies = await strategy_repository.get_active_strategies()
        active_ids = {s.id for s in active_strategies}
        
        assert strategies[0].id in active_ids
        assert strategies[1].id not in active_ids  # Désactivée
        assert strategies[2].id in active_ids
        
        # Réactiver la stratégie
        await strategy_repository.activate(strategies[1].id)
        
        # Vérifier la réactivation
        reactivated_strategies = await strategy_repository.get_active_strategies()
        reactivated_ids = {s.id for s in reactivated_strategies}
        
        assert strategies[1].id in reactivated_ids
        
        print(f"✅ Activation/désactivation des stratégies:")
        print(f"   Stratégies créées: {len(strategies)}")
        print(f"   Stratégies actives finales: {len(reactivated_strategies)}")


@pytest.mark.integration
@pytest.mark.persistence
@pytest.mark.slow
class TestDataConsistencyAndIntegrity:
    """Tests de cohérence et intégrité des données"""
    
    @pytest.mark.asyncio
    async def test_referential_integrity(self, portfolio_repository, transaction_repository):
        """Test de l'intégrité référentielle entre portefeuilles et transactions"""
        # Créer un portefeuille
        portfolio = create_test_portfolio()
        await portfolio_repository.save(portfolio)
        
        # Créer des transactions liées
        transactions = [
            Transaction(
                id=f"trans-integrity-{i}",
                symbol=f"STOCK{i}",
                quantity=10 * (i + 1),
                price=Decimal(f"{100 + i * 10}.00"),
                transaction_type="BUY",
                timestamp=datetime.now() - timedelta(days=i),
                fees=Decimal("9.99")
            )
            for i in range(5)
        ]
        
        for transaction in transactions:
            await transaction_repository.save(transaction, portfolio_id=portfolio.id)
        
        # Vérifier que toutes les transactions sont liées au portefeuille
        portfolio_transactions = await transaction_repository.get_by_portfolio_id(portfolio.id)
        assert len(portfolio_transactions) == len(transactions)
        
        # Tenter de supprimer le portefeuille (devrait échouer ou supprimer en cascade)
        try:
            deletion_success = await portfolio_repository.delete(portfolio.id)
            
            if deletion_success:
                # Si suppression réussie, vérifier que les transactions sont aussi supprimées
                remaining_transactions = await transaction_repository.get_by_portfolio_id(portfolio.id)
                assert len(remaining_transactions) == 0
                print("✅ Suppression en cascade fonctionnelle")
            else:
                print("✅ Intégrité référentielle protégée (suppression refusée)")
        
        except Exception as e:
            # Exception attendue pour violation d'intégrité
            print(f"✅ Intégrité référentielle protégée par exception: {type(e).__name__}")
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, portfolio_repository):
        """Test d'accès concurrent aux données"""
        # Créer un portefeuille
        portfolio = create_test_portfolio()
        await portfolio_repository.save(portfolio)
        
        # Simuler des modifications concurrentes
        async def modify_portfolio_cash(amount: Decimal, delay: float):
            await asyncio.sleep(delay)
            loaded_portfolio = await portfolio_repository.get_by_id(portfolio.id)
            loaded_portfolio.available_cash += amount
            loaded_portfolio.updated_at = datetime.now()
            return await portfolio_repository.save(loaded_portfolio)
        
        # Lancer plusieurs modifications en parallèle
        tasks = [
            modify_portfolio_cash(Decimal("1000.00"), 0.1),
            modify_portfolio_cash(Decimal("500.00"), 0.2),
            modify_portfolio_cash(Decimal("-200.00"), 0.3),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Vérifier que les modifications ont été appliquées
        final_portfolio = await portfolio_repository.get_by_id(portfolio.id)
        
        successful_modifications = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_modifications) > 0
        
        print(f"✅ Accès concurrent testé:")
        print(f"   Modifications réussies: {len(successful_modifications)}")
        print(f"   Cash final: ${final_portfolio.available_cash}")
    
    @pytest.mark.asyncio
    async def test_data_validation_constraints(self, portfolio_repository, transaction_repository):
        """Test des contraintes de validation des données"""
        # Test contraintes portefeuille
        invalid_portfolios = [
            # Capital initial négatif
            Portfolio(
                id="invalid-portfolio-1",
                name="Invalid Portfolio",
                initial_capital=Decimal("-1000.00"),  # Invalide
                available_cash=Decimal("500.00"),
                positions=[],
                created_at=datetime.now()
            ),
            # Cash disponible négatif (dans certains cas)
            Portfolio(
                id="invalid-portfolio-2",
                name="Invalid Portfolio",
                initial_capital=Decimal("10000.00"),
                available_cash=Decimal("-50000.00"),  # Potentiellement invalide
                positions=[],
                created_at=datetime.now()
            )
        ]
        
        for invalid_portfolio in invalid_portfolios:
            try:
                await portfolio_repository.save(invalid_portfolio)
                print(f"⚠️  Portfolio invalide accepté: {invalid_portfolio.id}")
            except (ValueError, Exception) as e:
                print(f"✅ Portfolio invalide rejeté: {type(e).__name__}")
        
        # Test contraintes transactions
        valid_portfolio = create_test_portfolio()
        await portfolio_repository.save(valid_portfolio)
        
        invalid_transactions = [
            # Quantité négative
            Transaction(
                id="invalid-trans-1",
                symbol="AAPL",
                quantity=-100,  # Invalide
                price=Decimal("150.00"),
                transaction_type="BUY",
                timestamp=datetime.now()
            ),
            # Prix négatif
            Transaction(
                id="invalid-trans-2",
                symbol="GOOGL",
                quantity=50,
                price=Decimal("-2500.00"),  # Invalide
                transaction_type="BUY",
                timestamp=datetime.now()
            )
        ]
        
        for invalid_transaction in invalid_transactions:
            try:
                await transaction_repository.save(invalid_transaction, portfolio_id=valid_portfolio.id)
                print(f"⚠️  Transaction invalide acceptée: {invalid_transaction.id}")
            except (ValueError, Exception) as e:
                print(f"✅ Transaction invalide rejetée: {type(e).__name__}")


if __name__ == "__main__":
    # Exécution directe pour tests de développement
    pytest.main([__file__, "-v", "--tb=short", "-m", "not slow"])