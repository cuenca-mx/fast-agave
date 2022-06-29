import asyncio
import json
from base64 import b64encode
from dataclasses import dataclass
from functools import wraps
from itertools import count
from typing import Callable, Coroutine, Optional
from uuid import uuid4

from aiobotocore.session import get_session
from cuenca_validations.typing import DictStrAny

from ..exc import RetryTask


async def run_task(
    coro: Coroutine,
    sqs,
    queue_url: str,
    receipt_handle: str,
    message_receive_count: int,
    max_retries: int,
) -> None:
    delete_message = True
    try:
        await coro
    except RetryTask:
        delete_message = message_receive_count >= max_retries + 1
    finally:
        if delete_message:
            await sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle,
            )


def task(
    queue_url: str,
    region_name: str,
    wait_time_seconds: int = 15,
    visibility_timeout: int = 3600,
    max_retries: int = 1,
):
    def task_builder(task_func: Callable):
        @wraps(task_func)
        async def start_task(*args, **kwargs) -> None:
            session = get_session()
            async with session.create_client('sqs', region_name) as sqs:
                for _ in count():
                    response = await sqs.receive_message(
                        QueueUrl=queue_url,
                        WaitTimeSeconds=wait_time_seconds,
                        VisibilityTimeout=visibility_timeout,
                        AttributeNames=['ApproximateReceiveCount'],
                    )
                    try:
                        messages = response['Messages']
                    except KeyError:
                        continue

                    for message in messages:
                        body = json.loads(message['Body'])
                        message_receive_count = int(
                            message['Attributes']['ApproximateReceiveCount']
                        )
                        asyncio.create_task(
                            run_task(
                                task_func(body),
                                sqs,
                                queue_url,
                                message['ReceiptHandle'],
                                message_receive_count,
                                max_retries,
                            )
                        )

        return start_task

    return task_builder


def _build_celery_message(task: str, data: DictStrAny) -> str:
    task_id = str(uuid4())
    # la definición de esta plantila se encuentra en:
    # docs.celeryproject.org/en/stable/internals/protocol.html#definition
    message = dict(
        properties=dict(
            correlation_id=task_id,
            content_type='application/json',
            content_encoding='utf-8',
            body_encoding='base64',
            delivery_info=dict(exchange='', routing_key='celery'),
        ),
        headers=dict(
            lang='py',
            task=task,
            id=task_id,
            root_id=task_id,
            parent_id=None,
            group=None,
        ),
        body=_b64_encode(
            json.dumps(
                (
                    (),
                    data,
                    dict(
                        callbacks=None, errbacks=None, chain=None, chord=None
                    ),
                )
            )
        ),
    )
    message['content-encoding'] = 'utf-8'
    message['content-type'] = 'application/json'

    encoded = _b64_encode(json.dumps(message))
    return encoded


def _b64_encode(value: str) -> str:
    encoded = b64encode(bytes(value, 'utf-8'))
    return encoded.decode('utf-8')


@dataclass
class Queue:
    queue_url: str
    region_name: str

    async def send_task(
        self, message: DictStrAny, message_group_id: Optional[str] = None
    ) -> None:
        session = get_session()
        async with session.create_client('sqs', self.region_name) as sqs:
            await sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message),
                MessageGroupId=message_group_id,
            )

    async def send_task_as_celery(
        self,
        task: str,
        message: DictStrAny,
        message_group_id: Optional[str] = None,
    ) -> None:
        celery_message = _build_celery_message(task, message)
        session = get_session()
        async with session.create_client('sqs', self.region_name) as sqs:
            await sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=celery_message,
                MessageGroupId=message_group_id,
            )
