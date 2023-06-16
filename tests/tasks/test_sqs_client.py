import json

import pytest

from fast_agave.tasks.sqs_client import SqsClient

CORE_QUEUE_REGION = 'us-east-1'


@pytest.mark.asyncio
async def test_send_task(sqs_client) -> None:
    queue = SqsClient(sqs_client.queue_url, CORE_QUEUE_REGION)
    await queue.start()

    data1 = dict(hola='mundo')
    data2 = dict(foo='bar')
    await queue.send_task(data1)
    await queue.send_task(data2, message_group_id='12345')

    sqs_message = await sqs_client.receive_message()
    message = json.loads(sqs_message['Messages'][0]['Body'])
    assert message == data1

    sqs_message = await sqs_client.receive_message()
    message = json.loads(sqs_message['Messages'][0]['Body'])
    assert message == data2
    await queue.close()


@pytest.mark.asyncio
async def test_send_background_task(sqs_client) -> None:
    queue = SqsClient(sqs_client.queue_url, CORE_QUEUE_REGION)
    await queue.start()

    data1 = dict(hola='mundo')

    task = queue.send_background_task(data1)
    await task
    sqs_message = await sqs_client.receive_message()
    message = json.loads(sqs_message['Messages'][0]['Body'])
    assert message == data1

    await queue.close()
