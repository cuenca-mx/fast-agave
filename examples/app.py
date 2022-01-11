import asyncio
from typing import Dict

from mongoengine import connect
from fastapi import FastAPI

from fast_agave.middlewares import FastAgaveErrorHandler
from .resources import app as resources
from .middlewares import AuthedMiddleware
from .tasks.task_example import dummy_task

connect(host='mongomock://localhost:27017/db')
app = FastAPI(title='example')
app.include_router(resources)

app.add_middleware(AuthedMiddleware)
app.add_middleware(FastAgaveErrorHandler)


@app.get('/')
async def iam_healty() -> Dict:
    return dict(greeting="I'm healthy!!!")


@app.on_event('startup')
async def on_startup() -> None:  # pragma: no cover
    # Inicializa el task que recibe mensajes
    # provenientes de SQS
    asyncio.create_task(dummy_task())
