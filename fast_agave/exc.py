from dataclasses import dataclass

from fastapi import HTTPException


@dataclass
class NotFoundError(HTTPException):
    status_code: int = 404
    detail: str = 'Not valid id'
