import datetime as dt
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient

from examples.models import Account, Card, File

USER_ID_FILTER_REQUIRED = (
    'examples.middlewares.AuthedMiddleware.required_user_id'
)


def test_create_resource(client: TestClient) -> None:
    data = dict(name='Doroteo Arango')
    resp = client.post('/accounts', json=data)
    json_body = resp.json()
    model = Account.objects.get(id=json_body['id'])
    assert resp.status_code == 201
    assert model.to_dict() == json_body
    model.delete()


def test_create_resource_bad_request(client: TestClient) -> None:
    data = dict(invalid_field='some value')
    resp = client.post('/accounts', json=data)
    assert resp.status_code == 422


def test_retrieve_resource(client: TestClient, account: Account) -> None:
    resp = client.get(f'/accounts/{account.id}')
    assert resp.status_code == 200
    assert resp.json() == account.to_dict()


@patch(USER_ID_FILTER_REQUIRED, MagicMock(return_value=True))
def test_retrieve_resource_user_id_filter_required(
    client: TestClient, other_account: Account
) -> None:
    resp = client.get(f'/accounts/{other_account.id}')
    assert resp.status_code == 404


def test_retrieve_resource_not_found(client: TestClient) -> None:
    resp = client.get('/accounts/unknown_id')
    assert resp.status_code == 404


def test_update_resource_with_invalid_params(client: TestClient) -> None:
    wrong_params = dict(wrong_param='wrong_value')
    response = client.patch(
        '/accounts/NOT_EXISTS',
        json=wrong_params,
    )
    assert response.status_code == 400


def test_retrieve_custom_method(client: TestClient, card: Card) -> None:
    resp = client.get(f'/cards/{card.id}')
    assert resp.status_code == 200
    assert resp.json()['number'] == '*' * 16


def test_update_resource_that_doesnt_exist(client: TestClient) -> None:
    resp = client.patch(
        '/accounts/5f9b4d0ff8d7255e3cc3c128',
        json=dict(name='Frida'),
    )
    assert resp.status_code == 404


def test_update_resource(client: TestClient, account: Account) -> None:
    resp = client.patch(
        f'/accounts/{account.id}',
        json=dict(name='Maria Felix'),
    )
    account.reload()
    assert resp.json()['name'] == 'Maria Felix'
    assert account.name == 'Maria Felix'
    assert resp.status_code == 200


def test_delete_resource(client: TestClient, account: Account) -> None:
    resp = client.delete(f'/accounts/{account.id}')
    account.reload()
    assert resp.status_code == 200
    assert resp.json()['deactivated_at'] is not None
    assert account.deactivated_at is not None


@pytest.mark.usefixtures('accounts')
def test_query_count_resource(client: TestClient) -> None:
    query_params = dict(count=1, name='Frida Kahlo')
    response = client.get(
        f'/accounts?{urlencode(query_params)}',
    )
    assert response.status_code == 200
    assert response.json()['count'] == 1


@pytest.mark.usefixtures('accounts')
def test_query_all_with_limit(client: TestClient) -> None:
    limit = 2
    query_params = dict(limit=limit)
    response = client.get(f'/accounts?{urlencode(query_params)}')
    json_body = response.json()
    assert response.status_code == 200
    assert len(json_body['items']) == limit
    assert json_body['next_page_uri'] is None


@pytest.mark.usefixtures('accounts')
def test_query_all_resource(client: TestClient) -> None:
    query_params = dict(page_size=2)
    resp = client.get(f'/accounts?{urlencode(query_params)}')
    json_body = resp.json()
    assert resp.status_code == 200
    assert len(json_body['items']) == 2

    resp = client.get(json_body['next_page_uri'])
    assert resp.status_code == 200
    assert len(json_body['items']) == 2


@pytest.mark.usefixtures('accounts')
def test_query_all_created_after(client: TestClient) -> None:
    query_params = dict(created_after=dt.datetime(2020, 2, 1).isoformat())
    resp = client.get(f'/accounts?{urlencode(query_params)}')
    json_body = resp.json()
    assert resp.status_code == 200
    assert len(json_body['items']) == 2


@pytest.mark.usefixtures('accounts')
@patch(USER_ID_FILTER_REQUIRED, MagicMock(return_value=True))
def test_query_user_id_filter_required(client: TestClient) -> None:
    query_params = dict(page_size=2)
    resp = client.get(f'/accounts?{urlencode(query_params)}')
    json_body = resp.json()
    assert resp.status_code == 200
    assert len(json_body['items']) == 2
    assert all(item['user_id'] == 'US123456789' for item in json_body['items'])

    resp = client.get(json_body['next_page_uri'])
    json_body = resp.json()
    assert resp.status_code == 200
    assert len(json_body['items']) == 1
    assert all(item['user_id'] == 'US123456789' for item in json_body['items'])


def test_query_resource_with_invalid_params(client: TestClient) -> None:
    wrong_params = dict(wrong_param='wrong_value')
    response = client.get(f'/accounts?{urlencode(wrong_params)}')
    assert response.status_code == 400


@pytest.mark.usefixtures('cards')
def test_query_custom_method(client: TestClient) -> None:
    query_params = dict(page_size=2)
    resp = client.get(f'/cards?{urlencode(query_params)}')
    json_body = resp.json()
    assert resp.status_code == 200
    assert len(json_body['items']) == 2
    assert all(card['number'] == '*' * 16 for card in json_body['items'])

    resp = client.get(json_body['next_page_uri'])
    json_body = resp.json()
    assert resp.status_code == 200
    assert len(json_body['items']) == 2
    assert all(card['number'] == '*' * 16 for card in json_body['items'])


def test_cannot_query_resource(client: TestClient) -> None:
    query_params = dict(count=1, name='Frida Kahlo')
    response = client.get(
        f'/transactions?{urlencode(query_params)}',
    )
    assert response.status_code == 405


def test_cannot_create_resource(client: TestClient) -> None:
    response = client.post('/transactions', json=dict())
    assert response.status_code == 405


def test_cannot_update_resource(client: TestClient) -> None:
    response = client.post('/transactions', json=dict())
    assert response.status_code == 405


def test_cannot_delete_resource(client: TestClient) -> None:
    resp = client.delete('/transactions/TR1234')
    assert resp.status_code == 405


def test_download_resource(client: TestClient, file: File) -> None:
    mimetype = 'application/pdf'
    resp = client.get(f'/files/{file.id}', headers={'Accept': mimetype})
    assert resp.status_code == 200
    assert resp.headers.get('Content-Type') == mimetype
