"""
데이터 검증 모듈
"""

from typing import Any, Dict, List

def validate_market_data(data: Dict[str, Any]) -> bool:
    """시장 데이터 검증"""
    required_keys = ["date", "market_phase", "symbols", "market_conditions"]
    
    if not validate_dict_structure(data, required_keys):
        return False
    
    # 심볼 데이터 확인
    symbols = data.get("symbols", {})
    if not symbols:
        return False
    
    # 각 심볼의 필수 키 확인
    for symbol_data in symbols.values():
        symbol_required_keys = ["price", "change", "volatility"]
        if not validate_dict_structure(symbol_data, symbol_required_keys):
            return False
    
    return True

def validate_strategy_config(config: Dict[str, Any]) -> bool:
    """전략 설정 검증"""
    required_keys = ["symbol", "type", "initial_capital", "stop_loss", "leverage", "target_return", "profit_target"]
    
    return validate_dict_structure(config, required_keys)

def validate_simulation_results(results: List[Dict[str, Any]]) -> bool:
    """시뮬레이션 결과 검증"""
    if not results:
        return False
    
    for day_result in results:
        required_keys = ["date", "strategies", "total_pnl", "total_capital"]
        if not validate_dict_structure(day_result, required_keys):
            return False
        
        # 전략 데이터 확인
        strategies = day_result.get("strategies", {})
        if not strategies:
            continue
        
        for strategy_data in strategies.values():
            strategy_required_keys = ["daily_pnl", "cumulative_pnl", "return_rate"]
            if not validate_dict_structure(strategy_data, strategy_required_keys):
                return False
    
    return True

def validate_analysis_results(results: Dict[str, Any]) -> bool:
    """분석 결과 검증"""
    required_keys = [
        "total_performance",
        "strategy_summary", 
        "group_performance",
        "risk_reward_analysis",
        "investment_analysis"
    ]
    
    return validate_dict_structure(results, required_keys)

def validate_dict_structure(data: Dict[str, Any], required_keys: List[str]) -> bool:
    """딕셔너리 구조 검증"""
    return all(key in data for key in required_keys)

def validate_numeric_values(data: Dict[str, Any], numeric_keys: List[str]) -> bool:
    """숫자 값 검증"""
    for key in numeric_keys:
        if key in data and not isinstance(data[key], (int, float)):
            return False
    return True

def validate_date_format(date_string: str) -> bool:
    """날짜 형식 검증"""
    try:
        from datetime import datetime
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_leverage(leverage: float) -> bool:
    """레버리지 검증"""
    return isinstance(leverage, (int, float)) and 1.0 <= leverage <= 50.0

def validate_return_rate(return_rate: float) -> bool:
    """수익률 검증"""
    return isinstance(return_rate, (int, float)) and -100.0 <= return_rate <= 1000.0
