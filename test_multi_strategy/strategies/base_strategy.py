#!/usr/bin/env python3
"""
기본 전략 클래스 (테스트 버전)
모든 전략의 기반이 되는 추상 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime, timezone


class BaseStrategy(ABC):
    """기본 전략 추상 클래스"""
    
    def __init__(self):
        self.name = ""
        self.description = ""
        self.params = {}
        self.performance_metrics = {}
    
    @abstractmethod
    def calculate_indicators(self, closes: List[float], highs: List[float], lows: List[float]) -> Dict[str, float]:
        """기술적 지표 계산"""
        pass
    
    @abstractmethod
    def generate_signal(self, symbol: str, closes: List[float], highs: List[float], lows: List[float], volumes: List[float]) -> Dict[str, Any]:
        """매매 신호 생성"""
        pass
    
    @abstractmethod
    def evaluate(self, symbol: str, closes: List[float], volumes: List[float]) -> Dict[str, Any]:
        """전략 평가"""
        pass
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """전략 정보 반환"""
        return {
            "name": self.name,
            "description": self.description,
            "params": self.params,
            "performance_metrics": self.performance_metrics
        }
    
    def update_performance(self, metrics: Dict[str, float]):
        """성과 지표 업데이트"""
        self.performance_metrics.update(metrics)
    
    def validate_data(self, closes: List[float], volumes: List[float]) -> bool:
        """데이터 유효성 검증"""
        if not closes or not volumes:
            return False
        
        if len(closes) != len(volumes):
            return False
        
        if len(closes) < 10:  # 최소 10개 데이터 필요
            return False
        
        return True
