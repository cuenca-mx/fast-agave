from mongoengine import DateTimeField, StringField, IntField
from mongoengine_plus.aio import AsyncDocument
from mongoengine_plus.models import BaseModel

from mongoengine_plus.models.helpers import uuid_field


class Card(BaseModel, AsyncDocument):
    id = StringField(primary_key=True, default=uuid_field('CA'))
    number = StringField(required=True)
    cvv = StringField(default='111')
    exp_year = IntField(default=2040)
    user_id = StringField(required=True)
    status = StringField(default='active')
    created_at = DateTimeField()
    deactivated_at = DateTimeField()
