"""
Payment Agent. Owned by Member 2 (Minh Đức).
Extracts payment rows, calculates total payment using Decimal arithmetic,
and generates payment candidate evidence IDs.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List

from src.contracts.messages import InvestigationRequest, PaymentFacts
from src.evidence import make_payment_evidence


def round_money(amount: float) -> float:
    """Utility function to round monetary float to 2 decimal places using Decimal."""
    return float(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class PaymentAgent:
    def __init__(self, dal=None):
        self.dal = dal

    async def process(self, request: InvestigationRequest) -> PaymentFacts:
        order_id = request.order_id
        if self.dal is None:
            raise RuntimeError("PaymentAgent requires a DataAccessLayer")
        payment_rows: List[Dict[str, Any]] = self.dal.get_payments(order_id)

        # Calculate total payment value using Decimal arithmetic
        # Note: Do NOT multiply payment_value by payment_installments
        total_dec = Decimal("0.00")
        evidence_candidates: List[str] = []

        for row in payment_rows:
            value = row.get("payment_value")
            try:
                p_val = Decimal(str(value))
            except (InvalidOperation, TypeError) as exc:
                raise ValueError(f"Invalid payment_value: {value!r}") from exc
            total_dec += p_val
            seq = row.get("payment_sequential")
            if seq is not None:
                evidence_candidates.append(make_payment_evidence(order_id, int(seq)))

        payment_total_brl = float(total_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        payment_count = len(payment_rows)

        return PaymentFacts(
            order_id=order_id,
            payment_rows=payment_rows,
            payment_total_brl=payment_total_brl,
            payment_count=payment_count,
            # Coordinator sets this after OrderSellerFacts is available.
            reconciled=False,
            evidence_candidates=evidence_candidates,
        )

    @staticmethod
    def reconcile(
        facts: PaymentFacts, item_total_brl: float, freight_total_brl: float
    ) -> PaymentFacts:
        """Set reconciliation after Coordinator receives OrderSellerFacts."""
        from src.policy_rules import is_payment_reconciled

        return facts.model_copy(
            update={
                "reconciled": is_payment_reconciled(
                    facts.payment_total_brl,
                    item_total_brl,
                    freight_total_brl,
                )
            }
        )
