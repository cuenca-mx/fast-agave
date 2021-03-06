from fast_agave.filters import generic_query
from ..models import User as UserModel
from ..validators import UserQuery, UserUpdateRequest
from .base import app
from fastapi.responses import JSONResponse as Response
from fastapi import Request


@app.resource('/users')
class User:
    model = UserModel
    query_validator = UserQuery
    get_query_filter = generic_query
    update_validator = UserUpdateRequest

    @staticmethod
    async def update(
        user: UserModel, request: UserUpdateRequest, api_request: Request
    ) -> Response:
        user.name = request.name
        user.ip = api_request.client.host
        await user.async_save()
        return Response(content=user.to_dict(), status_code=200)
