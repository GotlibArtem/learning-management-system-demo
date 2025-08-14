from dataclasses import dataclass

from rest_framework.request import Request


@dataclass
class PlatformDetector:
    request: Request

    @property
    def platform(self) -> str:
        return self.request.headers.get("Platform", "").lower()

    @property
    def is_ios(self) -> bool:
        return self.platform == "ios"

    @property
    def is_android(self) -> bool:
        return self.platform == "android"

    @property
    def is_web(self) -> bool:
        return self.platform in ("web", "")
