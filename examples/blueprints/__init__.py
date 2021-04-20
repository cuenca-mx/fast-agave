__all__ = ['AuthedRestApiBlueprint']

from fast_agave.blueprints import RestApiBlueprint
from .authed import AuthedBlueprint


class AuthedRestApiBlueprint(AuthedBlueprint, RestApiBlueprint):
    ...
