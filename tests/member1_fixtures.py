"""Small Olist dataset used by Member 1 behavioral tests."""

import csv
from pathlib import Path
from typing import Any, Dict, Iterable, List


LATE_ORDER_ID = "order-late"
ON_TIME_ORDER_ID = "order-on-time"
CANCELED_ORDER_ID = "order-canceled"


def _write_csv(path: Path, rows: Iterable[Dict[str, Any]], fields: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_member1_dataset(data_dir: Path) -> Path:
    data_dir.mkdir()
    order_fields = [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    _write_csv(
        data_dir / "olist_orders_dataset.csv",
        [
            {
                "order_id": LATE_ORDER_ID,
                "customer_id": "customer-1",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-01-01 09:00:00",
                "order_approved_at": "2018-01-01 10:00:00",
                "order_delivered_carrier_date": "2018-01-04 12:00:00",
                "order_delivered_customer_date": "2018-01-10 12:00:00",
                "order_estimated_delivery_date": "2018-01-08 00:00:00",
            },
            {
                "order_id": ON_TIME_ORDER_ID,
                "customer_id": "customer-2",
                "order_status": "delivered",
                "order_purchase_timestamp": "2018-01-01 09:00:00",
                "order_approved_at": "2018-01-01 10:00:00",
                "order_delivered_carrier_date": "2018-01-02 12:00:00",
                "order_delivered_customer_date": "2018-01-06 00:00:00",
                "order_estimated_delivery_date": "2018-01-06 00:00:00",
            },
            {
                "order_id": CANCELED_ORDER_ID,
                "customer_id": "customer-3",
                "order_status": "canceled",
                "order_purchase_timestamp": "2018-01-01 09:00:00",
                "order_approved_at": "2018-01-01 10:00:00",
                "order_delivered_carrier_date": "",
                "order_delivered_customer_date": "",
                "order_estimated_delivery_date": "2018-01-09 00:00:00",
            },
        ],
        order_fields,
    )

    item_fields = [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ]
    _write_csv(
        data_dir / "olist_order_items_dataset.csv",
        [
            {
                "order_id": LATE_ORDER_ID,
                "order_item_id": 2,
                "product_id": "product-2",
                "seller_id": "seller-b",
                "shipping_limit_date": "2018-01-05 12:00:00",
                "price": "20.20",
                "freight_value": "2.05",
            },
            {
                "order_id": LATE_ORDER_ID,
                "order_item_id": 1,
                "product_id": "product-1",
                "seller_id": "seller-a",
                "shipping_limit_date": "2018-01-03 12:00:00",
                "price": "10.10",
                "freight_value": "1.05",
            },
            {
                "order_id": ON_TIME_ORDER_ID,
                "order_item_id": 1,
                "product_id": "product-3",
                "seller_id": "seller-a",
                "shipping_limit_date": "2018-01-03 12:00:00",
                "price": "8.25",
                "freight_value": "1.75",
            },
        ],
        item_fields,
    )

    payment_fields = [
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ]
    _write_csv(
        data_dir / "olist_order_payments_dataset.csv",
        [
            {
                "order_id": LATE_ORDER_ID,
                "payment_sequential": 2,
                "payment_type": "voucher",
                "payment_installments": 1,
                "payment_value": "3.40",
            },
            {
                "order_id": LATE_ORDER_ID,
                "payment_sequential": 1,
                "payment_type": "credit_card",
                "payment_installments": 2,
                "payment_value": "30.00",
            },
            {
                "order_id": ON_TIME_ORDER_ID,
                "payment_sequential": 1,
                "payment_type": "credit_card",
                "payment_installments": 1,
                "payment_value": "10.00",
            },
            {
                "order_id": CANCELED_ORDER_ID,
                "payment_sequential": 1,
                "payment_type": "credit_card",
                "payment_installments": 1,
                "payment_value": "12.00",
            },
        ],
        payment_fields,
    )

    seller_fields = [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
    ]
    _write_csv(
        data_dir / "olist_sellers_dataset.csv",
        [
            {
                "seller_id": "seller-a",
                "seller_zip_code_prefix": "01001",
                "seller_city": "sao paulo",
                "seller_state": "SP",
            },
            {
                "seller_id": "seller-b",
                "seller_zip_code_prefix": "20001",
                "seller_city": "rio de janeiro",
                "seller_state": "RJ",
            },
        ],
        seller_fields,
    )
    return data_dir
