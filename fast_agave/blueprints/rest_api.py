from fastapi import APIRouter


class RestApiBlueprint(APIRouter):

    @property
    def current_user_id(self):
        # TODO: por definir
        return ...

    def user_id_filter_required(self) -> bool:
        raise NotImplementedError('this method should be override')

    def resource(self, path: str):

        def wrapper_resource_class(cls):
            @self.get(path + '/{id}')
            async def retrieve(id: str):
                return dict(id=id)

        return wrapper_resource_class
