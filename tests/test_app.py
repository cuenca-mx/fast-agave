from fastapi.testclient import TestClient


def test_iam_healthy(client: TestClient) -> None:
    resp = client.get('/')
    assert resp.status_code == 200
    assert resp.json() == dict(greeting="I'm healthy!!!")
