"""
Unit tests for Payment Agent. Owned by Member 2.
"""
import pytest
from src.agents.payment import PaymentAgent


def test_payment_agent_initialization():
    agent = PaymentAgent()
    assert agent is not None
