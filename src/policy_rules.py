"""
Deterministic Policy Rules implementation for EC_POLICY_V1. Owned by Member 2 (Minh Đức).
Applies strict business logic rules according to priority table.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict

from src.contracts.messages import OrderSellerFacts, PaymentFacts, DeliveryFacts


def round_money(amount: float) -> float:
    """Decimal rounding to 2 decimal places."""
    return float(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def is_payment_reconciled(
    payment_total_brl: float, item_total_brl: float, freight_total_brl: float
) -> bool:
    payment = Decimal(str(payment_total_brl))
    expected = Decimal(str(item_total_brl)) + Decimal(str(freight_total_brl))
    return abs(payment - expected) <= Decimal("0.10")


def evaluate_policy(
    order_seller_facts: OrderSellerFacts,
    payment_facts: PaymentFacts,
    delivery_facts: DeliveryFacts
) -> Dict[str, Any]:
    """
    Evaluates business rules according to EC_POLICY_V1 in strict priority order.
    
    Priority Order:
    1. canceled_order_paid
    2. unavailable_order_paid
    3. late_delivery_seller
    4. late_delivery_logistics
    5. valid_split_payment
    6. unsupported_late_claim
    """
    order_status = (order_seller_facts.order_status or "").lower()
    payment_total = round_money(payment_facts.payment_total_brl)
    item_total = round_money(order_seller_facts.item_total_brl)
    freight_total = round_money(order_seller_facts.freight_total_brl)

    # 1. canceled_order_paid
    if order_status == "canceled" and payment_total > 0:
        return {
            "primary_issue": "canceled_order_paid",
            "case_status": "action_required",
            "confidence": 1.0,
            "root_cause_code": "ORDER_CANCELED_AFTER_PAYMENT",
            "responsible_parties": [{"party_type": "platform", "party_id": "OLIST_PLATFORM"}],
            "recommended_refund_brl": payment_total,
            "resolution_actions": ["issue_full_refund"]
        }

    # 2. unavailable_order_paid
    if order_status == "unavailable" and payment_total > 0:
        return {
            "primary_issue": "unavailable_order_paid",
            "case_status": "action_required",
            "confidence": 1.0,
            "root_cause_code": "ORDER_UNAVAILABLE_AFTER_PAYMENT",
            "responsible_parties": [{"party_type": "platform", "party_id": "OLIST_PLATFORM"}],
            "recommended_refund_brl": payment_total,
            "resolution_actions": ["issue_full_refund"]
        }

    # Determine late delivery conditions
    delivered_late = delivery_facts.delivered_late

    # 3. late_delivery_seller
    if delivered_late and order_seller_facts.seller_late_handoff:
        violating_sellers = [
            seller.get("seller_id")
            for seller in order_seller_facts.sellers
            if seller.get("seller_late_handoff") and seller.get("seller_id")
        ]
        if not violating_sellers:
            violating_sellers = [
                item.get("seller_id")
                for item in order_seller_facts.items
                if item.get("seller_late_handoff") and item.get("seller_id")
            ]
        if not violating_sellers:
            known_sellers = {
                seller.get("seller_id")
                for seller in order_seller_facts.sellers
                if seller.get("seller_id")
            }
            known_sellers.update(
                item.get("seller_id")
                for item in order_seller_facts.items
                if item.get("seller_id")
            )
            if len(known_sellers) == 1:
                violating_sellers = list(known_sellers)
        if not violating_sellers:
            raise ValueError("Seller late handoff has no violating seller evidence")
        seller_id = violating_sellers[0]

        return {
            "primary_issue": "late_delivery_seller",
            "case_status": "action_required",
            "confidence": 0.95,
            "root_cause_code": "SELLER_HANDOFF_AFTER_LIMIT",
            "responsible_parties": [{"party_type": "seller", "party_id": seller_id}],
            "recommended_refund_brl": freight_total,
            "resolution_actions": ["refund_freight"]
        }

    # 4. late_delivery_logistics
    if delivered_late and not order_seller_facts.seller_late_handoff:
        return {
            "primary_issue": "late_delivery_logistics",
            "case_status": "action_required",
            "confidence": 0.95,
            "root_cause_code": "CARRIER_DELIVERED_AFTER_ESTIMATE",
            "responsible_parties": [{"party_type": "logistics_provider", "party_id": "LOGISTICS_PROVIDER"}],
            "recommended_refund_brl": freight_total,
            "resolution_actions": ["refund_freight"]
        }

    # Check payment reconciliation tolerance (within 0.10 BRL)
    reconciled = is_payment_reconciled(payment_total, item_total, freight_total)

    # 5. valid_split_payment
    if payment_facts.payment_count >= 2 and reconciled:
        return {
            "primary_issue": "valid_split_payment",
            "case_status": "no_action",
            "confidence": 0.95,
            "root_cause_code": "MULTIPLE_PAYMENTS_RECONCILED",
            "responsible_parties": [],
            "recommended_refund_brl": 0.0,
            "resolution_actions": ["explain_valid_split_payment"]
        }

    # 6. unsupported_late_claim
    if delivery_facts.delivered_within_estimate and reconciled:
        return {
            "primary_issue": "unsupported_late_claim",
            "case_status": "no_action",
            "confidence": 1.0,
            "root_cause_code": "DELIVERY_WITHIN_ESTIMATE",
            "responsible_parties": [],
            "recommended_refund_brl": 0.0,
            "resolution_actions": ["reject_late_refund"]
        }

    raise ValueError("No EC_POLICY_V1 rule matched the verified facts")
