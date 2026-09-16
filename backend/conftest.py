"""
Pytest configuration for TICKBRON backend tests.

This file contains pytest fixtures and configuration for reproducible testing.
"""
import pytest
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set Django settings module for pytest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


@pytest.fixture(scope='session')
def django_db_setup():
    """
    Set up the test database for the entire test session.
    This ensures database is created once and reused across tests.
    """
    pass


@pytest.fixture(scope='function')
def test_db():
    """
    Provide a clean database for each test function.
    Tests are isolated and database is cleaned up after each test.
    """
    pass


@pytest.fixture
def sample_system_settings():
    """
    Provide sample system settings data for testing.
    """
    return {
        'key': 'test_setting',
        'value': 'test_value',
        'description': 'Test setting for unit tests'
    }
