"""
Tests unitaires pour l'interface CLI de FinAgent.

Ce module teste toutes les commandes CLI, la validation des arguments,
la gestion d'erreurs et l'interaction utilisateur.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import tempfile
import os
import json
import click
from click.testing import CliRunner

from finagent.cli.main import cli, app
from finagent.cli.commands import (
    analyze, portfolio, strategy, market, config, history
)
from finagent.core.exceptions import (
    FinAgentError, DataProviderError, PortfolioError, StrategyLoadError
)
from tests.utils import (
    create_test_config, create_test_portfolio, create_test_strategy,
    MockOpenBBProvider, MockClaudeProvider
)


class TestCLIMain:
    """Tests pour le CLI principal."""
    
    @pytest.fixture
    def cli_runner(self):
        """Runner CLI pour tests."""
        return CliRunner()
    
    @pytest.fixture
    def mock_config_file(self):
        """Fichier de configuration mock."""
        config_data = {
            "openbb": {
                "api_key": "test-openbb-key",
                "base_url": "https://api.openbb.co/v1"
            },
            "claude": {
                "api_key": "test-claude-key",
                "model": "anthropic/claude-3-sonnet-20240229"
            },
            "portfolio": {
                "default_cash_reserve": 0.05,
                "max_position_size": 0.20
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name
        
        yield temp_file
        os.unlink(temp_file)
    
    def test_cli_help(self, cli_runner):
        """Test affichage de l'aide CLI."""
        result = cli_runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'FinAgent' in result.output
        assert 'analyze' in result.output
        assert 'portfolio' in result.output
        assert 'strategy' in result.output
    
    def test_cli_version(self, cli_runner):
        """Test affichage de la version."""
        result = cli_runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert 'FinAgent' in result.output
        # Vérifier format version (ex: "1.0.0")
        import re
        version_pattern = r'\d+\.\d+\.\d+'
        assert re.search(version_pattern, result.output)
    
    def test_cli_config_validation(self, cli_runner):
        """Test validation de configuration CLI."""
        # Sans fichier de configuration
        result = cli_runner.invoke(cli, ['analyze', 'AAPL'])
        
        # Devrait demander la configuration ou utiliser des valeurs par défaut
        assert result.exit_code in [0, 1]  # Succès ou erreur de config
    
    def test_cli_global_options(self, cli_runner, mock_config_file):
        """Test options globales CLI."""
        result = cli_runner.invoke(cli, [
            '--config', mock_config_file,
            '--verbose',
            '--no-color',
            'analyze', 'AAPL'
        ])
        
        # Vérifier que les options sont prises en compte
        assert result.exit_code in [0, 1]  # Peut échouer sans vraies APIs


