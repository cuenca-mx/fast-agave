from mongoengine import StringField

from mongoengine_plus.models.helpers import uuid_field

from fast_agave.models import AsyncBaseModel


class File(AsyncBaseModel):
    id = StringField(primary_key=True, default=uuid_field('TR'))
    user_id = StringField(required=True)
    name = StringField(required=True)
