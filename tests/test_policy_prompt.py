import json

from src.contracts.fixtures import MOCK_POLICY_REQUEST
from src.policy_prompt import POLICY_SYSTEM_PROMPT, build_policy_prompt


def test_policy_system_prompt_contains_all_rules_in_priority_order():
    issues = [
        "canceled_order_paid",
        "unavailable_order_paid",
        "late_delivery_seller",
        "late_delivery_logistics",
        "valid_split_payment",
        "unsupported_late_claim",
    ]

    positions = [POLICY_SYSTEM_PROMPT.index(issue) for issue in issues]

    assert positions == sorted(positions)
    assert "Do not invent" in POLICY_SYSTEM_PROMPT
    assert "Never calculate or return a refund amount" in POLICY_SYSTEM_PROMPT


def test_policy_prompt_contains_grounded_factual_summary():
    prompt = build_policy_prompt(MOCK_POLICY_REQUEST)
    facts = json.loads(prompt.split("FACTS_JSON:\n", 1)[1])

    assert facts["order_id"] == MOCK_POLICY_REQUEST.order_id
    assert facts["order_status"] == "delivered"
    assert facts["delivered_late"] is True
    assert facts["seller_late_handoff"] is True
    assert facts["payment_reconciled"] is True
    assert facts["violating_seller_ids"] == ["sel_abc"]
