from typing import Generator

import pytest
from fastapi.testclient import TestClient

from examples.app import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    client = TestClient(app)
    yield client
