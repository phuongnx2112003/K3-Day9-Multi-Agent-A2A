"""Behavioral tests for Delivery Agent."""

import asyncio
from pathlib import Path

import pytest

from src.agents.delivery import DeliveryAgent
from src.contracts.messages import InvestigationRequest
from src.data_access import DataAccessLayer
from tests.member1_fixtures import (
    CANCELED_ORDER_ID,
    LATE_ORDER_ID,
    ON_TIME_ORDER_ID,
    write_member1_dataset,
)


def _request(order_id: str) -> InvestigationRequest:
    return InvestigationRequest(
        case_id="EC_TEST",
        order_id=order_id,
        opened_at="2018-01-15T00:00:00-03:00",
        customer_request_message="Kiểm tra giao hàng",
    )


@pytest.fixture
def agent(tmp_path: Path) -> DeliveryAgent:
    dal = DataAccessLayer(write_member1_dataset(tmp_path / "data"))
    dal.load_data()
    return DeliveryAgent(dal)


def test_marks_delivery_after_estimate_as_late(agent: DeliveryAgent):
    facts = asyncio.run(agent.process(_request(LATE_ORDER_ID)))

    assert facts.delivered_late is True
    assert facts.delivered_within_estimate is False
    assert facts.order_delivered_carrier_date == "2018-01-04 12:00:00"
    assert facts.evidence_candidates == [f"order:{LATE_ORDER_ID}"]


def test_delivery_exactly_on_estimate_is_within_estimate(agent: DeliveryAgent):
    facts = asyncio.run(agent.process(_request(ON_TIME_ORDER_ID)))

    assert facts.delivered_late is False
    assert facts.delivered_within_estimate is True


def test_missing_delivery_date_is_not_assumed_on_time(agent: DeliveryAgent):
    facts = asyncio.run(agent.process(_request(CANCELED_ORDER_ID)))

    assert facts.order_delivered_customer_date is None
    assert facts.delivered_late is False
    assert facts.delivered_within_estimate is False


def test_missing_order_is_rejected(agent: DeliveryAgent):
    with pytest.raises(LookupError, match="order-missing"):
        asyncio.run(agent.process(_request("order-missing")))


def test_agent_requires_data_access():
    with pytest.raises(RuntimeError, match="DataAccessLayer"):
        asyncio.run(DeliveryAgent().process(_request(LATE_ORDER_ID)))
