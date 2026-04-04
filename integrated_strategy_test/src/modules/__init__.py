"""
모듈화된 테스트 프로그램 - 모듈 초기화 파일
"""

from .market_analyzer import MarketAnalyzer
from .portfolio_manager import PortfolioManager
from .realtime_data import RealTimeDataFetcher
from .simulator import ModularTradingSimulator

__all__ = [
    'MarketAnalyzer',
    'PortfolioManager', 
    'RealTimeDataFetcher',
    'ModularTradingSimulator'
]

__version__ = "1.1.0"
__author__ = "NEXT-TRADE Team"
__description__ = "모듈화된 트레이딩 시뮬레이터"
