"""Pytest configuration and fixtures for neo4j-graph-lib tests."""

import os
import pytest
from unittest.mock import Mock, MagicMock
from neo4j_graph_lib import Neo4jGraphLib
from neo4j_graph_lib.connection import Neo4jConnection


@pytest.fixture(scope="session")
def neo4j_config():
    """Neo4j configuration for tests."""
    return {
        "uri": os.getenv("NEO4J_TEST_URI", "bolt://localhost:7687"),
        "username": os.getenv("NEO4J_TEST_USERNAME", "neo4j"),
        "password": os.getenv("NEO4J_TEST_PASSWORD", "test_password"),
    }


@pytest.fixture(scope="session")
def neo4j_connection(neo4j_config):
    """Real Neo4j connection for integration tests.
    
    Note: This requires a running Neo4j instance.
    Set NEO4J_INTEGRATION_TESTS=true to enable integration tests.
    """
    if not os.getenv("NEO4J_INTEGRATION_TESTS"):
        pytest.skip("Integration tests disabled. Set NEO4J_INTEGRATION_TESTS=true to enable.")
    
    connection = Neo4jConnection(**neo4j_config)
    
    # Test connection
    if not connection.test_connection():
        pytest.skip("Cannot connect to Neo4j. Check your test database configuration.")
    
    yield connection
    
    # Cleanup
    connection.close()


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver for unit tests."""
    mock_driver = Mock()
    mock_session = Mock()
    mock_driver.session.return_value = mock_session
    
    # Mock session context manager
    mock_session.__enter__ = Mock(return_value=mock_session)
    mock_session.__exit__ = Mock(return_value=None)
    
    return mock_driver


@pytest.fixture
def mock_connection(mock_neo4j_driver):
    """Mock Neo4j connection for unit tests."""
    connection = Neo4jConnection("bolt://localhost:7687", "neo4j", "password")
    connection._driver = mock_neo4j_driver
    return connection


@pytest.fixture
def graph_lib(mock_connection):
    """Mock Neo4j graph library instance for unit tests."""
    lib = Neo4jGraphLib("bolt://localhost:7687", "neo4j", "password")
    lib.connection = mock_connection
    return lib


@pytest.fixture
def integration_graph_lib(neo4j_connection):
    """Real Neo4j graph library instance for integration tests."""
    lib = Neo4jGraphLib(
        neo4j_connection.uri,
        neo4j_connection.username,
        neo4j_connection.password
    )
    
    # Clear test database
    lib.connection.execute_write_query("MATCH (n) DETACH DELETE n")
    
    yield lib
    
    # Cleanup after test
    lib.connection.execute_write_query("MATCH (n) DETACH DELETE n")
    lib.connection.close()


@pytest.fixture
def sample_person_data():
    """Sample person data for tests."""
    return {
        "id": "test_person_001",
        "name": "John Doe",
        "age": 30,
        "email": "john.doe@example.com",
        "city": "San Francisco"
    }


@pytest.fixture
def sample_company_data():
    """Sample company data for tests."""
    return {
        "id": "test_company_001",
        "name": "Test Corp",
        "industry": "Technology",
        "size": "Medium",
        "founded": 2010
    }


@pytest.fixture
def sample_relationship_data():
    """Sample relationship data for tests."""
    return {
        "position": "Software Engineer",
        "since": 2020,
        "salary": 100000
    }


# Pytest markers
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add unit marker to unit tests
        if "unit" in item.nodeid or "test_unit" in item.name:
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to integration tests
        if "integration" in item.nodeid or "test_integration" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to slow tests
        if "slow" in item.nodeid or "test_slow" in item.name:
            item.add_marker(pytest.mark.slow)