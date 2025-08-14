import base64
import hashlib
import json
import time
from dataclasses import dataclass
from typing import TypedDict

from django.conf import settings
from django.utils.functional import cached_property

from app.services import BaseService
from users.models import User


class CommentAuthData(TypedDict):
    user_json_base64: str
    signature: str
    current_time_ms: str


@dataclass
class UserCommentTokenGetter(BaseService):
    """Get user comment token"""

    user: User

    def act(self) -> CommentAuthData:
        user_json_base64 = self.get_user_json_base64()
        signature = self.get_signature_string(user_json_base64)
        return CommentAuthData(user_json_base64=user_json_base64, signature=signature, current_time_ms=self.current_time_ms)

    def get_user_json_base64(self) -> str:
        user_data = {
            "id": str(self.user.id),
            "name": self.user.get_full_name() or self.user.username,
            "email": self.user.username,
        }
        json_data = json.dumps(user_data)
        return base64.b64encode(json_data.encode("utf-8")).decode("utf-8")

    def get_signature_string(self, user_json_base64: str) -> str:
        base64_data = base64.b64encode(user_json_base64.encode("utf-8")).decode("utf-8")

        signature_string = f"{base64_data}{settings.COMMENT_PROVIDER_API_KEY}{self.current_time_ms}"
        return hashlib.md5(signature_string.encode("utf-8")).hexdigest()

    @cached_property
    def current_time_ms(self) -> str:
        return str(int(time.time() * 1000))
