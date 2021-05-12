from io import BytesIO

from fast_agave.filters import generic_query

from ..models import File as FileModel
from ..validators import FileQuery
from .base import app


@app.resource('/files')
class File:
    model = FileModel
    query_validator = FileQuery
    get_query_filter = generic_query

    @classmethod
    async def download(cls, data: FileModel) -> BytesIO:
        return BytesIO(bytes('Hello', 'utf-8'))
