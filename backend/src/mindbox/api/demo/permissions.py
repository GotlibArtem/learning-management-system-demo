from rest_framework.permissions import DjangoModelPermissions


class MindboxIntegrationPermission(DjangoModelPermissions):
    perms_map = {
        "POST": [
            "users.allow_mindbox_integration",
        ],
    }
