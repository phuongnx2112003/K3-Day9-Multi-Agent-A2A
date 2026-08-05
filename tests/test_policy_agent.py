"""
Unit tests for Policy Agent. Owned by Member 2 (Minh Đức).
"""
import pytest
from src.contracts.fixtures import MOCK_POLICY_REQUEST
from src.agents.policy import PolicyAgent
from src.contracts.messages import ResolutionDraft
from src.policy_prompt import PolicyClassification


@pytest.mark.asyncio
async def test_policy_agent_process_mock_request():
    agent = PolicyAgent()
    draft: ResolutionDraft = await agent.process(MOCK_POLICY_REQUEST)

    assert draft.case_id == MOCK_POLICY_REQUEST.case_id
    assert draft.primary_issue == "late_delivery_seller"
    assert draft.case_status == "action_required"
    assert draft.recommended_refund_brl == 15.0
    assert draft.item_total_brl == 100.0
    assert draft.freight_total_brl == 15.0
    assert draft.payment_total_brl == 115.0
    assert "policy:SELLER_HANDOFF_AFTER_LIMIT" in draft.evidence_ids
    assert f"order:{MOCK_POLICY_REQUEST.order_id}" in draft.evidence_ids
    assert draft.resolution_actions == ["refund_freight"]


def matching_classification() -> PolicyClassification:
    return PolicyClassification(
        primary_issue="late_delivery_seller",
        root_cause_code="SELLER_HANDOFF_AFTER_LIMIT",
        case_status="action_required",
        responsible_party_type="seller",
        responsible_party_id="sel_abc",
        resolution_action="refund_freight",
        rationale="delivered_late and seller_late_handoff are true",
    )


@pytest.mark.asyncio
async def test_policy_agent_accepts_matching_llm_classification():
    agent = PolicyAgent(
        use_llm=True,
        llm_classifier=lambda request: matching_classification(),
    )

    draft = await agent.process(MOCK_POLICY_REQUEST)

    assert draft.primary_issue == "late_delivery_seller"
    assert agent.last_decision_source == "llm_verified"
    assert agent.last_llm_error is None


@pytest.mark.asyncio
async def test_policy_agent_falls_back_when_llm_disagrees():
    wrong = matching_classification().model_copy(
        update={
            "primary_issue": "late_delivery_logistics",
            "root_cause_code": "CARRIER_DELIVERED_AFTER_ESTIMATE",
            "responsible_party_type": "logistics_provider",
            "responsible_party_id": "LOGISTICS_PROVIDER",
        }
    )
    agent = PolicyAgent(use_llm=True, llm_classifier=lambda request: wrong)

    draft = await agent.process(MOCK_POLICY_REQUEST)

    assert draft.primary_issue == "late_delivery_seller"
    assert agent.last_decision_source == "deterministic_fallback"
    assert "primary_issue" in agent.last_llm_error
