"""
Fixture objects and mock handoff messages for unit and contract testing across all 3 members.
Owned by Member 3.
"""
from src.contracts.messages import (
    MessageEnvelope,
    InvestigationRequest,
    OrderSellerFacts,
    PaymentFacts,
    DeliveryFacts,
    PolicyRequest,
    ResolutionDraft,
    VerificationRequest,
    VerificationResult
)
from src.contracts.output_schema import CaseOutput

MOCK_CASE_ID = "EC_001"
MOCK_ORDER_ID = "e2a03ccf5ea816036608b2d8c3ab8e60"
MOCK_RUN_ID = "run-12345-abcde"
MOCK_TRACE_ID = "trace-67890-fghij"

MOCK_INVESTIGATION_REQUEST = InvestigationRequest(
    case_id=MOCK_CASE_ID,
    order_id=MOCK_ORDER_ID,
    opened_at="2018-10-18T00:00:00-03:00",
    customer_request_message="Tôi cho rằng đơn hàng được giao trễ. Hãy kiểm tra nguyên nhân và quyền lợi phù hợp."
)

MOCK_ORDER_SELLER_FACTS = OrderSellerFacts(
    order_id=MOCK_ORDER_ID,
    order_status="delivered",
    items=[
        {
            "order_item_id": 1,
            "product_id": "prod_123",
            "seller_id": "sel_abc",
            "shipping_limit_date": "2018-10-15T00:00:00",
            "price": 100.0,
            "freight_value": 15.0
        }
    ],
    sellers=[{"seller_id": "sel_abc"}],
    item_total_brl=100.0,
    freight_total_brl=15.0,
    seller_late_handoff=True,
    evidence_candidates=[
        f"order:{MOCK_ORDER_ID}",
        f"item:{MOCK_ORDER_ID}:1",
        "seller:sel_abc"
    ]
)

MOCK_PAYMENT_FACTS = PaymentFacts(
    order_id=MOCK_ORDER_ID,
    payment_rows=[
        {
            "payment_sequential": 1,
            "payment_type": "credit_card",
            "payment_installments": 1,
            "payment_value": 115.0
        }
    ],
    payment_total_brl=115.0,
    payment_count=1,
    reconciled=True,
    evidence_candidates=[f"payment:{MOCK_ORDER_ID}:1"]
)

MOCK_DELIVERY_FACTS = DeliveryFacts(
    order_id=MOCK_ORDER_ID,
    order_delivered_customer_date="2018-10-20T00:00:00",
    order_estimated_delivery_date="2018-10-17T00:00:00",
    order_delivered_carrier_date="2018-10-16T00:00:00",
    delivered_late=True,
    delivered_within_estimate=False,
    evidence_candidates=[]
)

MOCK_POLICY_REQUEST = PolicyRequest(
    case_id=MOCK_CASE_ID,
    order_id=MOCK_ORDER_ID,
    order_seller_facts=MOCK_ORDER_SELLER_FACTS,
    payment_facts=MOCK_PAYMENT_FACTS,
    delivery_facts=MOCK_DELIVERY_FACTS,
    policy_version="EC_POLICY_V1"
)

MOCK_RESOLUTION_DRAFT = ResolutionDraft(
    case_id=MOCK_CASE_ID,
    primary_issue="late_delivery_seller",
    case_status="action_required",
    confidence=0.95,
    order_ids=[MOCK_ORDER_ID],
    item_ids=[f"{MOCK_ORDER_ID}:1"],
    seller_ids=["sel_abc"],
    payment_ids=[f"{MOCK_ORDER_ID}:1"],
    ranked_causes=[{"cause_code": "SELLER_HANDOFF_AFTER_LIMIT", "rank": 1}],
    responsible_parties=[{"party_type": "seller", "party_id": "sel_abc"}],
    evidence_ids=[
        f"order:{MOCK_ORDER_ID}",
        f"item:{MOCK_ORDER_ID}:1",
        f"payment:{MOCK_ORDER_ID}:1",
        "seller:sel_abc",
        "policy:SELLER_HANDOFF_AFTER_LIMIT"
    ],
    currency="BRL",
    item_total_brl=100.0,
    freight_total_brl=15.0,
    payment_total_brl=115.0,
    recommended_refund_brl=15.0,
    resolution_actions=["refund_freight"]
)

MOCK_VERIFICATION_REQUEST = VerificationRequest(
    case_id=MOCK_CASE_ID,
    draft=MOCK_RESOLUTION_DRAFT,
    order_seller_facts=MOCK_ORDER_SELLER_FACTS,
    payment_facts=MOCK_PAYMENT_FACTS,
    delivery_facts=MOCK_DELIVERY_FACTS
)

MOCK_VERIFICATION_RESULT = VerificationResult(
    valid=True,
    errors=[],
    warnings=[],
    verified_at="2026-08-05T10:00:00Z"
)
