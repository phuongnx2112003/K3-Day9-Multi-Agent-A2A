"""Behavioral tests for the read-only Data Access Layer."""

from pathlib import Path

import pytest

from src.data_access import DataAccessLayer
from tests.member1_fixtures import CANCELED_ORDER_ID, LATE_ORDER_ID, write_member1_dataset


@pytest.fixture
def loaded_dal(tmp_path: Path) -> DataAccessLayer:
    dal = DataAccessLayer(write_member1_dataset(tmp_path / "data"))
    dal.load_data()
    return dal


def test_loads_and_indexes_required_datasets(loaded_dal: DataAccessLayer):
    assert loaded_dal.is_loaded is True
    assert len(loaded_dal.orders) == 3
    assert [row["order_item_id"] for row in loaded_dal.get_items(LATE_ORDER_ID)] == [1, 2]
    assert [row["payment_sequential"] for row in loaded_dal.get_payments(LATE_ORDER_ID)] == [1, 2]
    assert loaded_dal.get_seller("seller-a")["seller_zip_code_prefix"] == "01001"
    assert loaded_dal.get_order(CANCELED_ORDER_ID)["order_delivered_customer_date"] is None


def test_returns_copies_instead_of_mutable_index_records(loaded_dal: DataAccessLayer):
    order = loaded_dal.get_order(LATE_ORDER_ID)
    items = loaded_dal.get_items(LATE_ORDER_ID)
    order["order_status"] = "changed"
    items[0]["price"] = 999

    assert loaded_dal.get_order(LATE_ORDER_ID)["order_status"] == "delivered"
    assert loaded_dal.get_items(LATE_ORDER_ID)[0]["price"] == 10.10


def test_missing_dataset_fails_without_partial_state(tmp_path: Path):
    data_dir = write_member1_dataset(tmp_path / "data")
    (data_dir / "olist_sellers_dataset.csv").unlink()
    dal = DataAccessLayer(data_dir)

    with pytest.raises(FileNotFoundError, match="olist_sellers_dataset.csv"):
        dal.load_data()

    assert dal.is_loaded is False
    assert dal.orders == {}


def test_missing_required_column_is_rejected(tmp_path: Path):
    data_dir = write_member1_dataset(tmp_path / "data")
    path = data_dir / "olist_orders_dataset.csv"
    path.write_text("order_id,order_status\norder-1,delivered\n", encoding="utf-8")

    with pytest.raises(ValueError, match="order_estimated_delivery_date"):
        DataAccessLayer(data_dir).load_data()
