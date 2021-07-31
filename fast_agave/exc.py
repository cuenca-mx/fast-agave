from dataclasses import dataclass

from fastapi import HTTPException


@dataclass
class Error(HTTPException):
    def __init__(self, detail=''):
        super().__init__(status_code=self.status_code, detail=detail)


class BadRequestError(Error):
    status_code = 400


class UnauthorizedError(Error):
    status_code = 401


class ForbiddenError(Error):
    status_code = 403


class NotFoundError(Error):
    status_code = 404
