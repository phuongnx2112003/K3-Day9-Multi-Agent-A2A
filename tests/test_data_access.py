"""
Unit tests for Data Access Layer (DAL). Owned by Member 1.
"""
import pytest
from src.data_access import DataAccessLayer


def test_dal_initialization():
    dal = DataAccessLayer()
    assert dal is not None
