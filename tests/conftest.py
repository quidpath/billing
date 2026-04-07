"""
Conftest for billing integration tests
"""
import pytest


@pytest.fixture
def billing_url():
    return "http://localhost:8002"
