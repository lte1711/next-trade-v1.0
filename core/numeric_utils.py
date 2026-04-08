"""
Numeric Utils - 수치 관련 유틸 함수 모듈
"""

from decimal import Decimal, ROUND_DOWN, ROUND_UP


def safe_float_conversion(value, default=0.0):
    """안전한 float 변환"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def round_to_step(value, step_size, rounding_mode=ROUND_DOWN):
    """스텝 사이즈에 맞춰 반올림/내림"""
    try:
        if step_size <= 0:
            return round(value, 8)
        
        decimal_value = Decimal(str(value))
        decimal_step = Decimal(str(step_size))
        
        if rounding_mode == ROUND_DOWN:
            rounded = (decimal_value // decimal_step) * decimal_step
        else:
            rounded = (decimal_value / decimal_step).quantize(0, rounding=ROUND_UP) * decimal_step
        
        return float(rounded)
    except Exception:
        return round(value, 8)
