from cuenca_validations.types import QueryParams
from mongoengine import Q


def generic_query(query: QueryParams, excluded=[]) -> Q:
    filters = Q()
    if query.created_before:
        filters &= Q(created_at__lt=query.created_before)
    if query.created_after:
        filters &= Q(created_at__gt=query.created_after)
    exclude_fields = {
        'created_before',
        'created_after',
        'active',
        'limit',
        'page_size',
        'key',
        *excluded,
    }
    fields = query.dict(exclude=exclude_fields)
    if 'count' in fields:
        del fields['count']
    return filters & Q(**fields)


def no_user_id_query(query: QueryParams) -> Q:
    return generic_query(query, excluded=['user_id'])


def identity_query(query: QueryParams) -> Q:
    return generic_query(query, excluded=['user_id', 'platform_id'])
