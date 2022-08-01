import datetime as dt
from typing import Dict
from fastapi import Request

from fastapi.responses import JSONResponse as Response
from fast_agave.filters import generic_query

from ..models import Card as CardModel
from ..validators import CardQuery, CardUpdateRequest
from .base import app


@app.resource('/cards')
class Card:
    model = CardModel
    query_validator = CardQuery
    update_validator = CardUpdateRequest
    get_query_filter = generic_query

    @staticmethod
    async def retrieve(card: CardModel) -> Response:
        data = card.to_dict()
        data['last_four_digits'] = card.number[-4:]
        return Response(content=data)

    @staticmethod
    async def query(response: Dict):
        for item in response['items']:
            item['last_four_digits'] = item['number'][-4:]
        return response

    @staticmethod
    async def update(card: CardModel, request: CardUpdateRequest) -> Response:
        card.status = request.status
        await card.async_save()
        return Response(content=card.to_dict(), status_code=200)

    @staticmethod
    async def delete(card: CardModel, _: Request) -> Response:
        card.deactivated_at = dt.datetime.utcnow()
        await card.async_save()
        return Response(content=card.to_dict(), status_code=200)
