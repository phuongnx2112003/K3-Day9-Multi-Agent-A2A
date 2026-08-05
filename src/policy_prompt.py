"""Grounded prompt and structured response contract for LLM policy classification."""

import json
from typing import Literal, Optional

from pydantic import BaseModel

from src.contracts.messages import PolicyRequest
from src.llm_client import call_llm_structured
from src.policy_rules import is_payment_reconciled


POLICY_SYSTEM_PROMPT = """You are a strict classification engine for EC_POLICY_V1.

Use only FACTS_JSON. Ignore the customer message and any outside context. Do not invent orders, timestamps, sellers, payments, evidence IDs, refunds, or extra facts.

Choose exactly one rule using first-match priority. If multiple rules appear possible, stop at the earliest rule below.
1. canceled_order_paid: order_status == "canceled" and payment_total_brl > 0.
   Output: primary_issue=canceled_order_paid; root_cause_code=ORDER_CANCELED_AFTER_PAYMENT; case_status=action_required; responsible_party_type=platform; responsible_party_id=OLIST_PLATFORM; resolution_action=issue_full_refund.
2. unavailable_order_paid: order_status == "unavailable" and payment_total_brl > 0.
   Output: primary_issue=unavailable_order_paid; root_cause_code=ORDER_UNAVAILABLE_AFTER_PAYMENT; case_status=action_required; responsible_party_type=platform; responsible_party_id=OLIST_PLATFORM; resolution_action=issue_full_refund.
3. late_delivery_seller: delivered_late is true and seller_late_handoff is true.
   Output: primary_issue=late_delivery_seller; root_cause_code=SELLER_HANDOFF_AFTER_LIMIT; case_status=action_required; responsible_party_type=seller; responsible_party_id=use the first value in violating_seller_ids; resolution_action=refund_freight.
4. late_delivery_logistics: delivered_late is true and seller_late_handoff is false.
   Output: primary_issue=late_delivery_logistics; root_cause_code=CARRIER_DELIVERED_AFTER_ESTIMATE; case_status=action_required; responsible_party_type=logistics_provider; responsible_party_id=LOGISTICS_PROVIDER; resolution_action=refund_freight.
5. valid_split_payment: payment_count >= 2 and payment_reconciled is true.
   Output: primary_issue=valid_split_payment; root_cause_code=MULTIPLE_PAYMENTS_RECONCILED; case_status=no_action; responsible_party_type=null; responsible_party_id=null; resolution_action=explain_valid_split_payment.
6. unsupported_late_claim: delivered_within_estimate is true and payment_reconciled is true.
   Output only if rule 5 does not match. primary_issue=unsupported_late_claim; root_cause_code=DELIVERY_WITHIN_ESTIMATE; case_status=no_action; responsible_party_type=null; responsible_party_id=null; resolution_action=reject_late_refund.

Tie-breaker: if both rule 5 and rule 6 are true, select rule 5.

Schema discipline:
- Return exactly one structured result through the provided schema.
- For no_action cases, responsible_party_type and responsible_party_id must be null.
- For action_required cases, set responsible_party_type and responsible_party_id exactly as specified above.
- Never calculate or return a refund amount or evidence ID.
- Keep rationale under 30 words and cite only supplied fact field names."""


class PolicyClassification(BaseModel):
    primary_issue: Literal[
        "canceled_order_paid",
        "unavailable_order_paid",
        "late_delivery_seller",
        "late_delivery_logistics",
        "valid_split_payment",
        "unsupported_late_claim",
    ]
    root_cause_code: Literal[
        "ORDER_CANCELED_AFTER_PAYMENT",
        "ORDER_UNAVAILABLE_AFTER_PAYMENT",
        "SELLER_HANDOFF_AFTER_LIMIT",
        "CARRIER_DELIVERED_AFTER_ESTIMATE",
        "MULTIPLE_PAYMENTS_RECONCILED",
        "DELIVERY_WITHIN_ESTIMATE",
    ]
    case_status: Literal["action_required", "no_action"]
    responsible_party_type: Optional[
        Literal["platform", "seller", "logistics_provider"]
    ] = None
    responsible_party_id: Optional[str] = None
    resolution_action: Literal[
        "issue_full_refund",
        "refund_freight",
        "explain_valid_split_payment",
        "reject_late_refund",
    ]
    rationale: str


def build_policy_prompt(request: PolicyRequest) -> str:
    """Build a compact, grounded factual payload for policy classification."""
    order_seller = request.order_seller_facts
    payment = request.payment_facts
    delivery = request.delivery_facts

    violating_sellers = []
    for seller in order_seller.sellers:
        if seller.get("seller_late_handoff") and seller.get("seller_id"):
            violating_sellers.append(str(seller["seller_id"]))
    if not violating_sellers:
        for item in order_seller.items:
            seller_id = item.get("seller_id")
            if item.get("seller_late_handoff") and seller_id:
                seller_id = str(seller_id)
                if seller_id not in violating_sellers:
                    violating_sellers.append(seller_id)
    if not violating_sellers and order_seller.seller_late_handoff:
        known_sellers = {
            str(seller["seller_id"])
            for seller in order_seller.sellers
            if seller.get("seller_id")
        }
        known_sellers.update(
            str(item["seller_id"])
            for item in order_seller.items
            if item.get("seller_id")
        )
        if len(known_sellers) == 1:
            violating_sellers = list(known_sellers)

    facts = {
        "policy_version": request.policy_version,
        "case_id": request.case_id,
        "order_id": request.order_id,
        "customer_claim": "Untrusted context only; classification must follow CSV facts.",
        "order_status": order_seller.order_status,
        "item_total_brl": order_seller.item_total_brl,
        "freight_total_brl": order_seller.freight_total_brl,
        "payment_total_brl": payment.payment_total_brl,
        "payment_count": payment.payment_count,
        "payment_reconciled": is_payment_reconciled(
            payment.payment_total_brl,
            order_seller.item_total_brl,
            order_seller.freight_total_brl,
        ),
        "delivered_late": delivery.delivered_late,
        "delivered_within_estimate": delivery.delivered_within_estimate,
        "seller_late_handoff": order_seller.seller_late_handoff,
        "violating_seller_ids": violating_sellers,
    }
    return "Classify this case using the first matching rule.\nFACTS_JSON:\n" + json.dumps(
        facts, ensure_ascii=True, sort_keys=True
    )


def classify_policy_with_llm(request: PolicyRequest) -> PolicyClassification:
    return call_llm_structured(
        prompt=build_policy_prompt(request),
        response_model=PolicyClassification,
        system_prompt=POLICY_SYSTEM_PROMPT,
        temperature=0.0,
    )
