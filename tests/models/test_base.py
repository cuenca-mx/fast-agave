from enum import Enum

from mongoengine import Document, StringField
from mongoengine_plus.types import EnumField

from fast_agave.models import BaseModel


class ModelType(Enum):
    test = 'test'


class TestModel(BaseModel, Document):
    id = StringField()
    secret_field = StringField()
    type = EnumField(ModelType)
    __test__ = False
    _hidden = ['secret_field']


def test_hide_field():
    model = TestModel(id='12345', secret_field='secret', type=ModelType.test)
    model_dict = model.to_dict()
    assert model_dict['secret_field'] == '********'
    assert model_dict['id'] == '12345'
    assert model_dict['type'] == 'test'
