#!/usr/bin/env python3
"""
기본 전략 인터페이스
모든 전략의 기본 클래스로 사용되는 추상 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from datetime import datetime


class BaseStrategy(ABC):
    """모든 전략의 기본 인터페이스"""
    
    def __init__(self, strategy_id: str, strategy_name: str):
        self.strategy_id = strategy_id
        self.strategy_name = strategy_name
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.performance_metrics = {}
    
    @abstractmethod
    def calculate_indicators(self, closes: List[float], volumes: List[float]) -> Dict[str, float]:
        """기술적 지표 계산"""
        pass
    
    @abstractmethod
    def generate_signal(self, data: Dict[str, Any]) -> str:
        """신호 생성 (LONG, SHORT, HOLD)"""
        pass
    
    @abstractmethod
    def evaluate(self, symbol: str, closes: List[float], volumes: List[float]) -> Dict[str, Any]:
        """전략 평가 및 신호 생성"""
        pass
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """전략 정보 반환"""
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "performance_metrics": self.performance_metrics
        }
    
    def update_performance(self, metrics: Dict[str, float]) -> None:
        """성과 지표 업데이트"""
        self.performance_metrics.update(metrics)
        self.last_updated = datetime.now()
    
    def validate_data(self, closes: List[float], volumes: List[float]) -> bool:
        """데이터 유효성 검증"""
        if not closes or not volumes:
            return False
        if len(closes) != len(volumes):
            return False
        if len(closes) < 20:  # 최소 20개 데이터 포인트 필요
            return False
        return True
