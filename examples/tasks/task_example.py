from typing import Optional

from fast_agave.tasks.sqs_tasks import task

from pydantic import BaseModel

# Esta URL es solo un mock de la queue.
# Debes reemplazarla con la URL de tu queue
QUEUE_URL = 'http://127.0.0.1:4000/123456789012/core.fifo'
QUEUE2_URL = 'http://127.0.0.1:4000/123456789012/validator.fifo'


class ValidatorModel(BaseModel):
    name: str
    age: int
    nick_name: Optional[str]


@task(queue_url=QUEUE_URL, region_name='us-east-1')
async def dummy_task(message) -> None:
    print(message)


@task(queue_url=QUEUE2_URL, region_name='us-east-1', validator=ValidatorModel)
async def task_validator(message: ValidatorModel) -> None:
    print(message.dict())