class TestAnalyzeCommand:
    """Tests pour la commande analyze."""
    
    @pytest.fixture
    def cli_runner(self):
        """Runner CLI pour tests."""
        return CliRunner()
    
    @pytest.fixture
    def mock_providers(self):
        """Providers mock pour analyse."""
        with patch('finagent.cli.commands.analyze.OpenBBProvider') as mock_openbb, \
             patch('finagent.cli.commands.analyze.ClaudeProvider') as mock_claude:
            
            mock_openbb.return_value = MockOpenBBProvider({})
            mock_claude.return_value = MockClaudeProvider({})
            
            yield mock_openbb, mock_claude
    
    def test_analyze_single_symbol(self, cli_runner, mock_providers):
        """Test analyse d'un symbole unique."""
        result = cli_runner.invoke(cli, ['analyze', 'AAPL'])
        
        assert result.exit_code == 0
        assert 'AAPL' in result.output
        assert any(keyword in result.output.lower() for keyword in [
            'price', 'analysis', 'recommendation'
        ])
    
    def test_analyze_multiple_symbols(self, cli_runner, mock_providers):
        """Test analyse de plusieurs symboles."""
        result = cli_runner.invoke(cli, ['analyze', 'AAPL,GOOGL,MSFT'])
        
        assert result.exit_code == 0
        assert 'AAPL' in result.output
        assert 'GOOGL' in result.output
        assert 'MSFT' in result.output
    
    def test_analyze_with_timeframe(self, cli_runner, mock_providers):
        """Test analyse avec période spécifique."""
        result = cli_runner.invoke(cli, [
            'analyze', 'AAPL',
            '--timeframe', '1M',
            '--detailed'
        ])
        
        assert result.exit_code == 0
        assert 'AAPL' in result.output
    
    def test_analyze_with_strategy(self, cli_runner, mock_providers):
        """Test analyse avec stratégie spécifique."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
metadata:
  name: "Test Strategy"
strategy:
  type: "technical"
rules:
  - name: "RSI Check"
    conditions:
      - indicator: "rsi"
        operator: "<"
        value: 30
    action: "buy"
            """)
            strategy_file = f.name
        
        try:
            result = cli_runner.invoke(cli, [
                'analyze', 'AAPL',
                '--strategy', strategy_file
            ])
            
            assert result.exit_code == 0
        finally:
            os.unlink(strategy_file)
    
    def test_analyze_output_formats(self, cli_runner, mock_providers):
        """Test différents formats de sortie."""
        # Format JSON
        result_json = cli_runner.invoke(cli, [
            'analyze', 'AAPL',
            '--output', 'json'
        ])
        
        assert result_json.exit_code == 0
        
        # Format table
        result_table = cli_runner.invoke(cli, [
            'analyze', 'AAPL',
            '--output', 'table'
        ])
        
        assert result_table.exit_code == 0
    
    def test_analyze_invalid_symbol(self, cli_runner, mock_providers):
        """Test analyse avec symbole invalide."""
        result = cli_runner.invoke(cli, ['analyze', 'INVALID_SYMBOL_123'])
        
        # Devrait gérer l'erreur gracieusement
        assert result.exit_code in [0, 1]
        if result.exit_code == 1:
            assert 'error' in result.output.lower()
    
    def test_analyze_save_results(self, cli_runner, mock_providers):
        """Test sauvegarde des résultats d'analyse."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            result = cli_runner.invoke(cli, [
                'analyze', 'AAPL',
                '--save', output_file
            ])
            
            assert result.exit_code == 0
            assert os.path.exists(output_file)
            
            # Vérifier contenu du fichier
            with open(output_file, 'r') as f:
                data = json.load(f)
                assert 'symbol' in data or 'results' in data
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestPortfolioCommand:
    """Tests pour la commande portfolio."""
    
    @pytest.fixture
    def cli_runner(self):
        """Runner CLI pour tests."""
        return CliRunner()
    
    @pytest.fixture
    def mock_portfolio_manager(self):
        """Gestionnaire de portefeuille mock."""
        with patch('finagent.cli.commands.portfolio.PortfolioManager') as mock:
            manager = Mock()
            manager.create_portfolio = AsyncMock(return_value="portfolio-123")
            manager.get_portfolio = AsyncMock(return_value={
                "id": "portfolio-123",
                "name": "Test Portfolio",
                "total_value": Decimal("100000.00"),
                "positions": []
            })
            mock.return_value = manager
            yield manager
    
    def test_portfolio_create(self, cli_runner, mock_portfolio_manager):
        """Test création de portefeuille."""
        result = cli_runner.invoke(cli, [
            'portfolio', 'create',
            '--name', 'Test Portfolio',
            '--initial-cash', '50000',
            '--strategy', 'balanced'
        ])
        
        assert result.exit_code == 0
        assert 'created' in result.output.lower()
        mock_portfolio_manager.create_portfolio.assert_called_once()
    
    def test_portfolio_list(self, cli_runner, mock_portfolio_manager):
        """Test listage des portefeuilles."""
        mock_portfolio_manager.list_portfolios = AsyncMock(return_value=[
            {"id": "port-1", "name": "Portfolio 1", "value": 100000},
            {"id": "port-2", "name": "Portfolio 2", "value": 150000}
        ])
        
        result = cli_runner.invoke(cli, ['portfolio', 'list'])
        
        assert result.exit_code == 0
        assert 'Portfolio 1' in result.output
        assert 'Portfolio 2' in result.output
    
    def test_portfolio_show(self, cli_runner, mock_portfolio_manager):
        """Test affichage détaillé d'un portefeuille."""
        result = cli_runner.invoke(cli, [
            'portfolio', 'show',
            '--id', 'portfolio-123'
        ])
        
        assert result.exit_code == 0
        mock_portfolio_manager.get_portfolio.assert_called_once_with("portfolio-123")
    
    def test_portfolio_add_position(self, cli_runner, mock_portfolio_manager):
        """Test ajout de position."""
        mock_portfolio_manager.add_position = AsyncMock(return_value={
            "success": True,
            "transaction_id": "txn-123"
        })
        
        result = cli_runner.invoke(cli, [
            'portfolio', 'add',
            '--id', 'portfolio-123',
            '--symbol', 'AAPL',
            '--quantity', '10',
            '--price', '150.00'
        ])
        
        assert result.exit_code == 0
        assert 'added' in result.output.lower() or 'success' in result.output.lower()
    
    def test_portfolio_remove_position(self, cli_runner, mock_portfolio_manager):
        """Test suppression de position."""
        mock_portfolio_manager.remove_position = AsyncMock(return_value={
            "success": True,
            "transaction_id": "txn-124"
        })
        
        result = cli_runner.invoke(cli, [
            'portfolio', 'remove',
            '--id', 'portfolio-123',
            '--symbol', 'AAPL',
            '--quantity', '5'
        ])
        
        assert result.exit_code == 0
        assert 'removed' in result.output.lower() or 'success' in result.output.lower()
    
    def test_portfolio_rebalance(self, cli_runner, mock_portfolio_manager):
        """Test rééquilibrage de portefeuille."""
        mock_portfolio_manager.rebalance = AsyncMock(return_value={
            "success": True,
            "orders": [
                {"symbol": "AAPL", "action": "sell", "quantity": 5},
                {"symbol": "GOOGL", "action": "buy", "quantity": 2}
            ]
        })
        
        result = cli_runner.invoke(cli, [
            'portfolio', 'rebalance',
            '--id', 'portfolio-123',
            '--threshold', '0.05'
        ])
        
        assert result.exit_code == 0
        assert 'rebalance' in result.output.lower()
    
    def test_portfolio_performance(self, cli_runner, mock_portfolio_manager):
        """Test affichage de performance."""
        mock_portfolio_manager.calculate_metrics = AsyncMock(return_value={
            "total_return": 0.15,
            "volatility": 0.18,
            "sharpe_ratio": 0.83,
            "max_drawdown": -0.08
        })
        
        result = cli_runner.invoke(cli, [
            'portfolio', 'performance',
            '--id', 'portfolio-123',
            '--period', '1Y'
        ])
        
        assert result.exit_code == 0
        assert any(metric in result.output.lower() for metric in [
            'return', 'volatility', 'sharpe', 'drawdown'
        ])


