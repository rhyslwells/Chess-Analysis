"""
conftest.py
Shared pytest configuration and fixtures for all test modules.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests that interact with real Chess.com API"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests that take a long time to run"
    )


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that make real API calls"
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests by default unless --run-integration flag is used."""
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(
            reason="need --run-integration option to run"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)