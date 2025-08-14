from django.utils.timezone import now

from app.celery import celery
from payments.models import Recurrent, RecurrentStatus
from payments.services import RecurringPaymentProcessor


@celery.task(name="schedule_recurrent_charges", max_retries=0)
def schedule_recurrent_charges() -> None:
    today = now().date()

    recurrents = Recurrent.objects.filter(
        status=RecurrentStatus.ACTIVE,
        next_charge_date__lte=today,
        payment_instrument__isnull=False,
    )

    for recurrent in recurrents:
        run_recurrent_charge.delay(str(recurrent.id))


@celery.task(name="run_recurrent_charge", max_retries=0, rate_limit="3/m")
def run_recurrent_charge(recurrent_id: str) -> None:
    recurrent = Recurrent.objects.get(id=recurrent_id)
    RecurringPaymentProcessor(recurrent)()
