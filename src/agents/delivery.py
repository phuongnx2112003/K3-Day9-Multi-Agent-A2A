"""
Delivery Agent. Owned by Member 1.
"""
from src.contracts.messages import InvestigationRequest, DeliveryFacts


class DeliveryAgent:
    def __init__(self, dal=None):
        self.dal = dal

    async def process(self, request: InvestigationRequest) -> DeliveryFacts:
        return DeliveryFacts(
            order_id=request.order_id,
            delivered_late=False,
            delivered_within_estimate=True
        )
