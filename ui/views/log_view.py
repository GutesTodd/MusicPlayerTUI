from loguru import logger
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import RichLog


class TextualLoggerSink:
    def __init__(self, rich_log_widget: RichLog, app):
        self.rich_log = rich_log_widget
        self.app = app

    def write(self, message):
        self.rich_log.write(message.strip())


class LogPanel(Widget):
    def compose(self) -> ComposeResult:
        yield RichLog(id="system_logs", markup=True, highlight=True)

    def on_mount(self) -> None:
        import contextlib

        rich_log = self.query_one("#system_logs", RichLog)
        with contextlib.suppress(Exception):
            logger.remove()

        logger.add(
            TextualLoggerSink(rich_log, self.app),
            format="{time:HH:mm:ss} | {level} | {message}",
        )
