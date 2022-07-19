import asyncio
import base64
import binascii
import json
import os
import re
from dataclasses import asdict
from typing import Any, Optional

from aiohttp import ClientSession
from cuenca_validations.errors import CuencaError
from cuenca_validations.typing import DictStrAny
from fastapi import Request, Response
from starlette.datastructures import Headers
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)

from fast_agave.exc import FastAgaveError

AUTHED_REQUIRED_HEADERS = {
    'x-cuenca-token',
    'x-cuenca-logintoken',
    'x-cuenca-loginid',
    'x-cuenca-sessionid',
}

SENSITIVE_DATA_FIELDS = {
    'number',
    'cvv2',
    'cvv',
    'icvv',
    'exp_month',
    'exp_year',
    'pin',
    'pin_block',
    'pin_block_switch',
}

NON_VALID_SCOPE_VALUES = [
    'headers',
    'app',
    'extensions',
    'fastapi_astack',
    'app',
    'route_handler',
    'router',
    'endpoint',
]


def basic_auth_decode(basic: str) -> str:
    basic = re.sub(r'^Basic ', '', basic, flags=re.IGNORECASE)
    try:
        decoded = base64.b64decode(basic).decode('ascii')
        ak, _ = decoded.split(':')
    except (binascii.Error, UnicodeDecodeError, ValueError):
        # If `basic` value is not valid then it is not a sensitive data
        return basic
    return ak


def mask_sensitive_headers(headers: Headers) -> DictStrAny:
    masked_dict = dict()
    for key, val in headers.items():
        if key == 'authorization':
            masked_dict[key] = basic_auth_decode(val)
        elif key in AUTHED_REQUIRED_HEADERS:
            masked_dict[key] = val[0:5] + '*' * 5 if val else ''
        else:
            masked_dict[key] = val
    return masked_dict


def mask_sensitive_data(data: Any) -> Any:
    if type(data) is dict:
        for key, val in data.items():
            if type(val) is list:
                data[key] = [mask_sensitive_data(v) for v in val]
            elif key == 'number':
                data[key] = '*' * 12 + val[-4:]
            elif key in SENSITIVE_DATA_FIELDS and type(val) is int:
                data[key] = '***'
            elif key in SENSITIVE_DATA_FIELDS:
                data[key] = '*' * len(key)

    return data


class OpenSearchLog(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not os.environ.get('LOGS_SERVER_URL', ''):
            return await call_next(request)

        request_data = dict(request.scope)

        request_headers = mask_sensitive_headers(request.headers)
        request_data['client'] = f'{request.client.host}:{request.client.port}'
        request_data['query_string'] = str(request.query_params)
        request_data['server'] = ':'.join(
            (str(v) for v in request.scope['server'])
        )

        for value in NON_VALID_SCOPE_VALUES:
            request_data.pop(value, None)

        response_body = {}

        try:
            response = await call_next(request)
        except FastAgaveError as exc:
            response_body = asdict(exc)
            raise
        except CuencaError as exc:
            response_body = dict(status_code=exc.status_code, code=str(exc))
            raise
        else:
            # El objeto response es de tipo `starlette.responses.StreamingResponse`
            # por lo que sus datos vienen en binario, se deben obtener manualmente
            # y crear un custom Request
            # https://stackoverflow.com/questions/71882419/fastapi-how-to-get-the-response-body-in-middleware
            binary_response_body = b''
            async for chunk in response.body_iterator:  # type: ignore
                binary_response_body += chunk

            response_body = json.loads(binary_response_body.decode())
            response = Response(
                content=binary_response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

            response_body = mask_sensitive_data(response_body)
        finally:
            t = asyncio.create_task(
                self.send_log_to_open_search(
                    request.app.title,
                    request_data,
                    request_headers,
                    response_body,
                )
            )
            await t
        return response

    @classmethod
    async def send_log_to_open_search(
        cls,
        app_name: str,
        request_data: DictStrAny,
        request_headers: DictStrAny,
        response_body: Optional[DictStrAny] = None,
    ) -> None:
        log_server_url = os.environ.get('LOGS_SERVER_URL', '')
        data = dict(
            app=app_name,
            request_data=request_data,
            request_headers=request_headers,
            response_body=response_body,
        )
        async with ClientSession() as session:
            async with session.put(log_server_url, json=data):
                pass
