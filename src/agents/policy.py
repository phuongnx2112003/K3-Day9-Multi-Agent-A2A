"""
Policy Agent. Owned by Member 2 (Minh Đức).
Evaluates PolicyRequest against EC_POLICY_V1 policy rules and formats ResolutionDraft.
"""
import asyncio
from typing import Any, Callable, Dict, List, Optional

from src.contracts.messages import PolicyRequest, ResolutionDraft
from src.policy_prompt import PolicyClassification, classify_policy_with_llm
from src.policy_rules import evaluate_policy, round_money


class PolicyAgent:
    def __init__(
        self,
        use_llm: bool = False,
        llm_classifier: Optional[Callable[[PolicyRequest], PolicyClassification]] = None,
    ):
        self.use_llm = use_llm
        self.llm_classifier = llm_classifier or classify_policy_with_llm
        self.last_decision_source = "deterministic"
        self.last_llm_error: Optional[str] = None

    async def process(self, request: PolicyRequest) -> ResolutionDraft:
        order_id = request.order_id
        order_seller = request.order_seller_facts
        payment = request.payment_facts
        delivery = request.delivery_facts

        # Deterministic policy remains the source of truth and validates LLM output.
        decision = evaluate_policy(order_seller, payment, delivery)
        self.last_decision_source = "deterministic"
        self.last_llm_error = None
        if self.use_llm:
            try:
                classification = await asyncio.to_thread(self.llm_classifier, request)
                mismatch = _classification_mismatch(classification, decision)
                if mismatch:
                    self.last_decision_source = "deterministic_fallback"
                    self.last_llm_error = mismatch
                else:
                    self.last_decision_source = "llm_verified"
                    decision = _merge_verified_classification(decision, classification)
            except Exception as exc:
                self.last_decision_source = "deterministic_fallback"
                self.last_llm_error = f"{type(exc).__name__}: {exc}"

        # 2. Extract affected entity IDs (capped at max 5 each)
        order_ids = [order_id]

        item_ids: List[str] = []
        for item in order_seller.items:
            item_seq = item.get("order_item_id")
            if item_seq is not None:
                item_ids.append(f"{order_id}:{item_seq}")
        item_ids = item_ids[:5]

        seller_ids_set = []
        for s in order_seller.sellers:
            sid = s.get("seller_id")
            if sid and sid not in seller_ids_set:
                seller_ids_set.append(sid)
        if not seller_ids_set:
            for item in order_seller.items:
                sid = item.get("seller_id")
                if sid and sid not in seller_ids_set:
                    seller_ids_set.append(sid)
        seller_ids = seller_ids_set[:5]

        payment_ids: List[str] = []
        for p in payment.payment_rows:
            p_seq = p.get("payment_sequential")
            if p_seq is not None:
                payment_ids.append(f"{order_id}:{p_seq}")
        payment_ids = payment_ids[:5]

        # 3. Construct evidence IDs (capped at max 10)
        evidence_ids: List[str] = []
        
        # Order evidence
        evidence_ids.append(f"order:{order_id}")
        
        # Item evidence
        for i_id in item_ids:
            evidence_ids.append(f"item:{i_id}")
            
        # Payment evidence
        for p_id in payment_ids:
            evidence_ids.append(f"payment:{p_id}")
            
        # Seller evidence
        for s_id in seller_ids:
            evidence_ids.append(f"seller:{s_id}")

        # Policy evidence
        root_cause = decision["root_cause_code"]
        evidence_ids.append(f"policy:{root_cause}")

        # Deduplicate while preserving order
        unique_evidences: List[str] = []
        for ev in evidence_ids:
            if ev not in unique_evidences:
                unique_evidences.append(ev)
        evidence_ids = unique_evidences[:10]

        # 4. Construct ResolutionDraft
        item_total_brl = round_money(order_seller.item_total_brl)
        freight_total_brl = round_money(order_seller.freight_total_brl)
        payment_total_brl = round_money(payment.payment_total_brl)
        recommended_refund_brl = round_money(decision["recommended_refund_brl"])

        return ResolutionDraft(
            case_id=request.case_id,
            primary_issue=decision["primary_issue"],
            case_status=decision["case_status"],
            confidence=float(decision["confidence"]),
            order_ids=order_ids,
            item_ids=item_ids,
            seller_ids=seller_ids,
            payment_ids=payment_ids,
            ranked_causes=[{"cause_code": root_cause, "rank": 1}],
            responsible_parties=decision["responsible_parties"][:3],
            evidence_ids=evidence_ids,
            currency="BRL",
            item_total_brl=item_total_brl,
            freight_total_brl=freight_total_brl,
            payment_total_brl=payment_total_brl,
            recommended_refund_brl=recommended_refund_brl,
            resolution_actions=decision["resolution_actions"][:5]
        )


def _classification_mismatch(
    classification: PolicyClassification, expected: Dict[str, Any]
) -> Optional[str]:
    parties = expected["responsible_parties"]
    expected_party_type = parties[0]["party_type"] if parties else None
    expected_party_id = parties[0]["party_id"] if parties else None
    checks = {
        "primary_issue": (classification.primary_issue, expected["primary_issue"]),
        "root_cause_code": (
            classification.root_cause_code,
            expected["root_cause_code"],
        ),
        "case_status": (classification.case_status, expected["case_status"]),
        "responsible_party_type": (
            classification.responsible_party_type,
            expected_party_type,
        ),
        "responsible_party_id": (
            classification.responsible_party_id,
            expected_party_id,
        ),
        "resolution_action": (
            classification.resolution_action,
            expected["resolution_actions"][0],
        ),
    }
    mismatches = [
        f"{name}: got {actual!r}, expected {wanted!r}"
        for name, (actual, wanted) in checks.items()
        if actual != wanted
    ]
    return "; ".join(mismatches) if mismatches else None


def _merge_verified_classification(
    decision: Dict[str, Any], classification: PolicyClassification
) -> Dict[str, Any]:
    """Use LLM categorical fields only after they match deterministic policy."""
    merged = dict(decision)
    merged.update(
        primary_issue=classification.primary_issue,
        root_cause_code=classification.root_cause_code,
        case_status=classification.case_status,
        resolution_actions=[classification.resolution_action],
    )
    return merged
