from typing import Generator

from fastapi.testclient import TestClient

import pytest

from examples.app import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    client = TestClient(app)
    yield client
