from typing import Dict

from fastapi import FastAPI

from .resources import app as resources

app = FastAPI()
app.include_router(resources)


@app.get('/')
async def iam_healty() -> Dict:
    return dict(greeting="I'm healthy!!!")
