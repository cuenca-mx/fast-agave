from typing import Dict

from mongoengine import connect
from fastapi import FastAPI
from starlette.middleware import Middleware

from .resources import app as resources
from .middlewares import AuthedMiddleware


connect(host='mongomock://localhost:27017/db')
app = FastAPI(middleware=[Middleware(AuthedMiddleware)])
app.include_router(resources)


@app.get('/')
async def iam_healty() -> Dict:
    return dict(greeting="I'm healthy!!!")
