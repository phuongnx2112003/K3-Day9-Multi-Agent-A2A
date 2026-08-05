"""
Payment Agent. Owned by Member 2 (Minh Đức).
Extracts payment rows, calculates total payment using Decimal arithmetic,
and generates payment candidate evidence IDs.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from src.contracts.messages import InvestigationRequest, PaymentFacts


def round_money(amount: float) -> float:
    """Utility function to round monetary float to 2 decimal places using Decimal."""
    return float(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class PaymentAgent:
    def __init__(self, dal=None):
        self.dal = dal

    async def process(self, request: InvestigationRequest) -> PaymentFacts:
        order_id = request.order_id
        payment_rows: List[Dict[str, Any]] = []

        if self.dal is not None:
            payment_rows = self.dal.get_payments(order_id)

        # Calculate total payment value using Decimal arithmetic
        # Note: Do NOT multiply payment_value by payment_installments
        total_dec = Decimal("0.00")
        evidence_candidates: List[str] = []

        for row in payment_rows:
            p_val = Decimal(str(row.get("payment_value", 0.0)))
            total_dec += p_val
            seq = row.get("payment_sequential")
            if seq is not None:
                evidence_candidates.append(f"payment:{order_id}:{seq}")

        payment_total_brl = float(total_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        payment_count = len(payment_rows)

        return PaymentFacts(
            order_id=order_id,
            payment_rows=payment_rows,
            payment_total_brl=payment_total_brl,
            payment_count=payment_count,
            reconciled=False,  # Reconciled status will be evaluated when comparing with order total in Policy
            evidence_candidates=evidence_candidates
        )
