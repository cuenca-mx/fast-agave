from typing import Any

from agave.models import BaseModel
from cuenca_validations.types import QueryParams
from mongoengine import Document, Q, QuerySet

from ..lib.utils import create_awaitable


class AsyncQuerySet(QuerySet):
    async def async_get(self, *q_objs, **query):
        return await create_awaitable(self.get, *q_objs, **query)

    async def async_count(self, with_limit_and_skip=False):
        return await create_awaitable(self.count, with_limit_and_skip)

    async def get_items(self):
        return await create_awaitable(list, self)


class AsyncBaseModel(BaseModel, Document):
    meta = dict(
        allow_inheritance=True,
        queryset_class=AsyncQuerySet,
    )

    async def async_save(self, *args, **kwargs):
        return await create_awaitable(self.save, *args, **kwargs)
