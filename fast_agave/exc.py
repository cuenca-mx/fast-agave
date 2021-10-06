from dataclasses import dataclass


@dataclass
class FastAgaveError(Exception):
    error: str
    status_code: int


@dataclass
class BadRequestError(FastAgaveError):
    status_code: int = 400


@dataclass
class UnauthorizedError(FastAgaveError):
    status_code: int = 401


@dataclass
class ForbiddenError(FastAgaveError):
    status_code: int = 403


@dataclass
class NotFoundError(FastAgaveError):
    status_code: int = 404


@dataclass
class FastAgaveViewError(FastAgaveError):
    status_code: int = 500
