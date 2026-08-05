"""
Comprehensive unit tests for Quality Gate VerifierAgent.
Owned by Member 3.
"""
import pytest
from src.agents.verifier import VerifierAgent
from src.contracts.fixtures import (
    MOCK_VERIFICATION_REQUEST,
    MOCK_RESOLUTION_DRAFT,
    MOCK_ORDER_SELLER_FACTS,
    MOCK_PAYMENT_FACTS,
    MOCK_DELIVERY_FACTS,
    MOCK_CASE_ID,
    MOCK_ORDER_ID
)
from src.contracts.messages import VerificationRequest, ResolutionDraft


@pytest.mark.asyncio
async def test_verifier_valid_draft():
    verifier = VerifierAgent()
    res = await verifier.verify(MOCK_VERIFICATION_REQUEST)
    assert res.valid is True
    assert len(res.errors) == 0


@pytest.mark.asyncio
async def test_verifier_invalid_confidence():
    verifier = VerifierAgent()
    invalid_draft = MOCK_RESOLUTION_DRAFT.model_copy()
    invalid_draft.confidence = 1.5

    req = VerificationRequest(
        case_id=MOCK_CASE_ID,
        draft=invalid_draft,
        order_seller_facts=MOCK_ORDER_SELLER_FACTS,
        payment_facts=MOCK_PAYMENT_FACTS,
        delivery_facts=MOCK_DELIVERY_FACTS
    )
    res = await verifier.verify(req)
    assert res.valid is False
    assert any("confidence out of bounds" in e for e in res.errors)


@pytest.mark.asyncio
async def test_verifier_exceeding_entity_limits():
    verifier = VerifierAgent()
    invalid_draft = MOCK_RESOLUTION_DRAFT.model_copy()
    invalid_draft.evidence_ids = [f"evidence:{i}" for i in range(12)]  # limit 10

    req = VerificationRequest(
        case_id=MOCK_CASE_ID,
        draft=invalid_draft,
        order_seller_facts=MOCK_ORDER_SELLER_FACTS,
        payment_facts=MOCK_PAYMENT_FACTS,
        delivery_facts=MOCK_DELIVERY_FACTS
    )
    res = await verifier.verify(req)
    assert res.valid is False
    assert any("evidence_ids exceeds limit of 10" in e for e in res.errors)


@pytest.mark.asyncio
async def test_verifier_financial_and_status_mismatch():
    verifier = VerifierAgent()
    invalid_draft = MOCK_RESOLUTION_DRAFT.model_copy()
    invalid_draft.recommended_refund_brl = 0.0  # refund 0 but primary issue is late_delivery_seller
    invalid_draft.case_status = "action_required"  # mismatch: refund 0 should be no_action

    req = VerificationRequest(
        case_id=MOCK_CASE_ID,
        draft=invalid_draft,
        order_seller_facts=MOCK_ORDER_SELLER_FACTS,
        payment_facts=MOCK_PAYMENT_FACTS,
        delivery_facts=MOCK_DELIVERY_FACTS
    )
    res = await verifier.verify(req)
    assert res.valid is False
    assert len(res.errors) >= 1


@pytest.mark.asyncio
async def test_verifier_rejects_ungrounded_evidence():
    verifier = VerifierAgent()
    invalid_draft = MOCK_RESOLUTION_DRAFT.model_copy(
        update={
            "evidence_ids": [
                *MOCK_RESOLUTION_DRAFT.evidence_ids,
                f"payment:{MOCK_ORDER_ID}:999",
            ]
        }
    )
    req = VerificationRequest(
        case_id=MOCK_CASE_ID,
        draft=invalid_draft,
        order_seller_facts=MOCK_ORDER_SELLER_FACTS,
        payment_facts=MOCK_PAYMENT_FACTS,
        delivery_facts=MOCK_DELIVERY_FACTS,
    )

    res = await verifier.verify(req)

    assert res.valid is False
    assert any("not grounded" in error for error in res.errors)


@pytest.mark.asyncio
async def test_verifier_rejects_policy_decision_mismatch():
    verifier = VerifierAgent()
    invalid_draft = MOCK_RESOLUTION_DRAFT.model_copy(
        update={
            "primary_issue": "late_delivery_logistics",
            "responsible_parties": [
                {
                    "party_type": "logistics_provider",
                    "party_id": "LOGISTICS_PROVIDER",
                }
            ],
        }
    )
    req = VerificationRequest(
        case_id=MOCK_CASE_ID,
        draft=invalid_draft,
        order_seller_facts=MOCK_ORDER_SELLER_FACTS,
        payment_facts=MOCK_PAYMENT_FACTS,
        delivery_facts=MOCK_DELIVERY_FACTS,
    )

    res = await verifier.verify(req)

    assert res.valid is False
    assert any("primary_issue does not match" in error for error in res.errors)
