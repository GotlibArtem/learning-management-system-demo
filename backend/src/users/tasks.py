from django.conf import settings

from a12n.models import PasswordlessEmailAuthCode
from app.celery import celery
from mindbox.services import MindboxClient
from mindbox.utils import is_corporate_email
from users.services import AuthCodeEmailContextBuilder


@celery.task(
    name="send_user_auth_code_to_email",
)
def send_user_auth_code_to_email(auth_code_id: str) -> None:
    user_email, auth_code = PasswordlessEmailAuthCode.objects.values_list("user__username", "code").get(id=auth_code_id)

    context = AuthCodeEmailContextBuilder(user_email, auth_code)()

    operation = settings.MINDBOX_EMAIL_AUTH_CODE_OPERATION_NAME_CORPORATE if is_corporate_email(user_email) else settings.MINDBOX_EMAIL_AUTH_CODE_OPERATION_NAME

    MindboxClient().run_email_operation(operation, user_email, context)