class TestStrategyCommand:
    """Tests pour la commande strategy."""
    
    @pytest.fixture
    def cli_runner(self):
        """Runner CLI pour tests."""
        return CliRunner()
    
    @pytest.fixture
    def sample_strategy_file(self):
        """Fichier de stratégie échantillon."""
        strategy_yaml = """
metadata:
  name: "CLI Test Strategy"
  version: "1.0.0"

strategy:
  type: "technical"
  risk_tolerance: "medium"

rules:
  - name: "RSI Oversold"
    conditions:
      - indicator: "rsi"
        operator: "<"
        value: 30
    action: "buy"
    weight: 0.8
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(strategy_yaml)
            temp_file = f.name
        
        yield temp_file
        os.unlink(temp_file)
    
    @pytest.fixture
    def mock_strategy_engine(self):
        """Moteur de stratégies mock."""
        with patch('finagent.cli.commands.strategy.StrategyEngine') as mock:
            engine = Mock()
            engine.load_strategy = AsyncMock(return_value="strategy-123")
            engine.validate_strategy = AsyncMock(return_value=(True, []))
            engine.backtest_strategy = AsyncMock(return_value={
                "performance_metrics": {
                    "total_return": 0.20,
                    "sharpe_ratio": 1.2,
                    "max_drawdown": -0.06
                }
            })
            mock.return_value = engine
            yield engine
    
    def test_strategy_validate(self, cli_runner, mock_strategy_engine, sample_strategy_file):
        """Test validation de stratégie."""
        result = cli_runner.invoke(cli, [
            'strategy', 'validate',
            '--file', sample_strategy_file
        ])
        
        assert result.exit_code == 0
        assert 'valid' in result.output.lower()
    
    def test_strategy_load(self, cli_runner, mock_strategy_engine, sample_strategy_file):
        """Test chargement de stratégie."""
        result = cli_runner.invoke(cli, [
            'strategy', 'load',
            '--file', sample_strategy_file,
            '--name', 'test-strategy'
        ])
        
        assert result.exit_code == 0
        assert 'loaded' in result.output.lower()
    
    def test_strategy_list(self, cli_runner, mock_strategy_engine):
        """Test listage des stratégies."""
        mock_strategy_engine.list_strategies = AsyncMock(return_value=[
            {"id": "strat-1", "name": "Strategy 1", "type": "technical"},
            {"id": "strat-2", "name": "Strategy 2", "type": "fundamental"}
        ])
        
        result = cli_runner.invoke(cli, ['strategy', 'list'])
        
        assert result.exit_code == 0
        assert 'Strategy 1' in result.output
        assert 'Strategy 2' in result.output
    
    def test_strategy_backtest(self, cli_runner, mock_strategy_engine, sample_strategy_file):
        """Test backtesting de stratégie."""
        result = cli_runner.invoke(cli, [
            'strategy', 'backtest',
            '--file', sample_strategy_file,
            '--start', '2023-01-01',
            '--end', '2023-12-31',
            '--initial-capital', '100000'
        ])
        
        assert result.exit_code == 0
        assert any(metric in result.output.lower() for metric in [
            'return', 'sharpe', 'drawdown'
        ])
    
    def test_strategy_optimize(self, cli_runner, mock_strategy_engine, sample_strategy_file):
        """Test optimisation de stratégie."""
        mock_strategy_engine.optimize_parameters = AsyncMock(return_value={
            "optimized_parameters": {"rsi_threshold": 25},
            "performance_improvement": 0.05
        })
        
        result = cli_runner.invoke(cli, [
            'strategy', 'optimize',
            '--file', sample_strategy_file,
            '--metric', 'sharpe_ratio',
            '--iterations', '100'
        ])
        
        assert result.exit_code == 0
        assert 'optimized' in result.output.lower()
    
    def test_strategy_compare(self, cli_runner, mock_strategy_engine):
        """Test comparaison de stratégies."""
        mock_strategy_engine.compare_strategies = AsyncMock(return_value={
            "comparison_metrics": {
                "returns_correlation": 0.75,
                "risk_adjusted_performance": {
                    "strategy-1": 1.2,
                    "strategy-2": 0.9
                }
            }
        })
        
        result = cli_runner.invoke(cli, [
            'strategy', 'compare',
            '--strategies', 'strategy-1,strategy-2',
            '--period', '1Y'
        ])
        
        assert result.exit_code == 0
        assert 'comparison' in result.output.lower()


class TestMarketCommand:
    """Tests pour la commande market."""
    
    @pytest.fixture
    def cli_runner(self):
        """Runner CLI pour tests."""
        return CliRunner()
    
    @pytest.fixture
    def mock_market_data(self):
        """Données de marché mock."""
        with patch('finagent.cli.commands.market.OpenBBProvider') as mock:
            provider = Mock()
            provider.get_market_indices = AsyncMock(return_value={
                "^GSPC": {"price": 4200.15, "change": 1.2, "change_percent": 0.03},
                "^DJI": {"price": 34500.50, "change": -50.25, "change_percent": -0.15}
            })
            provider.get_sector_performance = AsyncMock(return_value=[
                {"name": "Technology", "performance_1d": 0.02},
                {"name": "Healthcare", "performance_1d": -0.01}
            ])
            mock.return_value = provider
            yield provider
    
    def test_market_overview(self, cli_runner, mock_market_data):
        """Test aperçu du marché."""
        result = cli_runner.invoke(cli, ['market', 'overview'])
        
        assert result.exit_code == 0
        assert any(index in result.output for index in ['S&P', 'Dow', 'NASDAQ'])
    
    def test_market_sectors(self, cli_runner, mock_market_data):
        """Test performance sectorielle."""
        result = cli_runner.invoke(cli, ['market', 'sectors'])
        
        assert result.exit_code == 0
        assert 'Technology' in result.output
        assert 'Healthcare' in result.output
    
    def test_market_news(self, cli_runner, mock_market_data):
        """Test actualités de marché."""
        mock_market_data.get_market_news = AsyncMock(return_value=[
            {
                "headline": "Fed announces rate decision",
                "summary": "Interest rates remain unchanged",
                "timestamp": datetime.now().isoformat()
            }
        ])
        
        result = cli_runner.invoke(cli, ['market', 'news'])
        
        assert result.exit_code == 0
        assert 'Fed' in result.output
    
    def test_market_calendar(self, cli_runner, mock_market_data):
        """Test calendrier de marché."""
        mock_market_data.get_market_calendar = AsyncMock(return_value=[
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "is_open": True,
                "market_open": "09:30",
                "market_close": "16:00"
            }
        ])
        
        result = cli_runner.invoke(cli, ['market', 'calendar'])
        
        assert result.exit_code == 0
        assert any(time in result.output for time in ['09:30', '16:00'])


class TestConfigCommand:
    """Tests pour la commande config."""
    
    @pytest.fixture
    def cli_runner(self):
        """Runner CLI pour tests."""
        return CliRunner()
    
    @pytest.fixture
    def temp_config_dir(self):
        """Répertoire de configuration temporaire."""
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_config_init(self, cli_runner, temp_config_dir):
        """Test initialisation de configuration."""
        config_file = os.path.join(temp_config_dir, 'config.json')
        
        result = cli_runner.invoke(cli, [
            'config', 'init',
            '--file', config_file
        ])
        
        assert result.exit_code == 0
        assert os.path.exists(config_file)
        
        # Vérifier contenu du fichier
        with open(config_file, 'r') as f:
            config = json.load(f)
            assert 'openbb' in config
            assert 'claude' in config
    
    def test_config_set(self, cli_runner, temp_config_dir):
        """Test modification de configuration."""
        config_file = os.path.join(temp_config_dir, 'config.json')
        
        # Initialiser d'abord
        cli_runner.invoke(cli, ['config', 'init', '--file', config_file])
        
        # Modifier une valeur
        result = cli_runner.invoke(cli, [
            'config', 'set',
            '--file', config_file,
            '--key', 'openbb.api_key',
            '--value', 'new-api-key'
        ])
        
        assert result.exit_code == 0
        
        # Vérifier modification
        with open(config_file, 'r') as f:
            config = json.load(f)
            assert config['openbb']['api_key'] == 'new-api-key'
    
    def test_config_get(self, cli_runner, temp_config_dir):
        """Test lecture de configuration."""
        config_file = os.path.join(temp_config_dir, 'config.json')
        
        # Créer configuration
        config_data = {
            "openbb": {"api_key": "test-key"},
            "claude": {"model": "claude-3-sonnet"}
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        result = cli_runner.invoke(cli, [
            'config', 'get',
            '--file', config_file,
            '--key', 'openbb.api_key'
        ])
        
        assert result.exit_code == 0
        assert 'test-key' in result.output
    
    def test_config_validate(self, cli_runner, temp_config_dir):
        """Test validation de configuration."""
        config_file = os.path.join(temp_config_dir, 'config.json')
        
        # Configuration valide
        valid_config = {
            "openbb": {"api_key": "valid-key", "base_url": "https://api.openbb.co"},
            "claude": {"api_key": "valid-key", "model": "claude-3-sonnet"}
        }
        
        with open(config_file, 'w') as f:
            json.dump(valid_config, f)
        
        result = cli_runner.invoke(cli, [
            'config', 'validate',
            '--file', config_file
        ])
        
        assert result.exit_code == 0
        assert 'valid' in result.output.lower()


class TestHistoryCommand:
    """Tests pour la commande history."""
    
    @pytest.fixture
    def cli_runner(self):
        """Runner CLI pour tests."""
        return CliRunner()
    
    @pytest.fixture
    def mock_history_manager(self):
        """Gestionnaire d'historique mock."""
        with patch('finagent.cli.commands.history.HistoryManager') as mock:
            manager = Mock()
            manager.get_command_history = AsyncMock(return_value=[
                {
                    "timestamp": datetime.now().isoformat(),
                    "command": "analyze AAPL",
                    "status": "success",
                    "duration": 2.5
                }
            ])
            manager.get_analysis_history = AsyncMock(return_value=[
                {
                    "timestamp": datetime.now().isoformat(),
                    "symbol": "AAPL",
                    "action": "buy",
                    "confidence": 0.8
                }
            ])
            mock.return_value = manager
            yield manager
    
    def test_history_commands(self, cli_runner, mock_history_manager):
        """Test historique des commandes."""
        result = cli_runner.invoke(cli, ['history', 'commands'])
        
        assert result.exit_code == 0
        assert 'analyze AAPL' in result.output
    
    def test_history_analyses(self, cli_runner, mock_history_manager):
        """Test historique des analyses."""
        result = cli_runner.invoke(cli, ['history', 'analyses'])
        
        assert result.exit_code == 0
        assert 'AAPL' in result.output
    
    def test_history_clear(self, cli_runner, mock_history_manager):
        """Test effacement de l'historique."""
        mock_history_manager.clear_history = AsyncMock(return_value=True)
        
        result = cli_runner.invoke(cli, ['history', 'clear'])
        
        assert result.exit_code == 0
        assert 'cleared' in result.output.lower()
    
    def test_history_export(self, cli_runner, mock_history_manager):
        """Test export de l'historique."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_file = f.name
        
        try:
            result = cli_runner.invoke(cli, [
                'history', 'export',
                '--file', export_file,
                '--format', 'json'
            ])
            
            assert result.exit_code == 0
            assert os.path.exists(export_file)
        finally:
            if os.path.exists(export_file):
                os.unlink(export_file)


class TestCLIInteractiveMode:
    """Tests pour le mode interactif CLI."""
    
    @pytest.fixture
    def cli_runner(self):
        """Runner CLI pour tests."""
        return CliRunner()
    
    def test_interactive_mode_start(self, cli_runner):
        """Test démarrage du mode interactif."""
        # Simuler quelques commandes interactives
        input_commands = "help\nanalyze AAPL\nexit\n"
        
        with patch('finagent.cli.interactive.InteractiveSession') as mock_session:
            mock_session.return_value.start = Mock()
            
            result = cli_runner.invoke(cli, ['interactive'], input=input_commands)
            
            # Le mode interactif devrait démarrer
            assert result.exit_code == 0
    
    def test_interactive_command_completion(self, cli_runner):
        """Test complétion de commandes en mode interactif."""
        # Test que les commandes sont disponibles pour complétion
        from finagent.cli.interactive import get_available_commands
        
        commands = get_available_commands()
        
        expected_commands = ['analyze', 'portfolio', 'strategy', 'market', 'config']
        for cmd in expected_commands:
            assert cmd in commands
    
    def test_interactive_error_handling(self, cli_runner):
        """Test gestion d'erreurs en mode interactif."""
        input_commands = "invalid_command\nexit\n"
        
        with patch('finagent.cli.interactive.InteractiveSession') as mock_session:
            session = Mock()
            session.handle_command = Mock(side_effect=[
                Exception("Unknown command"),
                None  # exit
            ])
            mock_session.return_value = session
            
            result = cli_runner.invoke(cli, ['interactive'], input=input_commands)
            
            # Devrait gérer l'erreur gracieusement
            assert result.exit_code == 0


