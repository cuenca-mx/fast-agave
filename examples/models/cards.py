from mongoengine import DateTimeField, StringField

from agave.models.helpers import uuid_field

from fast_agave.models import AsyncBaseModel


class Card(AsyncBaseModel):
    id = StringField(primary_key=True, default=uuid_field('CA'))
    number = StringField(required=True)
    user_id = StringField(required=True)
    created_at = DateTimeField()
