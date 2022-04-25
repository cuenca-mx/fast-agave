from typing import Any

from fast_agave.blueprints import RestApiBlueprint
from starlette_context import context


class ArteriaBlueprint(RestApiBlueprint):
    @property
    def wallet(self) -> str:
        return context['wallet']

    def wallet_filter_required(self) -> bool:
        return context.get('wallet_filter_required')

    def custom_filter_required(self, query_params: Any, model: any) -> None:
        if self.wallet_filter_required() and hasattr(model, 'wallet'):
            query_params.wallet = self.wallet

    def user_id_filter_required(self) -> bool:
        return False

    def platform_id_filter_required(self) -> bool:
        return False
