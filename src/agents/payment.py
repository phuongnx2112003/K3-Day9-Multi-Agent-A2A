"""
Payment Agent. Owned by Member 2.
"""
from src.contracts.messages import InvestigationRequest, PaymentFacts


class PaymentAgent:
    def __init__(self, dal=None):
        self.dal = dal

    async def process(self, request: InvestigationRequest) -> PaymentFacts:
        return PaymentFacts(
            order_id=request.order_id,
            payment_total_brl=0.0,
            payment_count=0
        )
