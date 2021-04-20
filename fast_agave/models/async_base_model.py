from typing import Any

from agave.models import BaseModel
from cuenca_validations.types import QueryParams
from mongoengine import Document, Q

from ..lib.utils import create_awaitable


class AsyncBaseModel(BaseModel, Document):
    meta = dict(allow_inheritance=True)

    @classmethod
    async def retrieve(cls, filters: Q) -> Any:
        return await create_awaitable(cls.objects.get, filters)

    @classmethod
    async def count(cls, filters: Q) -> int:
        return await create_awaitable(cls.objects.filter(filters).count)

    @classmethod
    async def filter(cls, filters: QueryParams, **delimiters) -> Any:
        ...

    async def async_save(self, *args, **kwargs):
        return await create_awaitable(self.save, *args, **kwargs)
