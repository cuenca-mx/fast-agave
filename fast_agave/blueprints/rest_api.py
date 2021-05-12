import mimetypes
from typing import Any, Optional
from urllib.parse import urlencode

from cuenca_validations.types import QueryParams
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse as Response
from fastapi.responses import StreamingResponse
from mongoengine import DoesNotExist, Q
from pydantic import ValidationError
from starlette_context import context

from ..exc import NotFoundError
from .decorators import copy_attributes


class RestApiBlueprint(APIRouter):
    @property
    def current_user_id(self) -> str:
        return context['user_id']

    def user_id_filter_required(self) -> bool:
        return context['user_id_filter_required']

    async def retrieve_object(
        self, resource_class: Any, resource_id: str
    ) -> Any:
        query = Q(id=resource_id)
        if self.user_id_filter_required():
            query = query & Q(user_id=self.current_user_id)
        try:
            data = await resource_class.model.objects.async_get(query)
        except DoesNotExist:
            raise NotFoundError
        return data

    def resource(self, path: str):
        """Decorator to transform a class in FastApi REST endpoints

        @app.resource('/my_resource')
        class Items(Resource):
            model = MyMongoModel
            query_validator = MyPydanticModel

            def create(): ...
            def delete(id): ...
            def retrieve(id): ...
            def get_query_filter(): ...

        This implementation create the following endpoints

        POST /my_resource
        PATCH /my_resource
        DELETE /my_resource/id
        GET /my_resource/id
        GET /my_resource
        """

        def wrapper_resource_class(cls):
            """Wrapper for resource class
            :param cls: Resoucre class
            :return:
            """

            """ POST /resource
            Create a FastApi endpoint using the method "create"
            """
            if hasattr(cls, 'create'):
                route = self.post(path)
                route(cls.create)

            """ DELETE /resource/{id}
            Use "delete" method (if exists) to create the FastApi endpoint
            """
            if hasattr(cls, 'delete'):

                @self.delete(path + '/{id}')
                @copy_attributes(cls)
                async def delete(id: str):
                    obj = await self.retrieve_object(cls, id)
                    return await cls.delete(obj)

            """ PATCH /resource/{id}
            Enable PATCH method if Resource.update method exist. It validates
            body data using `Resource.update_validator` but update logic is
            completely your responsibility.
            """
            if hasattr(cls, 'update'):

                @self.patch(path + '/{id}')
                @copy_attributes(cls)
                async def update(id: str, request: Request):
                    params = await request.json()
                    try:
                        update_params = cls.update_validator(**params)
                    except ValidationError as exc:
                        return Response(content=exc.json(), status_code=400)

                    obj = await self.retrieve_object(cls, id)
                    return await cls.update(obj, update_params)

                route(update)

            @self.get(path + '/{id}')
            @copy_attributes(cls)
            async def retrieve(id: str, request: Request):
                """GET /resource/{id}
                :param id: Object Id
                :return: Model object

                If exists "retrieve" method return the result of that, else
                use "id" param to retrieve the object of type "model" defined
                in the decorated class.

                The most of times this implementation is enough and is not
                necessary define a custom "retrieve" method
                """
                obj = await self.retrieve_object(cls, id)

                # This case is when the return is not an application/$
                # but can be some type of file such as image, xml, zip or pdf
                if hasattr(cls, 'download'):
                    file = await cls.download(obj)
                    mimetype = request.headers['accept']
                    extension = mimetypes.guess_extension(mimetype)
                    filename = f'{cls.model._class_name}.{extension}'
                    result = StreamingResponse(
                        file,
                        media_type=mimetype,
                        headers={
                            'Content-Disposition': f'attachment; filename={filename}'
                        },
                    )
                elif hasattr(cls, 'retrieve'):
                    result = await cls.retrieve(obj)
                else:
                    result = obj.to_dict()

                return result

            @self.get(path)
            @copy_attributes(cls)
            async def query(request: Request):
                """GET /resource
                Method for queries in resource. Use "query_validator" type
                defined in decorated class to validate the params.

                The "get_query_filter" method defined in decorated class
                should provide the way that the params are used to filter data

                If param "count" is True return the next response
                {
                    count:<count>

                }

                else the response is like this
                {
                    items = [{},{},...]
                    next_page = <url_for_next_items>
                }
                """
                if not hasattr(cls, 'query_validator') or not hasattr(
                    cls, 'get_query_filter'
                ):
                    raise HTTPException(405)

                try:
                    query_params = cls.query_validator(**request.query_params)
                except ValidationError as e:
                    return Response(content=e.json(), status_code=400)

                # Set user_id request as query param
                if self.user_id_filter_required():
                    query_params.user_id = self.current_user_id
                filters = cls.get_query_filter(query_params)
                if query_params.count:
                    result = await _count(filters)
                elif hasattr(cls, 'query'):
                    result = await cls.query(
                        await _all(query_params, filters, request.url.path)
                    )
                else:
                    result = await _all(
                        query_params, filters, request.url.path
                    )
                return result

            async def _count(filters: Q):
                count = await cls.model.objects.filter(filters).async_count()
                return dict(count=count)

            async def _all(query: QueryParams, filters: Q, resource_path: str):
                if query.limit:
                    limit = min(query.limit, query.page_size)
                    query.limit = max(0, query.limit - limit)
                else:
                    limit = query.page_size
                query_set = (
                    cls.model.objects.order_by("-created_at")
                    .filter(filters)
                    .limit(limit)
                )
                items = await query_set.async_to_list()
                item_dicts = [i.to_dict() for i in items]

                has_more: Optional[bool] = None
                if wants_more := query.limit is None or query.limit > 0:
                    # only perform this query if it's necessary
                    has_more = (
                        await query_set.limit(limit + 1).async_count() > limit
                    )

                next_page_uri: Optional[str] = None
                if wants_more and has_more:
                    query.created_before = item_dicts[-1]['created_at']
                    params = query.dict()
                    if self.user_id_filter_required():
                        params.pop('user_id')
                    next_page_uri = f'{resource_path}?{urlencode(params)}'
                return dict(items=item_dicts, next_page_uri=next_page_uri)

            return cls

        return wrapper_resource_class
