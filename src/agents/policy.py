"""
Policy Agent. Owned by Member 2.
"""
from src.contracts.messages import PolicyRequest, ResolutionDraft


class PolicyAgent:
    async def process(self, request: PolicyRequest) -> ResolutionDraft:
        return ResolutionDraft(
            case_id=request.case_id,
            primary_issue="unsupported_late_claim",
            case_status="no_action",
            confidence=1.0,
            order_ids=[request.order_id],
            item_ids=[],
            seller_ids=[],
            payment_ids=[],
            ranked_causes=[{"cause_code": "DELIVERY_WITHIN_ESTIMATE", "rank": 1}],
            responsible_parties=[],
            evidence_ids=[f"order:{request.order_id}", "policy:DELIVERY_WITHIN_ESTIMATE"],
            currency="BRL",
            item_total_brl=0.0,
            freight_total_brl=0.0,
            payment_total_brl=0.0,
            recommended_refund_brl=0.0,
            resolution_actions=["reject_late_refund"]
        )
