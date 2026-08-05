"""
Unit tests for Deterministic Policy Rules. Owned by Member 2.
"""
import pytest
from src.policy_rules import round_money


def test_round_money():
    assert round_money(10.555) == 10.56
    assert round_money(10.554) == 10.55
