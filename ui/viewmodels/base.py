from collections.abc import Callable

from loguru import logger


class BaseViewModel:
    def __init__(self):
        self._listeners: list[Callable[[], None]] = []
        self.is_loading: bool = False
        self.error_message: str | None = None

    def subscribe(self, callback: Callable[[], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify(self) -> None:
        for callback in self._listeners:
            try:
                callback()
            except Exception as e:
                logger.error(f"Ошибка в UI-коллбэке: {e}")

    def set_error(self, message: str | None) -> None:
        self.error_message = message
        logger.error(message)
        self.notify()
