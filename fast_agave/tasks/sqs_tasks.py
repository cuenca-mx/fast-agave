import asyncio
import json
from functools import wraps
from itertools import count
from typing import AsyncGenerator, Callable, Coroutine

from aiobotocore.httpsession import HTTPClientError
from aiobotocore.session import get_session

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


async def message_consumer(
    queue_url: str,
    wait_time_seconds: int,
    visibility_timeout: int,
    can_read: asyncio.Event,
    sqs,
) -> AsyncGenerator:
    for _ in count():
        print(f'esperando {can_read = }')
        await can_read.wait()
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
        except HTTPClientError:
            await asyncio.sleep(1)
            continue
        for message in messages:
            yield message


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
            can_read = asyncio.Event()
            concurrency_lock = asyncio.Lock()
            max_running_tasks = 5
            running_tasks = 0
            session = get_session()

            can_read.set()

            async def concurrency_controller(coro):
                async with concurrency_lock:
                    nonlocal running_tasks
                    running_tasks += 1
                    print(f'{max_running_tasks = }')
                    print(f'incrementando {running_tasks = }')
                    if running_tasks <= max_running_tasks:
                        can_read.set()
                    else:
                        can_read.clear()

                await coro

                async with concurrency_lock:
                    running_tasks -= 1
                    can_read.set()
                    print(f'decrementando {running_tasks = }')

            async with session.create_client('sqs', region_name) as sqs:
                async for message in message_consumer(
                    queue_url,
                    wait_time_seconds,
                    visibility_timeout,
                    can_read,
                    sqs,
                ):
                    body = json.loads(message['Body'])
                    message_receive_count = int(
                        message['Attributes']['ApproximateReceiveCount']
                    )
                    asyncio.create_task(
                        concurrency_controller(
                            run_task(
                                task_func(body),
                                sqs,
                                queue_url,
                                message['ReceiptHandle'],
                                message_receive_count,
                                max_retries,
                            )
                        )
                    )

        return start_task

    return task_builder


# def task(
#     queue_url: str,
#     region_name: str,
#     wait_time_seconds: int = 15,
#     visibility_timeout: int = 3600,
#     max_retries: int = 1,
# ):
#     def task_builder(task_func: Callable):
#         @wraps(task_func)
#         async def start_task(*args, **kwargs) -> None:
#             session = get_session()
#             async with session.create_client('sqs', region_name) as sqs:
#                 for _ in count():
#                     response = await sqs.receive_message(
#                         QueueUrl=queue_url,
#                         WaitTimeSeconds=wait_time_seconds,
#                         VisibilityTimeout=visibility_timeout,
#                         AttributeNames=['ApproximateReceiveCount'],
#                     )
#                     try:
#                         messages = response['Messages']
#                     except KeyError:
#                         continue
#
#                     for message in messages:
#                         body = json.loads(message['Body'])
#                         message_receive_count = int(
#                             message['Attributes']['ApproximateReceiveCount']
#                         )
#                         asyncio.create_task(
#                             run_task(
#                                 task_func(body),
#                                 sqs,
#                                 queue_url,
#                                 message['ReceiptHandle'],
#                                 message_receive_count,
#                                 max_retries,
#                             )
#                         )
#
#         return start_task
#
#     return task_builder
