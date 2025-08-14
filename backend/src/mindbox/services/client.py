from dataclasses import dataclass
from datetime import date

from django.conf import settings
from rest_framework.status import HTTP_200_OK

from app.convenient_http_client import ConvenientHTTPClient
from mindbox.decorators import mindbox_enabled
from mindbox.models import MindboxOperationLog
from mindbox.types import CourseProgressStatus


class MindboxClientException(Exception):
    """Raise if there is errors in communication."""


@dataclass
class MindboxClient:
    endpoint_id: str
    secret_key: str
    client: ConvenientHTTPClient

    def __init__(self) -> None:
        self.endpoint_id = settings.MINDBOX_ENDPOINT_ID
        self.secret_key = settings.MINDBOX_ENDPOINT_SECRET_KEY
        self.mindbox_http = ConvenientHTTPClient(base_url=settings.MINDBOX_URL)
        self.headers = {"Authorization": f"SecretKey {self.secret_key}"}

    @mindbox_enabled
    def run_email_operation(self, operation: str, email: str, mailing_params: dict) -> None:
        """
        This mindbox client is just transport.

        You should generate mailing params via business layer of your django app that needs operation to be sent,
        check this service for reference: `AuthCodeEmailContextBuilder`.
        """
        content = {
            "customer": {
                "email": email,
            },
            "emailMailing": {
                "customParameters": mailing_params,
            },
        }

        response, status = self.mindbox_http.request(
            method="post",
            endpoint=f"operations/sync?endpointId={self.endpoint_id}&operation={operation}",
            headers=self.headers,
            data=content,
            raise_for_status=False,
        )
        self._handle_response(response, status, operation, content, email)

    @mindbox_enabled
    def course_started(self, email: str, progress_id: str, product_id: str) -> None:
        """Send course started event to Mindbox."""
        operation = "CourseStarted"
        content = {
            "customer": {
                "email": email,
            },
            "order": {
                "ids": {
                    "externalID": progress_id,
                },
                "customFields": {
                    "lMSCourse": "true",
                },
                "lines": [
                    {
                        "basePricePerItem": "0",
                        "quantity": "1",
                        "lineNumber": "1",
                        "product": {
                            "ids": {
                                "website": product_id,
                            },
                        },
                    },
                ],
            },
        }

        response, status = self.mindbox_http.request(
            method="post",
            endpoint=f"operations/sync?endpointId={self.endpoint_id}&operation={operation}",
            headers=self.headers,
            data=content,
            raise_for_status=False,
        )
        self._handle_response(response, status, operation, content)

    @mindbox_enabled
    def update_course_progress(self, progress_id: str, status: CourseProgressStatus) -> None:
        """Update course progress status in Mindbox."""
        operation = "CourseProgressUpdate"
        content = {
            "orderLinesStatus": status,
            "order": {
                "ids": {
                    "externalID": progress_id,
                },
            },
        }

        response, status_code = self.mindbox_http.request(
            method="post",
            endpoint=f"operations/sync?endpointId={self.endpoint_id}&operation={operation}",
            headers=self.headers,
            data=content,
            raise_for_status=False,
        )
        self._handle_response(response, status_code, operation, content)

    @mindbox_enabled
    def user_logged_in(self, email: str, device_uuid: str) -> None:
        """Send logged in event to Mindbox."""
        operation = "LMSLoggedIn"
        content = {
            "customer": {
                "email": email,
            },
        }

        response, status = self.mindbox_http.request(
            method="post",
            endpoint=f"operations/sync?endpointId={self.endpoint_id}&operation={operation}&deviceUUID={device_uuid}",
            headers=self.headers,
            data=content,
            raise_for_status=False,
        )
        self._handle_response(response, status, operation, content)

    @mindbox_enabled
    def add_course_to_watched(self, email: str, product_id: str) -> None:
        """Add course to watched list in Mindbox."""
        operation = "AddProductToKursyKlientaItemList"
        content = {
            "customer": {
                "email": email,
            },
            "addProductToList": {
                "product": {
                    "ids": {
                        "website": product_id,
                    },
                },
            },
        }

        response, status = self.mindbox_http.request(
            method="post",
            endpoint=f"operations/sync?endpointId={self.endpoint_id}&operation={operation}",
            headers=self.headers,
            data=content,
            raise_for_status=False,
        )
        self._handle_response(response, status, operation, content)

    @mindbox_enabled
    def register_customer(self, email: str) -> None:
        operation = "LMSRegisterCustomer"
        content = {
            "customer": {
                "email": email,
                "subscriptions": [
                    {
                        "brand": "LMS",
                        "pointOfContact": "Email",
                        "topic": "LMS",
                        "isSubscribed": True,
                    },
                ],
            },
        }

        response, status = self.mindbox_http.request(
            method="post",
            endpoint=f"operations/sync?endpointId={self.endpoint_id}&operation={operation}",
            headers=self.headers,
            data=content,
            raise_for_status=False,
        )
        self._handle_response(response, status, operation, content)

    @mindbox_enabled
    def edit_customer(
        self,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        birth_date: date | None = None,
        interests: list[str] | None = None,
    ) -> None:
        operation = "LMSEditCustomer"
        customer: dict[str, object] = {"email": email}

        if first_name:
            customer["firstName"] = first_name
        if last_name:
            customer["lastName"] = last_name
        if birth_date:
            customer["birthDate"] = birth_date.isoformat()
        if interests is not None:
            customer["customFields"] = {"interesLMS": interests}

        content: dict[str, object] = {"customer": customer}

        response, status = self.mindbox_http.request(
            method="post",
            endpoint=f"operations/sync?endpointId={self.endpoint_id}&operation={operation}",
            headers=self.headers,
            data=content,
            raise_for_status=False,
        )
        self._handle_response(response, status, operation, content)

    @mindbox_enabled
    def update_or_create_recurrent_order(
        self,
        email: str,
        amount: str,
        subscription_last_date: date | None = None,
        next_charge_date: date | None = None,
    ) -> None:
        operation = "ReccurentOrder"

        customer_custom_fields: dict[str, str | bool] = {
            "amountRecurrentPaid": amount,
        }
        if subscription_last_date:
            customer_custom_fields["subLastDay"] = subscription_last_date.isoformat()
        if next_charge_date:
            customer_custom_fields["nextPaymentDate"] = next_charge_date.isoformat()

        content = {
            "customer": {
                "email": email,
                "customFields": customer_custom_fields,
            },
            "order": {
                "customFields": {
                    "rekurrent": True,
                },
            },
        }

        response, status = self.mindbox_http.request(
            method="post",
            endpoint=f"operations/sync?endpointId={self.endpoint_id}&operation={operation}",
            headers=self.headers,
            data=content,
            raise_for_status=False,
        )
        self._handle_response(response, status, operation, content)

    @mindbox_enabled
    def send_payment_attempt(self, email: str, num_attempt: str, attempt_success: bool) -> None:
        operation = "PaymentAttempt"
        content = {
            "customer": {
                "email": email,
            },
            "customerAction": {
                "customFields": {
                    "nomerpopytki": num_attempt,
                    "paymentSuccess": attempt_success,
                },
            },
        }

        response, status = self.mindbox_http.request(
            method="post",
            endpoint=f"operations/sync?endpointId={self.endpoint_id}&operation={operation}",
            headers=self.headers,
            data=content,
            raise_for_status=False,
        )
        self._handle_response(response, status, operation, content)

    def _handle_response(self, response: dict, status: int, operation: str, content: dict, destination: str | None = None) -> None:
        if status != HTTP_200_OK or response["status"] != "Success":
            raise MindboxClientException(f"Mindbox operation error! Status: {status}, response: {response}")

        log_data = {"operation": operation, "content": content}
        if destination:
            log_data["destination"] = destination
        MindboxOperationLog.objects.create(**log_data)
