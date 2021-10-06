from cuenca_validations.errors import CuencaError
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)

from fast_agave.exc import FastAgaveError


class FastAgaveErrorHandler(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except CuencaError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content=dict(
                    code=exc.code,
                    error=str(exc),
                ),
            )
        except FastAgaveError as exc:
            return JSONResponse(
                status_code=exc.status_code, content=dict(error=exc.error)
            )
