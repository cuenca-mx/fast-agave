import json
from dataclasses import asdict
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from cuenca_validations.errors import WrongCredsError
from fastapi.testclient import TestClient

from examples.models import Card
from fast_agave.exc import UnauthorizedError
from tests.helpers import auth_header


@pytest.fixture(autouse=True)
def patch_log_server_url(monkeypatch):
    monkeypatch.setenv('LOGS_SERVER_URL', 'http://logs.com')
    # with patch(
    #     'fast_agave.middlewares.loggers.LOGS_SERVER_URL', 'http://logs.com'
    # ):
    #     yield


@patch('aiohttp.client.ClientSession.put')
def test_doesnt_log_sensitive_data_in_headers(
    mock_put: MagicMock, client: TestClient
) -> None:
    token = 'TK123456789'
    login_token = 'LT123456789'
    login_id = 'LI123456789'
    session_id = 'SS123456789'
    auth = auth_header('AK123', 'secret')

    auth['X-Cuenca-Token'] = token
    auth['X-Cuenca-LoginToken'] = login_token
    auth['X-Cuenca-LoginId'] = login_id
    auth['X-Cuenca-SessionId'] = session_id

    resp = client.get('/accounts', headers=auth)
    assert resp.status_code == 200
    assert type(mock_put.call_args.kwargs['json']) is dict

    # makes it easy to search for specifics string instead
    # of searching in each key and document level
    data_as_str = json.dumps(mock_put.call_args.kwargs['json'])

    assert 'AK123' in data_as_str
    assert 'secret' not in data_as_str
    assert token not in data_as_str
    assert login_token not in data_as_str
    assert login_id not in data_as_str


@patch('aiohttp.client.ClientSession.put')
def test_log_fake_basic_auth_data_in_headers(
    mock_put: MagicMock, client: TestClient
) -> None:
    resp = client.get(
        '/accounts', headers={'Authorization': 'Basic malformed-token'}
    )
    assert resp.status_code == 200
    assert type(mock_put.call_args.kwargs['json']) is dict

    # makes it easy to search for specifics string instead
    # of searching in each key and document level
    data_as_str = json.dumps(mock_put.call_args.kwargs['json'])

    assert 'malformed-token' in data_as_str


@patch('aiohttp.client.ClientSession.put')
def test_doesnt_log_sensitive_data_in_query_response_body(
    mock_put: MagicMock, client: TestClient, cards: List[Card]
) -> None:
    resp = client.get('/cards')
    assert resp.status_code == 200
    assert type(mock_put.call_args.kwargs['json']) is dict

    data_as_str = json.dumps(mock_put.call_args.kwargs['json'])

    assert not any(c.number in data_as_str for c in cards)
    assert not any(str(c.exp_year) in data_as_str for c in cards)
    assert all(c.user_id in data_as_str for c in cards)


@pytest.mark.parametrize('method', ['get', 'delete'])
@patch('aiohttp.client.ClientSession.put')
def test_doesnt_log_sensitive_data_in_response_body(
    mock_put: MagicMock, client: TestClient, card: Card, method: str
) -> None:
    client_method = getattr(client, method)
    resp = client_method(f'/cards/{card.id}')
    assert resp.status_code == 200

    data_as_str = json.dumps(mock_put.call_args.kwargs['json'])
    assert card.number not in data_as_str
    assert card.user_id in data_as_str


@patch('aiohttp.client.ClientSession.put')
def test_doesnt_log_sensitive_data_in_patch_response_body(
    mock_put: MagicMock, client: TestClient, card: Card
) -> None:
    resp = client.patch(f'/cards/{card.id}', json=dict(status='deactivated'))
    assert resp.status_code == 200

    data_as_str = json.dumps(mock_put.call_args.kwargs['json'])
    assert card.number not in data_as_str
    assert card.user_id in data_as_str


@patch('aiohttp.client.ClientSession.put')
def test_logs_non_dict_response_bodies(
    mock_put: MagicMock, client: TestClient
) -> None:
    resp = client.get('/hello')
    assert resp.status_code == 200
    log_data = mock_put.call_args.kwargs['json']
    assert log_data['response_body'] == 'hello!'


@patch('aiohttp.client.ClientSession.put')
def test_logs_agave_error_response_bodies(
    mock_put: MagicMock, client: TestClient
) -> None:
    resp = client.get('/raise_fast_agave_errors')
    assert resp.status_code == 401
    expected_exc = UnauthorizedError('nice try!')
    log_data = mock_put.call_args.kwargs['json']
    assert log_data['response_body'] == asdict(expected_exc)


@patch('aiohttp.client.ClientSession.put')
def test_logs_cuenca_error_response_bodies(
    mock_put: MagicMock, client: TestClient
) -> None:
    resp = client.get('/raise_cuenca_errors')
    assert resp.status_code == 401
    expected_exc = WrongCredsError('you are not lucky enough!')
    log_data = mock_put.call_args.kwargs['json']
    assert log_data['response_body'] == dict(
        status_code=expected_exc.status_code, code='you are not lucky enough!'
    )
