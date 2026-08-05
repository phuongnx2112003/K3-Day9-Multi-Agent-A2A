"""Read-only, indexed access to the Olist datasets used by the agents."""

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.settings import DATA_DIR


class DataAccessLayer:
    DATASETS = {
        "orders": "olist_orders_dataset.csv",
        "items": "olist_order_items_dataset.csv",
        "payments": "olist_order_payments_dataset.csv",
        "sellers": "olist_sellers_dataset.csv",
    }

    REQUIRED_COLUMNS = {
        "orders": {
            "order_id",
            "order_status",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        },
        "items": {
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        },
        "payments": {
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        },
        "sellers": {"seller_id"},
    }

    DTYPES = {
        "orders": {
            "order_id": "string",
            "customer_id": "string",
            "order_status": "string",
            "order_purchase_timestamp": "string",
            "order_approved_at": "string",
            "order_delivered_carrier_date": "string",
            "order_delivered_customer_date": "string",
            "order_estimated_delivery_date": "string",
        },
        "items": {
            "order_id": "string",
            "order_item_id": "int64",
            "product_id": "string",
            "seller_id": "string",
            "shipping_limit_date": "string",
            "price": "float64",
            "freight_value": "float64",
        },
        "payments": {
            "order_id": "string",
            "payment_sequential": "int64",
            "payment_type": "string",
            "payment_installments": "int64",
            "payment_value": "float64",
        },
        "sellers": {
            "seller_id": "string",
            "seller_zip_code_prefix": "string",
            "seller_city": "string",
            "seller_state": "string",
        },
    }

    def __init__(self, data_dir: Path | str = DATA_DIR):
        self.data_dir = Path(data_dir)
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.items_by_order: Dict[str, List[Dict[str, Any]]] = {}
        self.payments_by_order: Dict[str, List[Dict[str, Any]]] = {}
        self.sellers: Dict[str, Dict[str, Any]] = {}
        self.is_loaded = False

    def load_data(self) -> None:
        """Load and index required CSV files without leaving partial state."""
        paths = {
            name: self.data_dir / filename
            for name, filename in self.DATASETS.items()
        }
        missing = [str(path) for path in paths.values() if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"Missing required Olist datasets: {', '.join(missing)}")

        frames = {
            name: self._read_dataset(name, path)
            for name, path in paths.items()
        }

        orders = self._index_unique(frames["orders"], "order_id", "orders")
        sellers = self._index_unique(frames["sellers"], "seller_id", "sellers")
        items_by_order = self._index_many(
            frames["items"], "order_id", sort_key="order_item_id"
        )
        payments_by_order = self._index_many(
            frames["payments"], "order_id", sort_key="payment_sequential"
        )

        self.orders = orders
        self.items_by_order = items_by_order
        self.payments_by_order = payments_by_order
        self.sellers = sellers
        self.is_loaded = True

    def _read_dataset(self, name: str, path: Path) -> pd.DataFrame:
        frame = pd.read_csv(path, dtype=self.DTYPES[name])
        missing_columns = self.REQUIRED_COLUMNS[name] - set(frame.columns)
        if missing_columns:
            columns = ", ".join(sorted(missing_columns))
            raise ValueError(f"Dataset {path.name} is missing columns: {columns}")

        # Convert pandas NA values to plain None before crossing agent boundaries.
        return frame.astype(object).where(pd.notna(frame), None)

    @staticmethod
    def _index_unique(
        frame: pd.DataFrame, key: str, dataset_name: str
    ) -> Dict[str, Dict[str, Any]]:
        if frame[key].isna().any():
            raise ValueError(f"Dataset {dataset_name} contains an empty {key}")
        duplicates = frame[key][frame[key].duplicated()].unique().tolist()
        if duplicates:
            raise ValueError(
                f"Dataset {dataset_name} contains duplicate {key}: {duplicates[0]}"
            )
        return {str(row[key]): row for row in frame.to_dict(orient="records")}

    @staticmethod
    def _index_many(
        frame: pd.DataFrame, key: str, sort_key: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        if frame[key].isna().any():
            raise ValueError(f"Dataset contains an empty {key}")

        indexed: Dict[str, List[Dict[str, Any]]] = {}
        for row in frame.to_dict(orient="records"):
            indexed.setdefault(str(row[key]), []).append(row)
        for rows in indexed.values():
            rows.sort(key=lambda row: row[sort_key])
        return indexed

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        order = self.orders.get(order_id)
        return deepcopy(order) if order is not None else None

    def get_items(self, order_id: str) -> List[Dict[str, Any]]:
        return deepcopy(self.items_by_order.get(order_id, []))

    def get_payments(self, order_id: str) -> List[Dict[str, Any]]:
        return deepcopy(self.payments_by_order.get(order_id, []))

    def get_seller(self, seller_id: str) -> Optional[Dict[str, Any]]:
        seller = self.sellers.get(seller_id)
        return deepcopy(seller) if seller is not None else None
