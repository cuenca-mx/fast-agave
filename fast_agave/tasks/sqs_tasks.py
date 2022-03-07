import asyncio
import json
from functools import wraps
from itertools import count
from typing import Callable, Coroutine

import aiobotocore

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
            session = aiobotocore.session.get_session()
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
