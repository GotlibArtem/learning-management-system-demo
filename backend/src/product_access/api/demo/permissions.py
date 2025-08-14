from rest_framework.permissions import DjangoModelPermissions


class ShopIntegrationPermission(DjangoModelPermissions):
    perms_map = {
        "POST": [
            "%(app_label)s.allow_shop_integration",
        ],
    }
