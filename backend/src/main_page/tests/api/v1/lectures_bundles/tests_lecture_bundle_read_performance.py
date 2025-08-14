import pytest


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def create_lecture_bundles(factory, user, block):
    def _create_lecture_bundles(count):
        bundles = factory.cycle(count).lecture_bundle_content(is_hidden=False)
        for bundle in bundles:
            lecture_bundle_item = factory.cycle(count).lecture_bundle_item(bundle=bundle)[0]
            factory.lecture_progress(user=user, lecture=lecture_bundle_item.lecture)
            factory.lecture_block(lecture=lecture_bundle_item.lecture, block=block, state="published")

    return _create_lecture_bundles


@pytest.mark.parametrize("count", [2, 4])
def test_lecture_bundles_list_no_nplus_one_queries(as_user, django_assert_max_num_queries, create_lecture_bundles, count):
    create_lecture_bundles(count)

    with django_assert_max_num_queries(10):
        as_user.get("/api/demo/main-page/lecture-bundles/")