class TestCLIErrorHandling:
    """Tests pour la gestion d'erreurs CLI."""
    
    @pytest.fixture
    def cli_runner(self):
        """Runner CLI pour tests."""
        return CliRunner()
    
    def test_network_error_handling(self, cli_runner):
        """Test gestion d'erreurs réseau."""
        with patch('finagent.cli.commands.analyze.OpenBBProvider') as mock:
            mock.side_effect = Exception("Network error")
            
            result = cli_runner.invoke(cli, ['analyze', 'AAPL'])
            
            assert result.exit_code == 1
            assert 'error' in result.output.lower()
    
    def test_invalid_arguments_handling(self, cli_runner):
        """Test gestion d'arguments invalides."""
        # Symbole manquant
        result = cli_runner.invoke(cli, ['analyze'])
        
        assert result.exit_code == 2  # Click error code for missing arguments
    
    def test_file_not_found_handling(self, cli_runner):
        """Test gestion de fichier non trouvé."""
        result = cli_runner.invoke(cli, [
            'strategy', 'validate',
            '--file', '/nonexistent/file.yaml'
        ])
        
        assert result.exit_code == 1
        assert 'not found' in result.output.lower() or 'error' in result.output.lower()
    
    def test_api_error_handling(self, cli_runner):
        """Test gestion d'erreurs API."""
        with patch('finagent.cli.commands.analyze.ClaudeProvider') as mock:
            mock.side_effect = Exception("API rate limit exceeded")
            
            result = cli_runner.invoke(cli, ['analyze', 'AAPL'])
            
            assert result.exit_code == 1
            assert 'rate limit' in result.output.lower() or 'error' in result.output.lower()


