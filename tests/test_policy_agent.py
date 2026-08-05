"""
Unit tests for Policy Agent. Owned by Member 2 (Minh Đức).
"""
import pytest
from src.contracts.fixtures import MOCK_POLICY_REQUEST
from src.agents.policy import PolicyAgent
from src.contracts.messages import ResolutionDraft


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
