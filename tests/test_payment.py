"""
Unit tests for Payment Agent. Owned by Member 2 (Minh Đức).
"""
import pytest
from src.contracts.messages import InvestigationRequest, PaymentFacts
from src.agents.payment import PaymentAgent, round_money


class MockDAL:
    def __init__(self, payments=None):
        self.payments = payments or []

    def get_payments(self, order_id: str):
        return self.payments


@pytest.mark.asyncio
async def test_payment_agent_with_mock_dal():
    mock_payments = [
        {"payment_sequential": 1, "payment_type": "credit_card", "payment_installments": 3, "payment_value": 50.55},
        {"payment_sequential": 2, "payment_type": "voucher", "payment_installments": 1, "payment_value": 25.45}
    ]
    dal = MockDAL(payments=mock_payments)
    agent = PaymentAgent(dal=dal)

    req = InvestigationRequest(
        case_id="EC_001",
        order_id="order_123",
        opened_at="2018-10-18T00:00:00-03:00",
        customer_request_message="Test message"
    )

    facts: PaymentFacts = await agent.process(req)

    assert facts.order_id == "order_123"
    assert facts.payment_count == 2
    assert facts.payment_total_brl == 76.00  # 50.55 + 25.45
    assert len(facts.evidence_candidates) == 2
    assert "payment:order_123:1" in facts.evidence_candidates
    assert "payment:order_123:2" in facts.evidence_candidates


@pytest.mark.asyncio
async def test_payment_agent_no_dal():
    agent = PaymentAgent(dal=None)
    req = InvestigationRequest(
        case_id="EC_002",
        order_id="order_456",
        opened_at="2018-10-18T00:00:00-03:00",
        customer_request_message="Test message"
    )
    facts = await agent.process(req)
    assert facts.payment_count == 0
    assert facts.payment_total_brl == 0.0
