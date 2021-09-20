from typing import Dict

from cuenca_validations.errors import CuencaError
from mongoengine import connect
from fastapi import FastAPI

from fast_agave.exc import FastAgaveError
from fast_agave.exception_handlers import (
    fast_agave_errors_handler,
    cuenca_errors_handler,
)
from .resources import app as resources
from .middlewares import AuthedMiddleware


connect(host='mongomock://localhost:27017/db')
app = FastAPI(title='example')
app.include_router(resources)

app.add_middleware(AuthedMiddleware)

app.add_exception_handler(FastAgaveError, fast_agave_errors_handler)
app.add_exception_handler(CuencaError, cuenca_errors_handler)


@app.get('/')
async def iam_healty() -> Dict:
    return dict(greeting="I'm healthy!!!")
