"""
Générateur de données de test pour FinAgent.

Ce module fournit des utilitaires pour générer des données de test
réalistes et cohérentes pour tous les composants de FinAgent.
"""

import random
import string
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple, Union
from uuid import uuid4, UUID

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker()
Faker.seed(42)  # Seed fixe pour reproductibilité


# ============================================================================
# GÉNÉRATEUR DE DONNÉES FINANCIÈRES
# ============================================================================

class FinancialDataGenerator:
    """Générateur de données financières réalistes."""
    
    def __init__(self, seed: int = 42):
        """Initialise le générateur avec un seed."""
        random.seed(seed)
        np.random.seed(seed)
        fake.seed_instance(seed)
        
        # Symboles d'actions réels pour tests
        self.stock_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
            'PYPL', 'ADBE', 'CRM', 'INTC', 'AMD', 'ORCL', 'IBM', 'UBER',
            'SPOT', 'ZOOM', 'SQ', 'TWTR', 'SNAP', 'PINS', 'DOCU', 'ZM'
        ]
        
        # Secteurs d'activité
        self.sectors = [
            'Technology', 'Healthcare', 'Financial Services', 'Consumer Cyclical',
            'Communication Services', 'Industrials', 'Consumer Defensive',
            'Energy', 'Utilities', 'Real Estate', 'Basic Materials'
        ]
        
        # Sources de news
        self.news_sources = [
            'Reuters', 'Bloomberg', 'Financial Times', 'Wall Street Journal',
            'MarketWatch', 'Yahoo Finance', 'CNBC', 'Seeking Alpha',
            'The Motley Fool', 'Barron\'s', 'Investopedia', 'TradingView'
        ]
    
    def generate_stock_price_series(
        self, 
        symbol: str,
        start_price: float = 100.0,
        days: int = 252,
        volatility: float = 0.2,
        trend: float = 0.05
    ) -> pd.DataFrame:
        """Génère une série temporelle de prix d'actions réaliste."""
        
        # Génère les dates
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=days),
            periods=days,
            freq='D'
        )
        
        # Modèle de marche aléatoire géométrique
        dt = 1.0 / 252.0  # Fraction d'année par jour
        mu = trend  # Dérive annuelle
        sigma = volatility  # Volatilité annuelle
        
        # Génère les rendements
        random_shocks = np.random.normal(0, 1, days)
        returns = mu * dt + sigma * np.sqrt(dt) * random_shocks
        
        # Calcule les prix
        prices = [start_price]
        for i in range(1, days):
            new_price = prices[-1] * np.exp(returns[i])
            prices.append(new_price)
        
        # Génère les volumes (corrélation inverse avec les prix)
        base_volume = random.randint(10_000_000, 50_000_000)
        volume_volatility = 0.3
        volume_shocks = np.random.normal(0, 1, days)
        volumes = []
        
        for i in range(days):
            volume_multiplier = 1 + volume_volatility * volume_shocks[i]
            # Volume plus élevé lors de mouvements de prix importants
            if i > 0:
                price_change = abs(returns[i])
                volume_multiplier *= (1 + price_change * 5)
            
            volume = int(base_volume * volume_multiplier)
            volumes.append(max(volume, 100_000))  # Volume minimum
        
        # Génère OHLC à partir des prix de clôture
        data = []
        for i, (date, close_price, volume) in enumerate(zip(dates, prices, volumes)):
            # Génère open, high, low autour du prix de clôture
            if i == 0:
                open_price = close_price
            else:
                open_price = prices[i-1]  # Open = close précédent
            
            # High et Low avec une variation réaliste
            daily_range = close_price * random.uniform(0.01, 0.05)
            high = close_price + random.uniform(0, daily_range)
            low = close_price - random.uniform(0, daily_range)
            
            # Assure la cohérence OHLC
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            data.append({
                'date': date,
                'symbol': symbol,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': volume,
                'adj_close': round(close_price, 2)  # Simplifié
            })
        
        return pd.DataFrame(data)
    
    def generate_technical_indicators(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """Génère des indicateurs techniques à partir des données de prix."""
        closes = price_data['close'].values
        highs = price_data['high'].values
        lows = price_data['low'].values
        volumes = price_data['volume'].values
        
        current_price = closes[-1]
        
        # RSI (approximation simplifiée)
        gains = []
        losses = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-change)
        
        avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else sum(gains) / len(gains)
        avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else sum(losses) / len(losses)
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # Moyennes mobiles
        sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else sum(closes) / len(closes)
        sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sum(closes) / len(closes)
        sma_200 = sum(closes[-200:]) / 200 if len(closes) >= 200 else sum(closes) / len(closes)
        
        # EMA (approximation)
        ema_12 = closes[-1]  # Simplifié
        ema_26 = closes[-1]  # Simplifié
        
        # MACD
        macd = ema_12 - ema_26
        macd_signal = macd * 0.9  # Approximation
        
        # Bollinger Bands
        std_20 = np.std(closes[-20:]) if len(closes) >= 20 else np.std(closes)
        bb_middle = sma_20
        bb_upper = bb_middle + (2 * std_20)
        bb_lower = bb_middle - (2 * std_20)
        
        # Volume moving average
        volume_sma = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes)
        
        return {
            'rsi': round(rsi, 1),
            'macd': round(macd, 3),
            'macd_signal': round(macd_signal, 3),
            'macd_histogram': round(macd - macd_signal, 3),
            'bb_upper': round(bb_upper, 2),
            'bb_middle': round(bb_middle, 2),
            'bb_lower': round(bb_lower, 2),
            'sma_20': round(sma_20, 2),
            'sma_50': round(sma_50, 2),
            'sma_200': round(sma_200, 2),
            'ema_12': round(ema_12, 2),
            'ema_26': round(ema_26, 2),
            'volume_sma': int(volume_sma),
            'price_to_sma_20': round((current_price / sma_20 - 1) * 100, 2),
            'price_to_sma_50': round((current_price / sma_50 - 1) * 100, 2)
        }
    
    def generate_company_fundamentals(self, symbol: str, market_cap_range: Tuple[int, int] = None) -> Dict[str, Any]:
        """Génère des données fondamentales d'entreprise."""
        if market_cap_range is None:
            market_cap_range = (1_000_000_000, 2_000_000_000_000)
        
        market_cap = random.randint(*market_cap_range)
        
        # Ratios financiers réalistes basés sur la capitalisation
        if market_cap > 100_000_000_000:  # Large cap
            pe_range = (15, 35)
            pb_range = (2, 8)
            roe_range = (15, 25)
        elif market_cap > 10_000_000_000:  # Mid cap
            pe_range = (12, 40)
            pb_range = (1.5, 10)
            roe_range = (10, 30)
        else:  # Small cap
            pe_range = (10, 50)
            pb_range = (1, 15)
            roe_range = (5, 35)
        
        return {
            'symbol': symbol,
            'company_name': f"{symbol} Corporation",
            'sector': random.choice(self.sectors),
            'market_cap': market_cap,
            'pe_ratio': round(random.uniform(*pe_range), 1),
            'pb_ratio': round(random.uniform(*pb_range), 1),
            'roe': round(random.uniform(*roe_range), 1),
            'debt_to_equity': round(random.uniform(0.1, 2.0), 2),
            'current_ratio': round(random.uniform(0.8, 3.0), 2),
            'dividend_yield': round(random.uniform(0, 5), 2),
            'payout_ratio': round(random.uniform(0, 80), 1),
            'revenue_growth': round(random.uniform(-10, 25), 1),
            'earnings_growth': round(random.uniform(-20, 30), 1),
            'profit_margin': round(random.uniform(2, 25), 1),
            'operating_margin': round(random.uniform(5, 30), 1),
            'employees': random.randint(1000, 500000),
            'beta': round(random.uniform(0.5, 2.0), 2)
        }
    
    def generate_news_articles(self, symbol: str, count: int = 5, days_back: int = 7) -> List[Dict[str, Any]]:
        """Génère des articles de news pour un symbole."""
        articles = []
        
        # Templates d'articles par sentiment
        positive_templates = [
            "{company} reports strong quarterly earnings",
            "{company} announces new product launch",
            "{company} beats analyst expectations",
            "{company} receives upgrade from major analyst",
            "{company} announces strategic partnership",
            "{company} shows robust revenue growth"
        ]
        
        negative_templates = [
            "{company} faces regulatory challenges",
            "{company} reports disappointing quarterly results",
            "{company} cuts annual guidance",
            "{company} receives downgrade from analyst",
            "{company} announces layoffs",
            "{company} faces supply chain disruptions"
        ]
        
        neutral_templates = [
            "{company} schedules earnings call",
            "{company} announces board changes",
            "{company} provides business update",
            "{company} participates in industry conference",
            "{company} files regulatory documents",
            "{company} announces dividend schedule"
        ]
        
        sentiments = ['positive', 'negative', 'neutral']
        templates_map = {
            'positive': positive_templates,
            'negative': negative_templates,
            'neutral': neutral_templates
        }
        
        company_name = f"{symbol} Corp"
        
        for i in range(count):
            sentiment = random.choice(sentiments)
            template = random.choice(templates_map[sentiment])
            title = template.format(company=company_name)
            
            # Génère le contenu
            content_templates = {
                'positive': "The company demonstrated strong performance with improved metrics and positive outlook for the future.",
                'negative': "Challenges in the current market environment have impacted performance and raised concerns among investors.",
                'neutral': "The company provided updates on its operations and strategic initiatives in line with market expectations."
            }
            
            content = f"{content_templates[sentiment]} {fake.text(max_nb_chars=300)}"
            
            # Date de publication
            published_at = datetime.now() - timedelta(
                days=random.randint(0, days_back),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            articles.append({
                'title': title,
                'content': content,
                'published_at': published_at.isoformat(),
                'source': random.choice(self.news_sources),
                'sentiment': sentiment,
                'relevance': round(random.uniform(0.6, 1.0), 2),
                'url': fake.url(),
                'symbol': symbol,
                'impact_score': round(random.uniform(0.1, 0.9), 2)
            })
        
        return sorted(articles, key=lambda x: x['published_at'], reverse=True)


# ============================================================================
# GÉNÉRATEUR DE DONNÉES DE PORTFOLIO
# ============================================================================

class PortfolioDataGenerator:
    """Générateur de données de portefeuille."""
    
    def __init__(self, seed: int = 42):
        """Initialise le générateur."""
        random.seed(seed)
        fake.seed_instance(seed)
    
    def generate_portfolio(
        self, 
        initial_cash: float = 100000.0,
        num_positions: int = 5,
        portfolio_name: str = None
    ) -> Dict[str, Any]:
        """Génère un portefeuille complet avec positions."""
        
        portfolio_id = uuid4()
        name = portfolio_name or f"Portfolio {fake.word().title()}"
        
        # Génère les positions
        symbols = random.sample(
            ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA'], 
            num_positions
        )
        
        positions = []
        total_invested = 0
        
        for symbol in symbols:
            quantity = random.randint(10, 200)
            avg_cost = random.uniform(50, 500)
            current_price = avg_cost * random.uniform(0.8, 1.3)
            
            position_value = quantity * avg_cost
            total_invested += position_value
            
            positions.append({
                'id': uuid4(),
                'symbol': symbol,
                'quantity': quantity,
                'average_cost': round(avg_cost, 2),
                'current_price': round(current_price, 2),
                'market_value': round(quantity * current_price, 2),
                'unrealized_pnl': round(quantity * (current_price - avg_cost), 2),
                'weight': 0,  # Sera calculé plus tard
                'opened_at': fake.date_time_between(start_date='-1y', end_date='-1m')
            })
        
        # Calcule les poids
        total_market_value = sum(pos['market_value'] for pos in positions)
        for pos in positions:
            pos['weight'] = round((pos['market_value'] / total_market_value) * 100, 2)
        
        # Cash restant
        remaining_cash = max(0, initial_cash - total_invested * 0.7)  # 70% investi
        
        return {
            'portfolio': {
                'id': portfolio_id,
                'name': name,
                'cash': round(remaining_cash, 2),
                'total_value': round(total_market_value + remaining_cash, 2),
                'total_invested': round(total_invested * 0.7, 2),
                'unrealized_pnl': round(sum(pos['unrealized_pnl'] for pos in positions), 2),
                'created_at': fake.date_time_between(start_date='-2y', end_date='-1y'),
                'updated_at': datetime.now()
            },
            'positions': positions,
            'metrics': {
                'total_return': round(random.uniform(-20, 30), 2),
                'annualized_return': round(random.uniform(-15, 25), 2),
                'volatility': round(random.uniform(10, 40), 2),
                'sharpe_ratio': round(random.uniform(-0.5, 2.0), 2),
                'max_drawdown': round(random.uniform(-30, -5), 2),
                'win_rate': round(random.uniform(40, 70), 1),
                'num_trades': random.randint(20, 200)
            }
        }
    
    def generate_transactions(self, portfolio_id: UUID, count: int = 20) -> List[Dict[str, Any]]:
        """Génère des transactions pour un portefeuille."""
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        transaction_types = ['buy', 'sell']
        
        transactions = []
        
        for i in range(count):
            symbol = random.choice(symbols)
            tx_type = random.choice(transaction_types)
            quantity = random.randint(1, 100)
            price = random.uniform(50, 500)
            
            # Frais de transaction réalistes
            fees = round(max(1.0, quantity * price * 0.001), 2)
            
            transactions.append({
                'id': uuid4(),
                'portfolio_id': portfolio_id,
                'symbol': symbol,
                'type': tx_type,
                'quantity': quantity,
                'price': round(price, 2),
                'total_amount': round(quantity * price, 2),
                'fees': fees,
                'net_amount': round(quantity * price + (fees if tx_type == 'buy' else -fees), 2),
                'executed_at': fake.date_time_between(start_date='-1y', end_date='now'),
                'order_id': fake.uuid4(),
                'status': 'executed'
            })
        
        return sorted(transactions, key=lambda x: x['executed_at'])


# ============================================================================
# GÉNÉRATEUR DE DONNÉES DE STRATÉGIES
# ============================================================================

class StrategyDataGenerator:
    """Générateur de données de stratégies de trading."""
    
    def generate_strategy_config(self, strategy_type: str = 'technical') -> Dict[str, Any]:
        """Génère une configuration de stratégie."""
        
        strategy_templates = {
            'technical': {
                'name': f'Technical {fake.word().title()} Strategy',
                'description': 'Strategy based on technical indicators',
                'rules': [
                    {
                        'name': 'RSI Oversold',
                        'conditions': [
                            {'indicator': 'rsi', 'operator': '<', 'value': 30}
                        ],
                        'action': 'buy',
                        'weight': 0.7
                    },
                    {
                        'name': 'RSI Overbought',
                        'conditions': [
                            {'indicator': 'rsi', 'operator': '>', 'value': 70}
                        ],
                        'action': 'sell',
                        'weight': 0.8
                    }
                ]
            },
            'fundamental': {
                'name': f'Fundamental {fake.word().title()} Strategy',
                'description': 'Strategy based on fundamental analysis',
                'rules': [
                    {
                        'name': 'Low PE Value',
                        'conditions': [
                            {'indicator': 'pe_ratio', 'operator': '<', 'value': 15}
                        ],
                        'action': 'buy',
                        'weight': 0.6
                    }
                ]
            }
        }
        
        base_config = strategy_templates.get(strategy_type, strategy_templates['technical'])
        
        return {
            'id': uuid4(),
            'name': base_config['name'],
            'type': strategy_type,
            'description': base_config['description'],
            'risk_tolerance': random.choice(['low', 'medium', 'high']),
            'time_horizon': random.choice(['short', 'medium', 'long']),
            'max_position_size': round(random.uniform(5, 25), 1),
            'stop_loss': round(random.uniform(5, 15), 1),
            'take_profit': round(random.uniform(10, 30), 1),
            'rules': base_config['rules'],
            'active': True,
            'created_at': fake.date_time_between(start_date='-6m', end_date='now')
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_test_dataset(size: str = 'small') -> Dict[str, Any]:
    """Génère un dataset complet pour tests."""
    
    sizes = {
        'small': {'symbols': 3, 'days': 30, 'portfolios': 1},
        'medium': {'symbols': 10, 'days': 90, 'portfolios': 3},
        'large': {'symbols': 20, 'days': 365, 'portfolios': 5}
    }
    
    config = sizes.get(size, sizes['small'])
    
    fin_gen = FinancialDataGenerator()
    port_gen = PortfolioDataGenerator()
    strat_gen = StrategyDataGenerator()
    
    symbols = random.sample(fin_gen.stock_symbols, config['symbols'])
    
    dataset = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'size': size,
            'config': config
        },
        'market_data': {},
        'portfolios': [],
        'strategies': []
    }
    
    # Génère les données de marché
    for symbol in symbols:
        price_data = fin_gen.generate_stock_price_series(symbol, days=config['days'])
        indicators = fin_gen.generate_technical_indicators(price_data)
        fundamentals = fin_gen.generate_company_fundamentals(symbol)
        news = fin_gen.generate_news_articles(symbol, count=5)
        
        dataset['market_data'][symbol] = {
            'price_data': price_data.to_dict('records'),
            'indicators': indicators,
            'fundamentals': fundamentals,
            'news': news
        }
    
    # Génère les portefeuilles
    for i in range(config['portfolios']):
        portfolio = port_gen.generate_portfolio(num_positions=len(symbols)//2)
        transactions = port_gen.generate_transactions(portfolio['portfolio']['id'])
        portfolio['transactions'] = transactions
        dataset['portfolios'].append(portfolio)
    
    # Génère les stratégies
    for strategy_type in ['technical', 'fundamental']:
        strategy = strat_gen.generate_strategy_config(strategy_type)
        dataset['strategies'].append(strategy)
    
    return dataset