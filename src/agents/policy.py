"""
Policy Agent. Owned by Member 2 (Minh Đức).
Evaluates PolicyRequest against EC_POLICY_V1 policy rules and formats ResolutionDraft.
"""
from typing import List, Dict, Any
from src.contracts.messages import PolicyRequest, ResolutionDraft
from src.policy_rules import evaluate_policy, round_money


class PolicyAgent:
    async def process(self, request: PolicyRequest) -> ResolutionDraft:
        order_id = request.order_id
        order_seller = request.order_seller_facts
        payment = request.payment_facts
        delivery = request.delivery_facts

        # 1. Evaluate policy rules
        decision = evaluate_policy(order_seller, payment, delivery)

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
