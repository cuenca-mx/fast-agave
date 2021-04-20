from typing import Dict

from ..blueprints import AuthedRestApiBlueprint

app = AuthedRestApiBlueprint()


@app.get('/healthy_auth')
def health_auth_check() -> Dict:
    return dict(greeting="I'm authenticated and healthy !!!")
