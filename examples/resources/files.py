from io import BytesIO

from fast_agave.filters import generic_query
from fastapi.responses import JSONResponse as Response

from ..models import File as FileModel
from ..validators import FileQuery, FileUploadValidator
from .base import app


@app.resource('/files')
class File:
    model = FileModel
    query_validator = FileQuery
    upload_validator = FileUploadValidator
    get_query_filter = generic_query

    @classmethod
    async def download(cls, data: FileModel) -> BytesIO:
        return BytesIO(bytes('Hello', 'utf-8'))

    @classmethod
    async def upload(cls, request: FileUploadValidator) -> Response:
        request_file = request.file
        file = FileModel(name=request_file.filename, user_id='US01')
        await file.async_save()
        return Response(content=file.to_dict(), status_code=201)
