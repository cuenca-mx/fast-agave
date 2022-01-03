import datetime as dt
import os
import subprocess
from functools import partial
from typing import Dict, Generator, List

import aiobotocore
import boto3
import pytest
from _pytest.monkeypatch import MonkeyPatch
from aiobotocore.session import AioSession
from fastapi.testclient import TestClient

from examples.app import app
from examples.models import Account, Card, File
from fast_agave.tasks import sqs_tasks


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    client = TestClient(app)
    yield client


@pytest.fixture
def accounts() -> Generator[List[Account], None, None]:
    user_id = 'US123456789'
    accs = [
        Account(
            name='Frida Kahlo',
            user_id=user_id,
            created_at=dt.datetime(2020, 1, 1),
        ),
        Account(
            name='Sor Juana Inés',
            user_id=user_id,
            created_at=dt.datetime(2020, 2, 1),
        ),
        Account(
            name='Leona Vicario',
            user_id=user_id,
            created_at=dt.datetime(2020, 3, 1),
        ),
        Account(
            name='Remedios Varo',
            user_id='US987654321',
            created_at=dt.datetime(2020, 4, 1),
        ),
    ]

    for acc in accs:
        acc.save()
    yield accs
    for acc in accs:
        acc.delete()


@pytest.fixture
def account(accounts: List[Account]) -> Generator[Account, None, None]:
    yield accounts[0]


@pytest.fixture
def other_account(accounts: List[Account]) -> Generator[Account, None, None]:
    yield accounts[-1]


@pytest.fixture
def files() -> Generator[List[File], None, None]:
    user_id = 'US123456789'
    accs = [
        File(
            name='Frida Kahlo',
            user_id=user_id,
        ),
    ]

    for acc in accs:
        acc.save()
    yield accs
    for acc in accs:
        acc.delete()


@pytest.fixture
def file(files: List[File]) -> Generator[File, None, None]:
    yield files[0]


@pytest.fixture
def cards() -> Generator[List[Card], None, None]:
    user_id = 'US123456789'
    cards = [
        Card(
            number='5434000000000001',
            user_id=user_id,
            created_at=dt.datetime(2020, 1, 1),
        ),
        Card(
            number='5434000000000002',
            user_id=user_id,
            created_at=dt.datetime(2020, 2, 1),
        ),
        Card(
            number='5434000000000003',
            user_id=user_id,
            created_at=dt.datetime(2020, 3, 1),
        ),
        Card(
            number='5434000000000004',
            user_id='US987654321',
            created_at=dt.datetime(2020, 4, 1),
        ),
    ]

    for card in cards:
        card.save()
    yield cards
    for card in cards:
        card.delete()


@pytest.fixture
def card(cards: List[Card]) -> Generator[Card, None, None]:
    yield cards[0]


@pytest.fixture(scope='session')
def aws_credentials() -> None:
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    boto3.setup_default_session()


@pytest.fixture(scope='session')
def aws_endpoint_urls(
    aws_credentials,
) -> Generator[Dict[str, str], None, None]:
    sqs = subprocess.Popen(['moto_server', 'sqs', '-p', '4000'])

    endpoints = dict(
        sqs='http://127.0.0.1:4000/',
    )
    yield endpoints
    sqs.kill()


@pytest.fixture(autouse=True)
def patch_tasks_count(monkeypatch: MonkeyPatch) -> None:
    def one_loop(*_, **__):
        # Para pruebas solo necesitamos un ciclo
        yield 0

    monkeypatch.setattr(sqs_tasks, 'count', one_loop)


@pytest.fixture(autouse=True)
def patch_create_client(aws_endpoint_urls, monkeypatch: MonkeyPatch) -> None:
    create_client = AioSession.create_client

    def mock_create_client(*args, **kwargs):
        service_name = next(a for a in args if type(a) is str)
        kwargs['endpoint_url'] = aws_endpoint_urls[service_name]

        return create_client(*args, **kwargs)

    monkeypatch.setattr(AioSession, 'create_client', mock_create_client)


@pytest.fixture
async def sqs_client():
    session = aiobotocore.session.get_session()
    async with session.create_client('sqs', 'us-east-1') as sqs:
        await sqs.create_queue(
            QueueName='core.fifo', Attributes={'FifoQueue': 'true'}
        )
        resp = await sqs.get_queue_url(QueueName='core.fifo')
        sqs.send_message = partial(sqs.send_message, QueueUrl=resp['QueueUrl'])
        sqs.receive_message = partial(
            sqs.receive_message, QueueUrl=resp['QueueUrl']
        )
        sqs.queue_url = resp['QueueUrl']
        yield sqs
        await sqs.purge_queue(QueueUrl=resp['QueueUrl'])
