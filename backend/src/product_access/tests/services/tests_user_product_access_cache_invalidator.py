import pytest
from django.core.cache import cache

from product_access.services import UserProductAccessCacheInvalidator


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def invalidator(user):
    return UserProductAccessCacheInvalidator(user=user)


@pytest.fixture
def cache_keys(user):
    return [
        f"subscription_boundaries_{user.id}",
        f"user_course_plans_{user.id}_with_series_True",
        f"user_course_plans_{user.id}_with_series_False",
        f"user_course_series_{user.id}",
        f"user_course_versions_{user.id}_with_series_True",
        f"user_course_versions_{user.id}_with_series_False",
        f"user_lectures_{user.id}",
        f"user_recurring_subscription_checker_{user.id}",
        f"user_subscription_checker_{user.id}",
    ]


@pytest.fixture
def prepare_cache(cache_keys):
    for key in cache_keys:
        cache.set(key, "dummy_value")


def test_invalidate_all_keys(invalidator, cache_keys, prepare_cache):
    # Ensure all keys exist before invalidation
    for key in cache_keys:
        assert cache.get(key) == "dummy_value"

    invalidator()

    for key in cache_keys:
        assert cache.get(key) is None


def test_invalidation_is_idempotent(invalidator, cache_keys):
    # Call invalidation when keys don't exist — should not raise errors
    invalidator()

    for key in cache_keys:
        assert cache.get(key) is None


def test_partial_cache_is_also_cleaned(invalidator, cache_keys):
    # Set only part of the keys
    for key in cache_keys[:3]:
        cache.set(key, "partial_value")

    invalidator()

    for key in cache_keys:
        assert cache.get(key) is None
