from django_filters import filters


class StringInFilter(filters.BaseInFilter, filters.CharFilter):
    """
    Gets comma separated strings from GET parameter and matches entities by `in` operator.

    Example: url.com?some_slugs=foo,bar,baz
    """
