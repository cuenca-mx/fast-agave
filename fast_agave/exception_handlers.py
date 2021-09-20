from cuenca_validations.errors import CuencaError
from fastapi import Request
from starlette.responses import JSONResponse

from fast_agave.exc import FastAgaveError


async def fast_agave_errors_handler(
    _: Request, exc: FastAgaveError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, content=dict(error=exc.detail)
    )


async def cuenca_errors_handler(_: Request, exc: CuencaError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=dict(error=str(exc), code=exc.code),
    )
