from dataclasses import dataclass

from fastapi import HTTPException


@dataclass
class FastAgaveError(HTTPException):
    def __init__(self, detail=''):
        super().__init__(status_code=self.status_code, detail=detail)


class BadRequestError(FastAgaveError):
    status_code = 400


class UnauthorizedError(FastAgaveError):
    status_code = 401


class ForbiddenError(FastAgaveError):
    status_code = 403


class NotFoundError(FastAgaveError):
    status_code = 404
