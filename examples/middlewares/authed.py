from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response
from starlette_context.middleware import ContextMiddleware
from starlette_context import _request_scope_context_storage

from fastapi import Request


class AuthedMiddleware(ContextMiddleware):
    def required_user_id(self) -> bool:
        """
        Example method so we can easily mock it in tests environment
        :return:
        """
        return False

    async def authenticate(self):
        self.token = _request_scope_context_storage.set(
            dict(user_id='US123456789')
        )

    async def authorize(self):
        context = _request_scope_context_storage.get()
        context['user_id_filter_required'] = self.required_user_id()
        self.token = _request_scope_context_storage.set(context)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            # Authentication and authorization goes here!
            await self.authenticate()
            await self.authorize()
            response = await call_next(request)
            for plugin in self.plugins:
                await plugin.enrich_response(response)

        finally:
            _request_scope_context_storage.reset(self.token)

        return response
