from dataclasses import dataclass
from enum import Enum
from typing import Optional

class AuthStatusEnum(str, Enum):
    IDLE = "idle"
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"

@dataclass
class AuthStatus:
    status: AuthStatusEnum = AuthStatusEnum.IDLE
    user_code: Optional[str] = None
    verification_url: Optional[str] = None
    error_message: Optional[str] = None

class AuthSessionStore:
    def __init__(self):
        self._current_status = AuthStatus()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self._current_status, key):
                setattr(self._current_status, key, value)

    def get_status(self) -> AuthStatus:
        return self._current_status

    def reset(self):
        self._current_status = AuthStatus()
