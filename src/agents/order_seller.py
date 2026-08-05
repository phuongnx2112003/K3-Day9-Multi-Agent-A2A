"""
Order & Seller Agent. Owned by Member 1.
"""
from src.contracts.messages import InvestigationRequest, OrderSellerFacts


class OrderSellerAgent:
    def __init__(self, dal=None):
        self.dal = dal

    async def process(self, request: InvestigationRequest) -> OrderSellerFacts:
        # Skeleton implementation
        return OrderSellerFacts(
            order_id=request.order_id,
            order_status="delivered",
            item_total_brl=0.0,
            freight_total_brl=0.0
        )
