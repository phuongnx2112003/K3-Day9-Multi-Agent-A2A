"""Behavioral tests for Order & Seller Agent."""

import asyncio
from pathlib import Path

import pytest

from src.agents.order_seller import OrderSellerAgent
from src.contracts.messages import InvestigationRequest
from src.data_access import DataAccessLayer
from tests.member1_fixtures import CANCELED_ORDER_ID, LATE_ORDER_ID, write_member1_dataset


def _request(order_id: str) -> InvestigationRequest:
    return InvestigationRequest(
        case_id="EC_TEST",
        order_id=order_id,
        opened_at="2018-01-15T00:00:00-03:00",
        customer_request_message="Kiểm tra đơn hàng",
    )


@pytest.fixture
def agent(tmp_path: Path) -> OrderSellerAgent:
    dal = DataAccessLayer(write_member1_dataset(tmp_path / "data"))
    dal.load_data()
    return OrderSellerAgent(dal)


def test_builds_multi_item_seller_facts_and_evidence(agent: OrderSellerAgent):
    facts = asyncio.run(agent.process(_request(LATE_ORDER_ID)))

    assert facts.order_status == "delivered"
    assert facts.item_total_brl == 30.30
    assert facts.freight_total_brl == 3.10
    assert facts.seller_late_handoff is True
    assert [item["order_item_id"] for item in facts.items] == [1, 2]
    assert facts.items[0]["seller_late_handoff"] is True
    assert facts.items[1]["seller_late_handoff"] is False
    assert [seller["seller_id"] for seller in facts.sellers] == ["seller-a", "seller-b"]
    assert facts.sellers[0]["seller_late_handoff"] is True
    assert facts.sellers[1]["seller_late_handoff"] is False
    assert facts.evidence_candidates == [
        f"order:{LATE_ORDER_ID}",
        f"item:{LATE_ORDER_ID}:1",
        f"item:{LATE_ORDER_ID}:2",
        "seller:seller-a",
        "seller:seller-b",
    ]


def test_itemless_order_has_zero_totals_and_only_order_evidence(
    agent: OrderSellerAgent,
):
    facts = asyncio.run(agent.process(_request(CANCELED_ORDER_ID)))

    assert facts.order_status == "canceled"
    assert facts.items == []
    assert facts.sellers == []
    assert facts.item_total_brl == 0.0
    assert facts.freight_total_brl == 0.0
    assert facts.seller_late_handoff is False
    assert facts.evidence_candidates == [f"order:{CANCELED_ORDER_ID}"]


def test_missing_order_is_rejected(agent: OrderSellerAgent):
    with pytest.raises(LookupError, match="order-missing"):
        asyncio.run(agent.process(_request("order-missing")))


def test_agent_requires_data_access():
    with pytest.raises(RuntimeError, match="DataAccessLayer"):
        asyncio.run(OrderSellerAgent().process(_request(LATE_ORDER_ID)))
