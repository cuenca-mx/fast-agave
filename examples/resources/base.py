from typing import Dict

from fast_agave.blueprints import RestApiBlueprint

app = RestApiBlueprint()


@app.get('/healthy_auth')
def health_auth_check() -> Dict:
    return dict(greeting="I'm authenticated and healthy !!!")
