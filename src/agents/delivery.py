"""Delivery timeline investigation agent."""

from src.contracts.messages import InvestigationRequest, DeliveryFacts
from src.datetime_utils import parse_olist_timestamp
from src.evidence import make_order_evidence


class DeliveryAgent:
    def __init__(self, dal=None):
        self.dal = dal

    async def process(self, request: InvestigationRequest) -> DeliveryFacts:
        if self.dal is None:
            raise RuntimeError("DeliveryAgent requires a DataAccessLayer")

        order = self.dal.get_order(request.order_id)
        if order is None:
            raise LookupError(f"Order not found: {request.order_id}")

        delivered_value = order.get("order_delivered_customer_date")
        estimated_value = order.get("order_estimated_delivery_date")
        carrier_value = order.get("order_delivered_carrier_date")
        delivered_at = parse_olist_timestamp(
            delivered_value, "order_delivered_customer_date"
        )
        estimated_at = parse_olist_timestamp(
            estimated_value, "order_estimated_delivery_date"
        )
        parse_olist_timestamp(carrier_value, "order_delivered_carrier_date")

        has_delivery_comparison = delivered_at is not None and estimated_at is not None
        delivered_late = has_delivery_comparison and delivered_at > estimated_at
        delivered_within_estimate = (
            has_delivery_comparison and delivered_at <= estimated_at
        )

        return DeliveryFacts(
            order_id=request.order_id,
            order_delivered_customer_date=delivered_value,
            order_estimated_delivery_date=estimated_value,
            order_delivered_carrier_date=carrier_value,
            delivered_late=delivered_late,
            delivered_within_estimate=delivered_within_estimate,
            evidence_candidates=[make_order_evidence(request.order_id)],
        )
