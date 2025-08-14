from rest_framework.permissions import DjangoModelPermissions


class PaymentIntegrationPermission(DjangoModelPermissions):
    perms_map = {
        "POST": [
            "%(app_label)s.allow_payment_integration",
            "%(app_label)s.allow_recurrent_integration",
        ],
    }
