from fastapi.testclient import TestClient


def test_retrieve_resource(client: TestClient) -> None:
    resp = client.get(f'/accounts/123')
    assert resp.status_code == 200
    assert resp.json() == dict(id='123')
