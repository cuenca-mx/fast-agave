from fast_agave.tasks.sqs_tasks import task
from fast_agave.exc import RetryTask


# Esta URL es solo un mock de la queue.
# Debes reemplazarla con la URL de tu queue
QUEUE_URL = 'http://127.0.0.1:4000/123456789012/core.fifo'


@task(queue_url=QUEUE_URL, region_name='us-east-1', max_retry=2)
async def dummy_retry_task(message) -> None:
    """This task will retry twice"""
    print(message)
    raise RetryTask()
