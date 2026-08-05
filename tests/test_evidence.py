"""
Unit tests for Evidence ID formatting utilities. Owned by Member 3.
"""
import pytest
from src.evidence import (
    make_order_evidence,
    make_item_evidence,
    make_payment_evidence,
    make_seller_evidence,
    make_policy_evidence
)


def test_evidence_formatters():
    assert make_order_evidence("abc") == "order:abc"
    assert make_item_evidence("abc", 1) == "item:abc:1"
    assert make_payment_evidence("abc", 2) == "payment:abc:2"
    assert make_seller_evidence("sel1") == "seller:sel1"
    assert make_policy_evidence("SELLER_HANDOFF_AFTER_LIMIT") == "policy:SELLER_HANDOFF_AFTER_LIMIT"
