"""
Pytest configuration and shared fixtures
"""

import pytest


# Configure pytest-asyncio if available
def pytest_configure(config):
    """Configure pytest with asyncio settings."""
    config.addinivalue_line("markers", "asyncio: mark test as async")


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for async tests."""
    import asyncio

    return asyncio.DefaultEventLoopPolicy()
