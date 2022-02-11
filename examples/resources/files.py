from io import BytesIO

from fast_agave.filters import generic_query
from fastapi.datastructures import UploadFile
from fastapi.responses import JSONResponse as Response

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

    @classmethod
    async def upload(cls, id: str, file: UploadFile) -> Response:
        file = FileModel(user_id=id, name=file.filename)
        await file.async_save()
        return Response(content=file.to_dict(), status_code=201)
