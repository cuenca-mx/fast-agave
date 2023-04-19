import asyncio
import datetime as dt
import json
import uuid
from unittest.mock import AsyncMock, call, patch

import aiobotocore.client
import pytest
from aiobotocore.httpsession import HTTPClientError

from fast_agave.exc import RetryTask
from fast_agave.tasks.sqs_tasks import get_running_fast_agave_tasks, task

CORE_QUEUE_REGION = 'us-east-1'


@pytest.mark.asyncio
async def test_execute_tasks(sqs_client) -> None:
    """
    Happy path: Se obtiene el mensaje y se ejecuta el task exitosamente.
    El mensaje debe ser eliminado automáticamente del queue
    """
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
    assert async_mock_function.call_count == 1

    resp = await sqs_client.receive_message()
    assert 'Messages' not in resp


@pytest.mark.asyncio
async def test_not_execute_tasks(sqs_client) -> None:
    """
    Este caso es cuando el queue está vacío. No hay nada que ejecutar
    """
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


@pytest.mark.asyncio
async def test_http_client_error_tasks(sqs_client) -> None:
    """
    Este test prueba el caso cuando hay un error de conexión al intentar
    obtener recibir el mensaje del queue. Se maneja correctamente la
    excepción `HTTPClientError` para evitar que el loop que consume mensajes
    se rompe inesperadamente.
    """

    test_message = dict(id='abc123', name='fast-agave')

    await sqs_client.send_message(
        MessageBody=json.dumps(test_message),
        MessageGroupId='1234',
    )

    original_create_client = aiobotocore.client.AioClientCreator.create_client

    # Esta función hace un patch de la función `receive_message` para simular
    # un error de conexión, la recuperación de la conexión y posteriores
    # recepciones de mensajes sin body del queue.
    async def mock_create_client(*args, **kwargs):
        client = await original_create_client(*args, **kwargs)
        client.receive_message = AsyncMock(
            side_effect=[
                HTTPClientError(error='[Errno 104] Connection reset by peer'),
                await sqs_client.receive_message(),
                dict(),
                dict(),
                dict(),
            ]
        )
        return client

    async_mock_function = AsyncMock(return_value=None)
    with patch(
        'aiobotocore.client.AioClientCreator.create_client', mock_create_client
    ):
        await task(
            queue_url=sqs_client.queue_url,
            region_name=CORE_QUEUE_REGION,
            wait_time_seconds=1,
            visibility_timeout=3,
            max_retries=1,
        )(async_mock_function)()
        async_mock_function.assert_called_once()


@pytest.mark.asyncio
async def test_retry_tasks_default_max_retries(sqs_client) -> None:
    """
    Este test prueba la lógica de reintentos con la configuración default,
    es decir `max_retries=1`

    En este caso el task debe ejecutarse 2 veces
    (la ejecución normal + max_retries)

    Se ejecuta este número de veces para ser consistentes con la lógica
    de reintentos de Celery
    """
    test_message = dict(id='abc123', name='fast-agave')

    await sqs_client.send_message(
        MessageBody=json.dumps(test_message),
        MessageGroupId='1234',
    )

    async_mock_function = AsyncMock(side_effect=RetryTask)

    await task(
        queue_url=sqs_client.queue_url,
        region_name=CORE_QUEUE_REGION,
        wait_time_seconds=1,
        visibility_timeout=1,
    )(async_mock_function)()

    expected_calls = [call(test_message)] * 2
    async_mock_function.assert_has_calls(expected_calls)
    assert async_mock_function.call_count == len(expected_calls)

    resp = await sqs_client.receive_message()
    assert 'Messages' not in resp


@pytest.mark.asyncio
async def test_retry_tasks_custom_max_retries(sqs_client) -> None:
    """
    Este test prueba la lógica de reintentos con la configuración default,
    es decir `max_retries=3`

    En este caso el task debe ejecutarse 4 veces
    (la ejecución normal + max_retries)
    """
    test_message = dict(id='abc123', name='fast-agave')
    await sqs_client.send_message(
        MessageBody=json.dumps(test_message),
        MessageGroupId='1234',
    )

    async_mock_function = AsyncMock(side_effect=RetryTask)

    await task(
        queue_url=sqs_client.queue_url,
        region_name=CORE_QUEUE_REGION,
        wait_time_seconds=1,
        visibility_timeout=1,
        max_retries=3,
    )(async_mock_function)()

    expected_calls = [call(test_message)] * 4
    async_mock_function.assert_has_calls(expected_calls)
    assert async_mock_function.call_count == len(expected_calls)

    resp = await sqs_client.receive_message()
    assert 'Messages' not in resp


@pytest.mark.asyncio
async def test_does_not_retry_on_unhandled_exceptions(sqs_client) -> None:
    """
    Este caso prueba que las excepciones no controladas no se reintentan por
    default (comportamiento consistente con Celery)

    Dentro de task deben manejarse las excepciones esperadas (como desconexión
    de la red). Véase los ejemplos de cómo aplicar este tipo de reintentos
    """
    test_message = dict(id='abc123', name='fast-agave')
    await sqs_client.send_message(
        MessageBody=json.dumps(test_message),
        MessageGroupId='1234',
    )

    async_mock_function = AsyncMock(
        side_effect=Exception('something went wrong :(')
    )

    await task(
        queue_url=sqs_client.queue_url,
        region_name=CORE_QUEUE_REGION,
        wait_time_seconds=1,
        visibility_timeout=1,
        max_retries=3,
    )(async_mock_function)()

    async_mock_function.assert_called_with(test_message)
    assert async_mock_function.call_count == 1

    resp = await sqs_client.receive_message()
    assert 'Messages' not in resp


@pytest.mark.asyncio
async def test_retry_tasks_with_countdown(sqs_client) -> None:
    """
    Este test prueba la lógica de reintentos con la configuración default,
    es decir `max_retries=1`

    En este caso el task debe ejecutarse 2 veces
    (la ejecución normal + max_retries)

    Se ejecuta este número de veces para ser consistentes con la lógica
    de reintentos de Celery
    """
    test_message = dict(id='abc123', name='fast-agave')

    await sqs_client.send_message(
        MessageBody=json.dumps(test_message),
        MessageGroupId='1234',
    )

    call_times = []

    async def countdown_tester(_):
        call_times.append(dt.datetime.now())
        raise RetryTask(countdown=2)

    await task(
        queue_url=sqs_client.queue_url,
        region_name=CORE_QUEUE_REGION,
        wait_time_seconds=1,
        visibility_timeout=1,
    )(countdown_tester)()

    assert len(call_times) == 2
    assert call_times[1] - call_times[0] >= dt.timedelta(seconds=2)
    resp = await sqs_client.receive_message()
    assert 'Messages' not in resp


@pytest.mark.asyncio
async def test_concurrency_controller(
    sqs_client,
) -> None:
    message_id = str(uuid.uuid4())
    test_message = dict(id=message_id, name='fast-agave')
    for i in range(5):
        await sqs_client.send_message(
            MessageBody=json.dumps(test_message),
            MessageGroupId=message_id,
        )

    max_running_tasks = 0

    async def task_counter(_) -> None:
        nonlocal max_running_tasks
        await asyncio.sleep(1)
        running_tasks = len(await get_running_fast_agave_tasks())
        if running_tasks > max_running_tasks:
            max_running_tasks = running_tasks

    await task(
        queue_url=sqs_client.queue_url,
        region_name=CORE_QUEUE_REGION,
        wait_time_seconds=1,
        visibility_timeout=1,
        max_retries=3,
        max_concurrent_tasks=2,
    )(task_counter)()

    assert max_running_tasks == 2
