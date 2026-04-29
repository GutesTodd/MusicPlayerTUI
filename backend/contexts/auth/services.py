from dataclasses import dataclass
from typing import Literal


@dataclass
class AuthStatus:
    status: Literal["pending", "success", "error", "none"]
    error_message: str | None = None


class AuthSessionStore:
    def __init__(self):
        self._sessions: dict[str, AuthStatus] = {}

    def set_status(self, platform: str, status: AuthStatus):
        self._sessions[platform] = status

    def get_status(self, platform: str) -> AuthStatus:
        return self._sessions.get(platform, AuthStatus(status="none"))
