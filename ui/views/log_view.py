from loguru import logger
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import RichLog


class LogPanel(Vertical):
    def compose(self) -> ComposeResult:
        yield RichLog(id="system_logs", markup=True, highlight=True)

    def on_mount(self) -> None:
        import contextlib

        rich_log = self.query_one("#system_logs", RichLog)
        rich_log.write("[bold green]>>> Панель логов активирована[/]")
        with contextlib.suppress(Exception):
            logger.remove()

        logger.add(
            lambda msg: rich_log.write(msg.strip()),
            format="{time:HH:mm:ss} | {level: <8} | {message}",
            level="DEBUG",
        )

        logger.info("Связь с Loguru установлена")
        logger.debug("Отладочные сообщения включены")
