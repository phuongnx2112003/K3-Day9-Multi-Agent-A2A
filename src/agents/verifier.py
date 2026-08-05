"""
Verifier Agent. Owned by Member 3.
Acts as an independent quality gate before writing final case output.
"""
import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from src.contracts.messages import VerificationRequest, VerificationResult, ResolutionDraft


def round_money_dec(val: float) -> Decimal:
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class VerifierAgent:
    def __init__(self, dal=None):
        self.dal = dal

    async def verify(self, request: VerificationRequest) -> VerificationResult:
        errors: List[str] = []
        warnings: List[str] = []
        draft: ResolutionDraft = request.draft

        # 1. Case ID & basic schema checks
        if not draft.case_id or draft.case_id != request.case_id:
            errors.append(f"case_id mismatch or empty: expected {request.case_id}, got {draft.case_id}")

        # 2. Confidence range check
        if not (0.0 <= draft.confidence <= 1.0):
            errors.append(f"confidence out of bounds [0, 1]: got {draft.confidence}")

        # 3. Entity limits check
        if len(draft.order_ids) > 5:
            errors.append(f"order_ids exceeds limit of 5: count {len(draft.order_ids)}")
        if len(draft.item_ids) > 5:
            errors.append(f"item_ids exceeds limit of 5: count {len(draft.item_ids)}")
        if len(draft.seller_ids) > 5:
            errors.append(f"seller_ids exceeds limit of 5: count {len(draft.seller_ids)}")
        if len(draft.payment_ids) > 5:
            errors.append(f"payment_ids exceeds limit of 5: count {len(draft.payment_ids)}")
        if len(draft.evidence_ids) > 10:
            errors.append(f"evidence_ids exceeds limit of 10: count {len(draft.evidence_ids)}")
        if len(draft.ranked_causes) > 3:
            errors.append(f"ranked_causes exceeds limit of 3: count {len(draft.ranked_causes)}")
        if len(draft.responsible_parties) > 3:
            errors.append(f"responsible_parties exceeds limit of 3: count {len(draft.responsible_parties)}")
        if len(draft.resolution_actions) > 5:
            errors.append(f"resolution_actions exceeds limit of 5: count {len(draft.resolution_actions)}")

        # 4. Evidence ID prefix and format validation
        valid_prefixes = ("order:", "item:", "payment:", "seller:", "policy:")
        for ev_id in draft.evidence_ids:
            if not any(ev_id.startswith(p) for p in valid_prefixes):
                errors.append(f"Invalid evidence_id format: '{ev_id}'. Must start with order:, item:, payment:, seller:, or policy:")

        # Policy evidence ID check
        if draft.ranked_causes:
            expected_policy_ev = f"policy:{draft.ranked_causes[0]['cause_code']}"
            if expected_policy_ev not in draft.evidence_ids:
                warnings.append(f"Evidence list missing matching policy evidence ID '{expected_policy_ev}'")

        # 5. Financial Decimal Totals Verification
        item_total = round_money_dec(draft.item_total_brl)
        freight_total = round_money_dec(draft.freight_total_brl)
        payment_total = round_money_dec(draft.payment_total_brl)
        refund = round_money_dec(draft.recommended_refund_brl)

        facts_item_total = round_money_dec(request.order_seller_facts.item_total_brl)
        facts_freight_total = round_money_dec(request.order_seller_facts.freight_total_brl)
        facts_payment_total = round_money_dec(request.payment_facts.payment_total_brl)

        if item_total != facts_item_total:
            errors.append(f"item_total_brl mismatch: draft={item_total}, facts={facts_item_total}")
        if freight_total != facts_freight_total:
            errors.append(f"freight_total_brl mismatch: draft={freight_total}, facts={facts_freight_total}")
        if payment_total != facts_payment_total:
            errors.append(f"payment_total_brl mismatch: draft={payment_total}, facts={facts_payment_total}")

        # 6. Status & Refund Consistency Checks
        if refund > Decimal("0.00") and draft.case_status != "action_required":
            errors.append(f"case_status must be 'action_required' when refund > 0 (refund={refund})")
        if refund == Decimal("0.00") and draft.case_status != "no_action":
            errors.append(f"case_status must be 'no_action' when refund == 0 (refund={refund})")

        # Expected refund verification based on primary issue
        primary_issue = draft.primary_issue
        if primary_issue in ("canceled_order_paid", "unavailable_order_paid"):
            if refund != payment_total:
                errors.append(f"Primary issue '{primary_issue}' requires refund equal to payment_total ({payment_total}), got {refund}")
        elif primary_issue in ("late_delivery_seller", "late_delivery_logistics"):
            if refund != freight_total:
                errors.append(f"Primary issue '{primary_issue}' requires refund equal to freight_total ({freight_total}), got {refund}")
        elif primary_issue in ("valid_split_payment", "unsupported_late_claim"):
            if refund != Decimal("0.00"):
                errors.append(f"Primary issue '{primary_issue}' requires refund equal to 0.00, got {refund}")

        # 7. Real Data Record Existence Check (if DAL is initialized)
        if self.dal and request.order_seller_facts.order_id:
            order_id = request.order_seller_facts.order_id
            order_rec = self.dal.get_order(order_id)
            if not order_rec and order_id:
                warnings.append(f"Order ID '{order_id}' not found in DAL CSV index")

        valid = len(errors) == 0
        return VerificationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            verified_at=datetime.now(timezone.utc).isoformat()
        )
