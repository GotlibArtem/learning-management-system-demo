from rest_framework.permissions import DjangoModelPermissions


class BonusIntegrationPermission(DjangoModelPermissions):
    perms_map = {
        "GET": [
            "%(app_label)s.allow_bonuses_integration",
        ],
        "POST": [
            "%(app_label)s.allow_bonuses_integration",
        ],
    }
