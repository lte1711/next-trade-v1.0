"""
통합 전략 테스트 설정 모듈
"""

import json
from pathlib import Path
from typing import Dict, Any

class Settings:
    """통합 설정 클래스"""
    
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[2]
        self.config_file = self.project_root / "config" / "config.json"
        self.original_config_file = self.project_root.parent / "config.json"
        
        # 기본 설정
        self.default_settings = {
            "simulation": {
                "start_date": "2025-04-02",
                "end_date": "2026-04-02",
                "total_days": 366,
                "market_phases": 4
            },
            "strategies": {
                "total_count": 29,
                "groups": 18
            },
            "data": {
                "source": "real_market_conditions",
                "symbols": [
                    "BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "SHIBUSDT",
                    "PEPEUSDT", "WIFUSDT", "BONKUSDT", "FLOKIUSDT", "1000PEPEUSDT",
                    "QUICKUSDT", "LRCUSDT", "ADAUSDT", "MATICUSDT", "AVAXUSDT", "DOTUSDT"
                ]
            },
            "reporting": {
                "standard": "FACT_ONLY",
                "format": "json"
            }
        }
        
        self._load_config()
    
    def _load_config(self) -> None:
        """설정 로드"""
        # 원본 설정 파일이 있으면 복사
        if self.original_config_file.exists() and not self.config_file.exists():
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(self.original_config_file, self.config_file)
        
        # 설정 파일 로드
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {}
        else:
            self.config = {}
        
        # 기본 설정과 병합
        self._merge_default_settings()
    
    def _merge_default_settings(self) -> None:
        """기본 설정과 병합"""
        for key, value in self.default_settings.items():
            if key not in self.config:
                self.config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정 값 가져오기"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """설정 값 설정"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self) -> None:
        """설정 저장"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def is_compatible_with_original(self) -> bool:
        """원본과 호환성 확인"""
        if not self.original_config_file.exists():
            return False
        
        try:
            with open(self.original_config_file, 'r', encoding='utf-8') as f:
                original_config = json.load(f)
            
            # 바이낸스 설정 확인
            if "binance_testnet" in original_config:
                return True
            
            return False
        except Exception:
            return False
    
    def get_original_binance_config(self) -> Dict[str, Any]:
        """원본 바이낸스 설정 가져오기"""
        if not self.original_config_file.exists():
            return {}
        
        try:
            with open(self.original_config_file, 'r', encoding='utf-8') as f:
                original_config = json.load(f)
            
            return original_config.get("binance_testnet", {})
        except Exception:
            return {}

# 전역 설정 인스턴스
settings = Settings()
