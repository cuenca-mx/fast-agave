import datetime as dt

from agave.filters import generic_query
from fastapi.responses import JSONResponse as Response
from fast_agave.exc import NotFoundError
from mongoengine import DoesNotExist

from ..models import Account as AccountModel
from ..validators import AccountQuery, AccountRequest, AccountUpdateRequest
from .base import app


@app.resource('/accounts')
class Account:
    model = AccountModel
    query_validator = AccountQuery
    update_validator = AccountUpdateRequest
    get_query_filter = generic_query

    @staticmethod
    async def create(request: AccountRequest) -> Response:
        account = AccountModel(
            name=request.name,
            user_id=app.current_user_id,
        )
        account.save()
        return Response(content=account.to_dict(), status_code=201)

    @staticmethod
    async def update(
        account: AccountModel, request: AccountUpdateRequest
    ) -> Response:
        account.name = request.name
        account.save()
        return Response(content=account.to_dict(), status_code=200)

    @staticmethod
    async def delete(id: str) -> Response:
        try:
            account = AccountModel.objects.get(id=id)
        except DoesNotExist:
            raise NotFoundError

        account.deactivated_at = dt.datetime.utcnow().replace(microsecond=0)
        account.save()
        return Response(account.to_dict(), status_code=200)
