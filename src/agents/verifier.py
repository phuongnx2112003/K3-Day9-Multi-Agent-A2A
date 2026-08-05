"""
Verifier Agent. Owned by Member 3.
Acts as an independent quality gate before writing final case output.
"""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from src.contracts.messages import VerificationRequest, VerificationResult, ResolutionDraft
from src.policy_rules import evaluate_policy


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

        # Evidence and entity grounding validation against investigation facts.
        fact_order_id = request.order_seller_facts.order_id if request.order_seller_facts else None
        fact_items = []
        fact_sellers = []
        if request.order_seller_facts:
            for item in request.order_seller_facts.items:
                item_id = item.get("order_item_id", item.get("item_id"))
                if item_id is not None:
                    fact_items.append(f"{fact_order_id}:{item_id}")
                seller_id = item.get("seller_id")
                if seller_id is not None and str(seller_id) not in fact_sellers:
                    fact_sellers.append(str(seller_id))
            for seller in request.order_seller_facts.sellers:
                seller_id = seller.get("seller_id") if isinstance(seller, dict) else seller
                if seller_id is not None and str(seller_id) not in fact_sellers:
                    fact_sellers.append(str(seller_id))

        fact_payments = []
        for payment in request.payment_facts.payment_rows:
            sequence = payment.get("payment_sequential")
            if sequence is not None:
                fact_payments.append(f"{fact_order_id}:{sequence}")

        expected_entities = {
            "order_ids": [fact_order_id] if fact_order_id else [],
            "item_ids": fact_items[:5],
            "seller_ids": fact_sellers[:5],
            "payment_ids": fact_payments[:5],
        }
        for field_name, expected in expected_entities.items():
            actual = getattr(draft, field_name)
            if actual != expected:
                errors.append(
                    f"{field_name} does not match grounded facts: "
                    f"expected {expected}, got {actual}"
                )

        grounded_evidence = set(request.order_seller_facts.evidence_candidates)
        grounded_evidence.update(request.payment_facts.evidence_candidates)
        grounded_evidence.update(request.delivery_facts.evidence_candidates)

        for ev_id in draft.evidence_ids:
            if not ev_id.startswith("policy:") and ev_id not in grounded_evidence:
                errors.append(f"Evidence ID is not grounded in investigation facts: '{ev_id}'")

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
        if draft.currency != "BRL":
            errors.append(f"currency must be 'BRL', got '{draft.currency}'")
        if min(item_total, freight_total, payment_total, refund) < Decimal("0.00"):
            errors.append("financial values must not be negative")

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

        # Recompute the deterministic policy decision independently from the draft.
        try:
            expected_decision = evaluate_policy(
                request.order_seller_facts,
                request.payment_facts,
                request.delivery_facts,
            )
        except ValueError as exc:
            errors.append(f"Unable to verify policy decision: {exc}")
        else:
            expected_cause = expected_decision["root_cause_code"]
            expected_causes = [{"cause_code": expected_cause, "rank": 1}]
            policy_evidence = f"policy:{expected_cause}"
            decision_checks = {
                "primary_issue": expected_decision["primary_issue"],
                "case_status": expected_decision["case_status"],
                "ranked_causes": expected_causes,
                "responsible_parties": expected_decision["responsible_parties"][:3],
                "resolution_actions": expected_decision["resolution_actions"][:5],
            }
            for field_name, expected in decision_checks.items():
                actual = getattr(draft, field_name)
                if actual != expected:
                    errors.append(
                        f"{field_name} does not match EC_POLICY_V1: "
                        f"expected {expected}, got {actual}"
                    )
            if round_money_dec(draft.confidence) != round_money_dec(
                expected_decision["confidence"]
            ):
                errors.append(
                    "confidence does not match EC_POLICY_V1: "
                    f"expected {expected_decision['confidence']}, got {draft.confidence}"
                )
            if policy_evidence not in draft.evidence_ids:
                errors.append(f"Missing required policy evidence ID: '{policy_evidence}'")
            for ev_id in draft.evidence_ids:
                if ev_id.startswith("policy:") and ev_id != policy_evidence:
                    errors.append(f"Incorrect policy evidence ID: '{ev_id}'")

        # 7. Real Data Record Existence Check (if DAL is initialized)
        if self.dal and request.order_seller_facts.order_id:
            order_id = request.order_seller_facts.order_id
            order_rec = self.dal.get_order(order_id)
            if not order_rec and order_id:
                errors.append(f"Order ID '{order_id}' not found in DAL CSV index")

        valid = len(errors) == 0
        return VerificationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            verified_at=datetime.now(timezone.utc).isoformat()
        )
