"""
Evidence ID formatting and verification utilities.
"""
def make_order_evidence(order_id: str) -> str:
    return f"order:{order_id}"

def make_item_evidence(order_id: str, order_item_id: int) -> str:
    return f"item:{order_id}:{order_item_id}"

def make_payment_evidence(order_id: str, payment_seq: int) -> str:
    return f"payment:{order_id}:{payment_seq}"

def make_seller_evidence(seller_id: str) -> str:
    return f"seller:{seller_id}"

def make_policy_evidence(root_cause_code: str) -> str:
    return f"policy:{root_cause_code}"
