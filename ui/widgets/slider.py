from __future__ import annotations

from rich.text import Text
from textual.events import MouseDown, MouseMove, MouseUp
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget


class InteractiveSlider(Widget, can_focus=True):
    DEFAULT_CSS = """
    InteractiveSlider {
        width: 100%;
        height: 1;
        min-height: 1;
        margin: 0 1;
    }
    InteractiveSlider.-dragging {
        color: $accent;
    }
    """

    class Changed(Message):
        def __init__(self, slider: InteractiveSlider, value: float) -> None:
            super().__init__()
            self.slider = slider
            self.value = value

        @property
        def control(self) -> InteractiveSlider:
            return self.slider

    class Seeked(Message):
        def __init__(self, slider: InteractiveSlider, value: float) -> None:
            super().__init__()
            self.slider = slider
            self.value = value

        @property
        def control(self) -> InteractiveSlider:
            return self.slider

    value: reactive[float] = reactive(0.0)
    _dragging: bool = False

    def render(self) -> Text:
        width = self.size.width
        if width <= 0:
            return Text("")

        filled_width = int(self.value * width)

        text = Text()
        # Filled part
        text.append("━" * max(0, filled_width - 1), style="#1DB954")
        # Thumb
        text.append("●", style="white" if not self._dragging else "#1DB954")
        # Unfilled part
        text.append("━" * max(0, width - filled_width), style="#A7A7A7")

        return text

    def _update_value_from_mouse(self, x: int) -> None:
        width = self.size.width
        if width > 0:
            self.value = max(0.0, min(1.0, x / width))
            self.post_message(self.Changed(self, self.value))

    def on_mouse_down(self, event: MouseDown) -> None:
        self._dragging = True
        self.add_class("-dragging")
        self.capture_mouse()
        self._update_value_from_mouse(event.x)

    def on_mouse_move(self, event: MouseMove) -> None:
        if self._dragging:
            self._update_value_from_mouse(event.x)

    def on_mouse_up(self, event: MouseUp) -> None:
        if self._dragging:
            self._dragging = False
            self.remove_class("-dragging")
            self.release_mouse()
            self.post_message(self.Seeked(self, self.value))
