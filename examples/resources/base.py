from typing import Dict, NoReturn

from cuenca_validations.errors import WrongCredsError

from fast_agave.blueprints import RestApiBlueprint
from fast_agave.exc import UnauthorizedError

app = RestApiBlueprint()


@app.get('/healthy_auth')
def health_auth_check() -> Dict:
    return dict(greeting="I'm authenticated and healthy !!!")


@app.get('/raise_cuenca_errors')
def raise_cuenca_errors() -> NoReturn:
    raise WrongCredsError('you are not lucky enough!')


@app.get('/raise_fast_agave_errors')
def raise_fast_agave_errors() -> NoReturn:
    raise UnauthorizedError('nice try!')


@app.get('/you_shall_not_pass')
def you_shall_not_pass() -> None:
    # Este endpoint nunca será ejecutado
    # La prueba de este endpoint hace un mock a nivel middleware
    # para responder con un `UnauthorizedError`
    ...
