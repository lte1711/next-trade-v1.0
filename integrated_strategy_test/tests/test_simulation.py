"""
시뮬레이션 테스트
"""

import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.data.market_data import RealMarketDataLoader
from src.simulation.engine import SimulationEngine
from src.strategies.strategy_manager import StrategyManager
from src.analysis.performance import PerformanceAnalyzer

class TestSimulation:
    """시뮬레이션 테스트 클래스"""
    
    def test_market_data_loader(self):
        """시장 데이터 로더 테스트"""
        
        loader = RealMarketDataLoader()
        
        # 기본 속성 확인
        assert loader.symbols is not None
        assert len(loader.symbols) > 0
        assert loader.initial_prices is not None
        assert loader.market_phases is not None
        
        # 데이터 로드
        data = loader.load_real_market_data()
        
        # 데이터 구조 확인
        assert len(data) > 0
        assert all("date" in day for day in data)
        assert all("symbols" in day for day in data)
        assert all("market_phase" in day for day in data)
        
        # 데이터 유효성 확인
        assert loader.validate_data(data) == True
    
    def test_simulation_engine(self):
        """시뮬레이션 엔진 테스트"""
        
        # 테스트 데이터 생성
        loader = RealMarketDataLoader()
        historical_data = loader.load_real_market_data()
        
        # 전략 관리자
        strategy_manager = StrategyManager()
        strategies = strategy_manager.load_all_strategies()
        
        # 시뮬레이션 엔진
        engine = SimulationEngine()
        
        # 시뮬레이션 실행
        results = engine.run_simulation(historical_data, strategies)
        
        # 결과 확인
        assert "simulation_results" in results
        assert "total_pnl_history" in results
        assert len(results["simulation_results"]) > 0
        assert len(results["total_pnl_history"]) > 0
        
        # 시뮬레이션 요약
        summary = engine.get_simulation_summary()
        assert "total_days" in summary
        assert "final_pnl" in summary
        assert "volatility" in summary
    
    def test_performance_analyzer(self):
        """성과 분석기 테스트"""
        
        # 테스트 시뮬레이션 데이터 생성
        loader = RealMarketDataLoader()
        historical_data = loader.load_real_market_data()
        
        strategy_manager = StrategyManager()
        strategies = strategy_manager.load_all_strategies()
        
        engine = SimulationEngine()
        simulation_data = engine.run_simulation(historical_data, strategies)
        
        # 성과 분석
        analyzer = PerformanceAnalyzer()
        analysis_results = analyzer.analyze(simulation_data)
        
        # 분석 결과 확인
        required_keys = [
            "total_performance",
            "strategy_summary",
            "group_performance",
            "risk_reward_analysis",
            "investment_analysis"
        ]
        
        for key in required_keys:
            assert key in analysis_results
        
        # 최고 성과 전략
        top_performers = analyzer.get_top_performers()
        assert isinstance(top_performers, list)
        assert len(top_performers) <= 5
        
        # 최저 성과 전략
        worst_performers = analyzer.get_worst_performers()
        assert isinstance(worst_performers, list)
        assert len(worst_performers) <= 5
    
    def test_integration_flow(self):
        """통합 플로우 테스트"""
        
        try:
            # 1. 데이터 로드
            loader = RealMarketDataLoader()
            historical_data = loader.load_real_market_data()
            assert len(historical_data) > 0
            
            # 2. 전략 로드
            strategy_manager = StrategyManager()
            strategies = strategy_manager.load_all_strategies()
            assert len(strategies) > 0
            
            # 3. 시뮬레이션 실행
            engine = SimulationEngine()
            simulation_data = engine.run_simulation(historical_data, strategies)
            assert len(simulation_data["simulation_results"]) > 0
            
            # 4. 성과 분석
            analyzer = PerformanceAnalyzer()
            analysis_results = analyzer.analyze(simulation_data)
            assert "total_performance" in analysis_results
            
            # 5. 보고서 생성
            from src.analysis.reporter import FactReporter
            reporter = FactReporter()
            report = reporter.generate_report(analysis_results)
            assert "comprehensive_performance" in report
            
            print("FACT: 통합 플로우 테스트 성공")
            
        except Exception as e:
            pytest.fail(f"Integration flow failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__])
