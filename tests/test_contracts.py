"""
Comprehensive unit tests for contracts, handoff schemas, and fixtures.
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
from src.contracts.fixtures import (
    MOCK_CASE_ID,
    MOCK_ORDER_ID,
    MOCK_INVESTIGATION_REQUEST,
    MOCK_ORDER_SELLER_FACTS,
    MOCK_PAYMENT_FACTS,
    MOCK_DELIVERY_FACTS,
    MOCK_POLICY_REQUEST,
    MOCK_RESOLUTION_DRAFT,
    MOCK_VERIFICATION_REQUEST,
    MOCK_VERIFICATION_RESULT
)


def test_investigation_request_schema():
    req = MOCK_INVESTIGATION_REQUEST
    assert req.case_id == MOCK_CASE_ID
    assert req.order_id == MOCK_ORDER_ID


def test_order_seller_facts_schema():
    facts = MOCK_ORDER_SELLER_FACTS
    assert facts.order_id == MOCK_ORDER_ID
    assert facts.item_total_brl == 100.0
    assert facts.freight_total_brl == 15.0
    assert len(facts.items) == 1


def test_payment_facts_schema():
    facts = MOCK_PAYMENT_FACTS
    assert facts.order_id == MOCK_ORDER_ID
    assert facts.payment_total_brl == 115.0
    assert facts.reconciled is True


def test_delivery_facts_schema():
    facts = MOCK_DELIVERY_FACTS
    assert facts.order_id == MOCK_ORDER_ID
    assert facts.delivered_late is True


def test_resolution_draft_conversion_to_case_output():
    draft = MOCK_RESOLUTION_DRAFT
    case_output = draft.to_case_output()
    assert isinstance(case_output, CaseOutput)
    assert case_output.case_id == MOCK_CASE_ID
    assert case_output.assessment.primary_issue == "late_delivery_seller"
    assert case_output.assessment.case_status == "action_required"
    assert case_output.financial_resolution.recommended_refund_brl == 15.0


def test_verification_result_schema():
    res = MOCK_VERIFICATION_RESULT
    assert res.valid is True
    assert len(res.errors) == 0
