"""
Unit tests for Order & Seller Agent. Owned by Member 1.
"""
import pytest
from src.agents.order_seller import OrderSellerAgent


def test_order_seller_agent_initialization():
    agent = OrderSellerAgent()
    assert agent is not None
