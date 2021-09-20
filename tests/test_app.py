from fastapi.testclient import TestClient


def test_iam_healthy(client: TestClient) -> None:
    resp = client.get('/')
    assert resp.status_code == 200
    assert resp.json() == dict(greeting="I'm healthy!!!")


def test_cuenca_error_handler(client: TestClient) -> None:
    resp = client.get('/raise_cuenca_errors')
    assert resp.status_code == 401
    assert resp.json() == dict(error='you are not lucky enough!', code=101)


def test_cuenca_error_handler(client: TestClient) -> None:
    resp = client.get('/raise_cuenca_errors')
    assert resp.status_code == 401
    assert resp.json() == dict(error='you are not lucky enough!', code=101)


def test_fast_agave_error_handler(client: TestClient) -> None:
    resp = client.get('/raise_fast_agave_errors')
    assert resp.status_code == 401
    assert resp.json() == dict(error='nice try!')
