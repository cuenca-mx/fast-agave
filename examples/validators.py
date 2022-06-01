from typing import Optional

from cuenca_validations.types import QueryParams
from pydantic import BaseModel
import datetime as dt

from pydantic.main import BaseConfig


class AccountQuery(QueryParams):
    name: Optional[str] = None
    user_id: Optional[str] = None
    platform_id: Optional[str] = None
    is_active: Optional[bool] = None


class TransactionQuery(QueryParams):
    user_id: Optional[str] = None


class BillerQuery(QueryParams):
    name: str


class UserQuery(QueryParams):
    platform_id: str


class AccountRequest(BaseModel):
    name: str

    class Config(BaseConfig):
        fields = {
            'name': {'description': 'Sample description'},
        }
        schema_extra = {
            'example': {
                'name': 'Doroteo Arango',
            }
        }


class AccountResponse(BaseModel):
    id: str
    name: str
    user_id: str
    platform_id: str
    created_at: dt.datetime
    deactivated_at: Optional[dt.datetime] = None

    class Config(BaseConfig):
        fields = {'name': {'description': 'Sample description'}}
        schema_extra = {
            'example': {
                'id': 'AC-123456',
                'name': 'Doroteo Arango',
                'user_id': 'US123456789',
                'platform_id': 'PT-123456',
                'created_at': None,
                'deactivated_at': None,
            }
        }


class AccountUpdateRequest(BaseModel):
    name: str

    class Config(BaseConfig):
        schema_extra = {
            'example': {
                'name': 'Pancho Villa',
            }
        }


class FileQuery(QueryParams):
    user_id: Optional[str] = None


class CardQuery(QueryParams):
    number: Optional[str] = None


class FileUploadValidator(BaseModel):
    file: bytes
    file_name: str


class UserUpdateRequest(BaseModel):
    name: str
