from mongoengine import FloatField, StringField

from agave.models.helpers import uuid_field

from fast_agave.models import AsyncBaseModel


class Transaction(AsyncBaseModel):
    id = StringField(primary_key=True, default=uuid_field('TR'))
    user_id = StringField(required=True)
    amount = FloatField(required=True)
