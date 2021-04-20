from mongoengine import DateTimeField, Document, StringField

from agave.models.helpers import uuid_field

from fast_agave.models import AsyncBaseModel


class Account(AsyncBaseModel):
    id = StringField(primary_key=True, default=uuid_field('AC'))
    name = StringField(required=True)
    user_id = StringField(required=True)
    created_at = DateTimeField()
    deactivated_at = DateTimeField()
