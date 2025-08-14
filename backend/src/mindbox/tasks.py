from datetime import timedelta

from django.apps import apps

from app.celery import celery
from payments.models import Recurrent, RecurrentChargeAttempt, RecurrentChargeStatus
from product_access.models import ProductAccess
from users.models import User


@celery.task(name="mindbox_notify_user_logged_in")
def notify_user_logged_in(user_id: str, device_uuid: str) -> None:
    from mindbox.services import MindboxClient

    user = User.objects.get(pk=user_id)
    MindboxClient().user_logged_in(email=user.username, device_uuid=device_uuid)


@celery.task(name="mindbox_register_customer")
def register_customer(user_id: str) -> None:
    from mindbox.services import MindboxClient

    user = User.objects.get(pk=user_id)
    MindboxClient().register_customer(email=user.username)


@celery.task(name="mindbox_edit_customer")
def edit_customer(user_id: str) -> None:
    from mindbox.services import MindboxClient

    user = User.objects.get(pk=user_id)
    MindboxClient().edit_customer(email=user.username, first_name=user.first_name, last_name=user.last_name, birth_date=user.birthdate)


@celery.task(name="mindbox_send_customer_interests")
def send_customer_interests(user_id: str) -> None:
    from mindbox.services import MindboxClient

    user = User.objects.get(pk=user_id)

    interests = ["all-interests"] if user.all_interests else user.interests.slugs()

    MindboxClient().edit_customer(email=user.username, interests=interests)


@celery.task(name="mindbox_notify_course_progress")
def notify_course_progress(course_progress_id: str) -> None:
    from mindbox.services import MindboxProgressNotifier

    CourseProgress = apps.get_model("progress", "CourseProgress")
    course_progress = CourseProgress.objects.get(pk=course_progress_id)
    MindboxProgressNotifier(course_progress=course_progress)()


@celery.task(name="mindbox_update_or_create_recurrent_order")
def update_or_create_recurrent_order(user_id: str, recurrent_id: str) -> None:
    from mindbox.services import MindboxClient

    user = User.objects.get(pk=user_id)
    recurrent = Recurrent.objects.get(pk=recurrent_id)
    product_access = ProductAccess.objects.filter(user=user, product=recurrent.product).first()

    next_charge_date = (
        recurrent.next_charge_date.date() if recurrent.next_charge_date else (product_access.end_date.date() + timedelta(days=product_access.product.lifetime))  # type: ignore
    )

    MindboxClient().update_or_create_recurrent_order(
        email=user.username,
        amount=recurrent.amount,
        subscription_last_date=product_access.end_date.date() if product_access else None,
        next_charge_date=next_charge_date,
    )


@celery.task(name="mindbox_send_payment_attempt")
def send_payment_attempt(user_id: str, recurrent_charge_attempt_id: str) -> None:
    from mindbox.services import MindboxClient

    user = User.objects.get(pk=user_id)
    recurrent_charge_attempt = RecurrentChargeAttempt.objects.get(pk=recurrent_charge_attempt_id)
    attempts_count = RecurrentChargeAttempt.objects.filter(
        recurrent=recurrent_charge_attempt.recurrent,
        created__gte=recurrent_charge_attempt.recurrent.next_charge_date,
    ).count()

    attempt_success = recurrent_charge_attempt.status == RecurrentChargeStatus.SUCCESS

    MindboxClient().send_payment_attempt(
        email=user.username,
        num_attempt=f"{attempts_count}attempt",
        attempt_success=attempt_success,
    )
