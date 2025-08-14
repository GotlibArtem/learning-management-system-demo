import pytest

from mindbox.services.mindbox_progress_notifier import MindboxProgressNotifier
from mindbox.types import CourseProgressStatus


pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture(autouse=True)
def mock_course_started(mocker):
    return mocker.patch("mindbox.services.client.MindboxClient.course_started")


@pytest.fixture(autouse=True)
def mock_update_course_progress(mocker):
    return mocker.patch("mindbox.services.client.MindboxClient.update_course_progress")


@pytest.fixture(autouse=True)
def mock_add_course_to_watched(mocker):
    return mocker.patch("mindbox.services.client.MindboxClient.add_course_to_watched")


@pytest.fixture
def notifier(course_progress):
    return MindboxProgressNotifier(course_progress=course_progress)


@pytest.fixture(autouse=True)
def product_with_shop_id(product, course_version, course_plan):
    product.setattr_and_save("shop_id", "123")
    product.course_versions_plans.add(course_version, through_defaults=dict(course_plan=course_plan))
    return product


def test_call_course_started_if_mindbox_sent_percent_is_none(notifier, course_progress, mock_course_started, mock_update_course_progress):
    course_progress.setattr_and_save("mindbox_sent_percent", None)
    course_progress.setattr_and_save("completion_percent", 10)

    notifier()

    mock_course_started.assert_called_once_with(
        email=course_progress.user.username,
        progress_id=str(course_progress.id),
        product_id=notifier.shop_id,
    )
    mock_update_course_progress.assert_called_once_with(
        progress_id=str(course_progress.id),
        status=CourseProgressStatus.PROGRESS_10,
    )
    assert course_progress.mindbox_sent_percent == 10


def test_do_nothing_if_current_progress_less_than_previous(notifier, course_progress, mock_course_started, mock_update_course_progress):
    course_progress.setattr_and_save("completion_percent", 10)
    course_progress.setattr_and_save("mindbox_sent_percent", 25)

    notifier()

    mock_update_course_progress.assert_not_called()
    mock_course_started.assert_not_called()
    assert course_progress.mindbox_sent_percent == 25


def test_do_nothing_if_status_not_changed(notifier, course_progress, mock_course_started, mock_update_course_progress):
    course_progress.setattr_and_save("completion_percent", 12)
    course_progress.setattr_and_save("mindbox_sent_percent", 10)

    notifier()

    mock_update_course_progress.assert_not_called()
    mock_course_started.assert_not_called()
    assert course_progress.mindbox_sent_percent == 10


@pytest.mark.parametrize(
    ("completion_percent", "mindbox_sent_percent", "expected_status"),
    [
        (5, 1, CourseProgressStatus.PROGRESS_5),
        (10, 5, CourseProgressStatus.PROGRESS_10),
        (25, 10, CourseProgressStatus.PROGRESS_25),
        (50, 25, CourseProgressStatus.PROGRESS_50),
        (75, 50, CourseProgressStatus.PROGRESS_75),
        (90, 75, CourseProgressStatus.PROGRESS_90),
        (100, 90, CourseProgressStatus.FINISHED),
    ],
)
def test_update_course_progress_with_proper_status(
    notifier,
    course_progress,
    mock_course_started,
    mock_update_course_progress,
    completion_percent,
    mindbox_sent_percent,
    expected_status,
):
    course_progress.setattr_and_save("completion_percent", completion_percent)
    course_progress.setattr_and_save("mindbox_sent_percent", mindbox_sent_percent)

    notifier()

    mock_update_course_progress.assert_called_once_with(
        progress_id=str(course_progress.id),
        status=expected_status,
    )
    mock_course_started.assert_not_called()
    assert course_progress.mindbox_sent_percent == completion_percent


def test_do_nothing_if_mindbox_disabled(settings, notifier, course_progress, mock_course_started, mock_update_course_progress):
    course_progress.setattr_and_save("mindbox_sent_percent", None)
    course_progress.setattr_and_save("completion_percent", 10)
    settings.MINDBOX_ENABLED = False

    notifier()

    mock_course_started.assert_not_called()
    mock_update_course_progress.assert_not_called()
    assert course_progress.mindbox_sent_percent is None


def test_add_course_to_watched_when_completed(
    notifier,
    course_progress,
    mock_course_started,
    mock_update_course_progress,
    mock_add_course_to_watched,
):
    course_progress.setattr_and_save("completion_percent", 100)
    course_progress.setattr_and_save("mindbox_sent_percent", 90)

    notifier()

    mock_course_started.assert_not_called()
    mock_add_course_to_watched.assert_called_once_with(
        email=course_progress.user.username,
        product_id=notifier.shop_id,
    )
    mock_update_course_progress.assert_called_once_with(
        progress_id=str(course_progress.id),
        status=CourseProgressStatus.FINISHED,
    )
    assert course_progress.mindbox_sent_percent == 100


def test_do_not_add_course_to_watched_if_already_completed(
    notifier,
    course_progress,
    mock_course_started,
    mock_update_course_progress,
    mock_add_course_to_watched,
):
    course_progress.setattr_and_save("completion_percent", 100)
    course_progress.setattr_and_save("mindbox_sent_percent", 100)

    notifier()

    mock_add_course_to_watched.assert_not_called()
    mock_update_course_progress.assert_not_called()
    mock_course_started.assert_not_called()
