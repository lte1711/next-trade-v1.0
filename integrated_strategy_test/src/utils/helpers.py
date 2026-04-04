"""
헬퍼 함수 모듈
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

def format_number(value: float, decimals: int = 2) -> str:
    """숫자 포맷팅"""
    return f"{value:,.{decimals}f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """퍼센트 포맷팅"""
    return f"{value:.{decimals}f}%"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """안전한 나눗셈"""
    if denominator == 0:
        return default
    return numerator / denominator

def validate_dict_structure(data: Dict[str, Any], required_keys: List[str]) -> bool:
    """딕셔너리 구조 검증"""
    return all(key in data for key in required_keys)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """JSON 파일 로드"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_json_file(file_path: Path, data: Dict[str, Any]) -> bool:
    """JSON 파일 저장"""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def get_timestamp() -> str:
    """타임스탬프 생성"""
    return datetime.now().isoformat()

def calculate_returns(initial: float, final: float) -> float:
    """수익률 계산"""
    if initial == 0:
        return 0.0
    return ((final - initial) / initial) * 100

def calculate_volatility(returns: List[float]) -> float:
    """변동성 계산"""
    if not returns:
        return 0.0
    return sum(abs(r) for r in returns) / len(returns) * 100

def rank_by_performance(data: Dict[str, Dict[str, Any]], metric: str = "total_pnl") -> List[tuple]:
    """성과별 순위 매김"""
    return sorted(data.items(), key=lambda x: x[1].get(metric, 0), reverse=True)

def filter_by_threshold(data: Dict[str, Dict[str, Any]], metric: str, threshold: float) -> Dict[str, Dict[str, Any]]:
    """임계값으로 필터링"""
    return {
        key: value for key, value in data.items()
        if value.get(metric, 0) >= threshold
    }
