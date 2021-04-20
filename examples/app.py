from typing import Dict
from mongoengine import connect
from fastapi import FastAPI

from .resources import app as resources

connect(host='mongomock://localhost:27017/db')
app = FastAPI()
app.include_router(resources)


@app.get('/')
async def iam_healty() -> Dict:
    return dict(greeting="I'm healthy!!!")
