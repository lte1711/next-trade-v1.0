"""
Numeric Utils - Numeric Utility Functions Module
"""

from decimal import Decimal, ROUND_DOWN, ROUND_UP


def safe_float_conversion(value, default=0.0):
    """Safe float conversion"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def round_to_step(value, step_size, rounding_mode=ROUND_DOWN):
    """Round to step size"""
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
