"""
Unit tests for Deterministic Policy Rules. Owned by Member 2 (Minh Đức).
"""
import pytest
from src.contracts.messages import OrderSellerFacts, PaymentFacts, DeliveryFacts
from src.policy_rules import evaluate_policy, round_money


def test_round_money():
    assert round_money(10.555) == 10.56
    assert round_money(10.554) == 10.55
    assert round_money(0.0) == 0.0


def test_policy_canceled_order_paid():
    order_seller = OrderSellerFacts(order_id="o1", order_status="canceled", item_total_brl=100.0, freight_total_brl=15.0)
    payment = PaymentFacts(order_id="o1", payment_rows=[{}], payment_total_brl=115.0, payment_count=1)
    delivery = DeliveryFacts(order_id="o1")

    res = evaluate_policy(order_seller, payment, delivery)

    assert res["primary_issue"] == "canceled_order_paid"
    assert res["case_status"] == "action_required"
    assert res["root_cause_code"] == "ORDER_CANCELED_AFTER_PAYMENT"
    assert res["recommended_refund_brl"] == 115.0
    assert res["responsible_parties"] == [{"party_type": "platform", "party_id": "OLIST_PLATFORM"}]
    assert res["resolution_actions"] == ["issue_full_refund"]


def test_policy_unavailable_order_paid():
    order_seller = OrderSellerFacts(order_id="o2", order_status="unavailable", item_total_brl=50.0, freight_total_brl=10.0)
    payment = PaymentFacts(order_id="o2", payment_rows=[{}], payment_total_brl=60.0, payment_count=1)
    delivery = DeliveryFacts(order_id="o2")

    res = evaluate_policy(order_seller, payment, delivery)

    assert res["primary_issue"] == "unavailable_order_paid"
    assert res["case_status"] == "action_required"
    assert res["root_cause_code"] == "ORDER_UNAVAILABLE_AFTER_PAYMENT"
    assert res["recommended_refund_brl"] == 60.0
    assert res["responsible_parties"] == [{"party_type": "platform", "party_id": "OLIST_PLATFORM"}]


def test_policy_late_delivery_seller():
    order_seller = OrderSellerFacts(
        order_id="o3",
        order_status="delivered",
        sellers=[{"seller_id": "seller_abc"}],
        item_total_brl=100.0,
        freight_total_brl=20.0,
        seller_late_handoff=True
    )
    payment = PaymentFacts(order_id="o3", payment_rows=[{}], payment_total_brl=120.0, payment_count=1)
    delivery = DeliveryFacts(order_id="o3", delivered_late=True)

    res = evaluate_policy(order_seller, payment, delivery)

    assert res["primary_issue"] == "late_delivery_seller"
    assert res["case_status"] == "action_required"
    assert res["root_cause_code"] == "SELLER_HANDOFF_AFTER_LIMIT"
    assert res["recommended_refund_brl"] == 20.0
    assert res["responsible_parties"] == [{"party_type": "seller", "party_id": "seller_abc"}]
    assert res["resolution_actions"] == ["refund_freight"]


def test_policy_late_delivery_logistics():
    order_seller = OrderSellerFacts(
        order_id="o4",
        order_status="delivered",
        sellers=[{"seller_id": "seller_abc"}],
        item_total_brl=100.0,
        freight_total_brl=20.0,
        seller_late_handoff=False
    )
    payment = PaymentFacts(order_id="o4", payment_rows=[{}], payment_total_brl=120.0, payment_count=1)
    delivery = DeliveryFacts(order_id="o4", delivered_late=True)

    res = evaluate_policy(order_seller, payment, delivery)

    assert res["primary_issue"] == "late_delivery_logistics"
    assert res["case_status"] == "action_required"
    assert res["root_cause_code"] == "CARRIER_DELIVERED_AFTER_ESTIMATE"
    assert res["recommended_refund_brl"] == 20.0
    assert res["responsible_parties"] == [{"party_type": "logistics_provider", "party_id": "LOGISTICS_PROVIDER"}]
    assert res["resolution_actions"] == ["refund_freight"]


def test_policy_valid_split_payment():
    order_seller = OrderSellerFacts(order_id="o5", order_status="delivered", item_total_brl=100.0, freight_total_brl=20.0)
    payment = PaymentFacts(order_id="o5", payment_rows=[{}, {}], payment_total_brl=120.05, payment_count=2)
    delivery = DeliveryFacts(order_id="o5", delivered_late=False, delivered_within_estimate=True)

    res = evaluate_policy(order_seller, payment, delivery)

    assert res["primary_issue"] == "valid_split_payment"
    assert res["case_status"] == "no_action"
    assert res["root_cause_code"] == "MULTIPLE_PAYMENTS_RECONCILED"
    assert res["recommended_refund_brl"] == 0.0
    assert res["responsible_parties"] == []
    assert res["resolution_actions"] == ["explain_valid_split_payment"]


def test_policy_unsupported_late_claim():
    order_seller = OrderSellerFacts(order_id="o6", order_status="delivered", item_total_brl=100.0, freight_total_brl=20.0)
    payment = PaymentFacts(order_id="o6", payment_rows=[{}], payment_total_brl=120.0, payment_count=1)
    delivery = DeliveryFacts(order_id="o6", delivered_late=False, delivered_within_estimate=True)

    res = evaluate_policy(order_seller, payment, delivery)

    assert res["primary_issue"] == "unsupported_late_claim"
    assert res["case_status"] == "no_action"
    assert res["root_cause_code"] == "DELIVERY_WITHIN_ESTIMATE"
    assert res["recommended_refund_brl"] == 0.0
    assert res["responsible_parties"] == []
    assert res["resolution_actions"] == ["reject_late_refund"]
