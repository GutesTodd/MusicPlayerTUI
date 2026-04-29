from typing import Callable, Final
from loguru import logger
from pynput import keyboard

from shared.domain.interfaces import GlobalHotkeyProvider


class PynputHotkeyProvider(GlobalHotkeyProvider):
    """Реализация захвата клавиш через библиотеку pynput."""

    def __init__(self) -> None:
        self._listener: keyboard.GlobalHotKeys | None = None
        self._callback: Callable[[str], None] | None = None

        # Словарь маппинга клавиш на внутренние действия (Actions)
        self._hotkeys_map: Final[dict[str, str]] = {
            "<alt>+p": "toggle_play",
            "<ctrl>+<alt>+space": "toggle_play",
            "<media_play_pause>": "toggle_play",
            "<media_next>": "next_track",
            "<media_previous>": "prev_track",
        }

    def start(self, callback: Callable[[str], None]) -> None:
        self._callback = callback

        # Создаем обработчики для pynput
        handlers = {
            key: self._make_handler(action) for key, action in self._hotkeys_map.items()
        }

        try:
            self._listener = keyboard.GlobalHotKeys(handlers)
            self._listener.daemon = True
            self._listener.start()
            logger.info(
                f"PynputHotkeyProvider запущен. Зарегистрировано {len(handlers)} клавиш."
            )
        except Exception as e:
            logger.error(f"Не удалось запустить PynputHotkeyProvider: {e}")

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            logger.info("PynputHotkeyProvider остановлен.")

    def _make_handler(self, action: str) -> Callable[[], None]:
        """Фабрика для создания потокобезопасных замыканий."""

        def handler():
            if self._callback:
                logger.debug(f"Глобальная клавиша нажата -> Action: {action}")
                self._callback(action)

        return handler
