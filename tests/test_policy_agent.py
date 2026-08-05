"""
Unit tests for Policy Agent. Owned by Member 2.
"""
import pytest
from src.agents.policy import PolicyAgent


def test_policy_agent_initialization():
    agent = PolicyAgent()
    assert agent is not None
