"""
Deterministic Policy Rules implementation for EC_POLICY_V1. Owned by Member 2.
"""
from decimal import Decimal, ROUND_HALF_UP


def round_money(amount: float) -> float:
    """Decimal rounding to 2 decimal places."""
    return float(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
