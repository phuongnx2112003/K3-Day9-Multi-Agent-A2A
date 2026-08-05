"""Order and seller investigation agent."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Iterable

from src.contracts.messages import InvestigationRequest, OrderSellerFacts
from src.datetime_utils import parse_olist_timestamp
from src.evidence import (
    make_item_evidence,
    make_order_evidence,
    make_seller_evidence,
)


MONEY_QUANTUM = Decimal("0.01")


def _sum_money(rows: Iterable[Dict[str, Any]], field: str) -> float:
    total = Decimal("0")
    for row in rows:
        value = row.get(field)
        try:
            total += Decimal(str(value))
        except (InvalidOperation, TypeError) as exc:
            raise ValueError(f"Invalid {field} value: {value!r}") from exc
    return float(total.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP))


class OrderSellerAgent:
    def __init__(self, dal=None):
        self.dal = dal

    async def process(self, request: InvestigationRequest) -> OrderSellerFacts:
        if self.dal is None:
            raise RuntimeError("OrderSellerAgent requires a DataAccessLayer")

        order = self.dal.get_order(request.order_id)
        if order is None:
            raise LookupError(f"Order not found: {request.order_id}")

        carrier_date = parse_olist_timestamp(
            order.get("order_delivered_carrier_date"),
            "order_delivered_carrier_date",
        )
        items = self.dal.get_items(request.order_id)
        seller_late_handoff = False
        for item in items:
            shipping_limit = parse_olist_timestamp(
                item.get("shipping_limit_date"), "shipping_limit_date"
            )
            is_late = (
                carrier_date is not None
                and shipping_limit is not None
                and carrier_date > shipping_limit
            )
            item["seller_late_handoff"] = is_late
            seller_late_handoff = seller_late_handoff or is_late

        seller_facts = []
        seen_sellers = set()
        for item in items:
            seller_id = str(item["seller_id"])
            if seller_id in seen_sellers:
                continue
            seen_sellers.add(seller_id)
            seller = self.dal.get_seller(seller_id)
            if seller is not None:
                seller["seller_late_handoff"] = any(
                    row["seller_late_handoff"]
                    for row in items
                    if str(row["seller_id"]) == seller_id
                )
                seller_facts.append(seller)

        evidence_candidates = [make_order_evidence(request.order_id)]
        evidence_candidates.extend(
            make_item_evidence(request.order_id, int(item["order_item_id"]))
            for item in items
        )
        evidence_candidates.extend(
            make_seller_evidence(str(seller["seller_id"]))
            for seller in seller_facts
        )

        return OrderSellerFacts(
            order_id=request.order_id,
            order_status=str(order["order_status"]),
            items=items,
            sellers=seller_facts,
            item_total_brl=_sum_money(items, "price"),
            freight_total_brl=_sum_money(items, "freight_value"),
            seller_late_handoff=seller_late_handoff,
            evidence_candidates=evidence_candidates,
        )
