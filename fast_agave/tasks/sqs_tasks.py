import asyncio
import json
from functools import wraps
from itertools import count
from typing import Callable, Coroutine

import aiobotocore


async def run_task(
    coro: Coroutine,
    sqs,
    queue_url: str,
    receipe_handle: str,
) -> None:
    await coro
    await sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipe_handle,
    )


def task(
    queue_url: str,
    region_name: str,
    wait_time_seconds: int = 15,
    visibility_timeout: int = 3600,
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
                    )
                    try:
                        messages = response['Messages']
                    except KeyError:
                        continue

                    for message in messages:
                        body = json.loads(message['Body'])
                        asyncio.create_task(
                            run_task(
                                task_func(body),
                                sqs,
                                queue_url,
                                message['ReceiptHandle'],
                            )
                        )

        return start_task

    return task_builder
