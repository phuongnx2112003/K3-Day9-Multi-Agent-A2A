"""
Unit tests for Delivery Agent. Owned by Member 1.
"""
import pytest
from src.agents.delivery import DeliveryAgent


def test_delivery_agent_initialization():
    agent = DeliveryAgent()
    assert agent is not None
