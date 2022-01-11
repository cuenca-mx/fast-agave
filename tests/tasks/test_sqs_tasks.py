import json
from unittest.mock import AsyncMock

import pytest

from fast_agave.tasks.sqs_tasks import task

CORE_QUEUE_REGION = 'us-east-1'


@pytest.mark.asyncio
async def test_execute_tasks(sqs_client) -> None:
    test_message = dict(id='abc123', name='fast-agave')

    await sqs_client.send_message(
        MessageBody=json.dumps(test_message),
        MessageGroupId='1234',
    )

    async_mock_function = AsyncMock(return_value=None)
    await task(
        queue_url=sqs_client.queue_url,
        region_name=CORE_QUEUE_REGION,
        wait_time_seconds=1,
        visibility_timeout=1,
    )(async_mock_function)()
    async_mock_function.assert_called_with(test_message)

    resp = await sqs_client.receive_message()
    assert 'Messages' not in resp


@pytest.mark.asyncio
async def test_not_execute_tasks(sqs_client) -> None:
    async_mock_function = AsyncMock(return_value=None)
    # No escribimos un mensaje en el queue
    await task(
        queue_url=sqs_client.queue_url,
        region_name=CORE_QUEUE_REGION,
        wait_time_seconds=1,
        visibility_timeout=1,
    )(async_mock_function)()
    async_mock_function.assert_not_called()
    resp = await sqs_client.receive_message()
    assert 'Messages' not in resp