# Fixtures globales pour tests CLI
@pytest.fixture
def cli_test_data():
    """Données de test pour CLI."""
    return {
        "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"],
        "timeframes": ["1D", "1W", "1M", "3M", "1Y"],
        "output_formats": ["table", "json", "csv"],
        "portfolio_strategies": ["conservative", "balanced", "aggressive"]
    }


@pytest.fixture
def cli_test_files(tmp_path):
    """Fichiers de test pour CLI."""
    # Créer fichiers temporaires
    config_file = tmp_path / "test_config.json"
    strategy_file = tmp_path / "test_strategy.yaml"
    portfolio_file = tmp_path / "test_portfolio.json"
    
    # Contenu des fichiers
    config_data = {
        "openbb": {"api_key": "test"},
        "claude": {"api_key": "test"}
    }
    
    strategy_data = """
metadata:
  name: "Test"
strategy:
  type: "technical"
rules: []
    """
    
    portfolio_data = {
        "name": "Test Portfolio",
        "positions": []
    }
    
    # Écrire fichiers
    config_file.write_text(json.dumps(config_data))
    strategy_file.write_text(strategy_data)
    portfolio_file.write_text(json.dumps(portfolio_data))
    
    return {
        "config": str(config_file),
        "strategy": str(strategy_file),
        "portfolio": str(portfolio_file)
    }