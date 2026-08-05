"""
Data Access Layer (DAL) for Olist CSV datasets.
Read-only, indexed access. Owned by Member 1.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
from src.settings import DATA_DIR


class DataAccessLayer:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = data_dir
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.items_by_order: Dict[str, List[Dict[str, Any]]] = {}
        self.payments_by_order: Dict[str, List[Dict[str, Any]]] = {}
        self.sellers: Dict[str, Dict[str, Any]] = {}

    def load_data(self) -> None:
        """Load and index CSV files."""
        # Member 1 will implement CSV loading and indexing here
        pass

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        return self.orders.get(order_id)

    def get_items(self, order_id: str) -> List[Dict[str, Any]]:
        return self.items_by_order.get(order_id, [])

    def get_payments(self, order_id: str) -> List[Dict[str, Any]]:
        return self.payments_by_order.get(order_id, [])

    def get_seller(self, seller_id: str) -> Optional[Dict[str, Any]]:
        return self.sellers.get(seller_id)
