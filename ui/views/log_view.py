from textual.app import ComposeResult
from textual.widgets import RichLog
from textual.widget import Widget
from loguru import logger


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
        rich_log = self.query_one("#system_logs", RichLog)
        try:
            logger.remove()
        except Exception:
            pass

        logger.add(
            TextualLoggerSink(rich_log, self.app),
            format="{time:HH:mm:ss} | {level} | {message}",
        )
