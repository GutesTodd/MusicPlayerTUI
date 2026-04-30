from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label, ProgressBar, Static

from ui.widgets.visualizer import Visualizer


class TickerLabel(Label):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._full_text: str = ""
        self._offset: int = 0
        self._ticker_interval: Any = None

    def update_text(self, text: str) -> None:
        if self._full_text == text:
            return
        self._full_text = text
        self._offset = 0
        if self._ticker_interval is None:
            self._ticker_interval = self.set_interval(0.3, self._tick)
        self._render_text()

    def _tick(self) -> None:
        width = self.size.width
        if not self._full_text or width <= 0:
            return

        if len(self._full_text) > width:
            self._offset = (self._offset + 1) % (len(self._full_text) + 5)
            self._render_text()
        else:
            if self._offset != 0:
                self._offset = 0
                self._render_text()

    def _render_text(self) -> None:
        width = self.size.width
        if not self._full_text:
            self.update("")
            return

        if width <= 0 or len(self._full_text) <= width:
            self.update(self._full_text)
            return

        padded = self._full_text + "     " + self._full_text
        visible = padded[self._offset : self._offset + width]
        self.update(visible)


class PlayerBar(Static):
    def compose(self) -> ComposeResult:
        with Vertical(id="player_layout"):
            # Уровень 1: Название - Прогресс - Таймкод
            with Horizontal(id="player_row1"):
                yield TickerLabel("▶ Сейчас ничего не играет", id="current_track")
                yield ProgressBar(
                    total=100,
                    show_bar=True,
                    show_percentage=False,
                    show_eta=False,
                    id="track_progress",
                )
                yield Label("00:00 / 00:00", id="time_code")

            # Уровень 2: Визуализатор
            with Horizontal(id="player_row2"):
                yield Visualizer(id="wave_viz")

            # Уровень 3: Кнопки - Громкость
            with Horizontal(id="player_row3"):
                with Horizontal(id="player_row3_left"):
                    pass
                with Horizontal(id="player_controls"):
                    yield Button("󰑗", id="btn_repeat", variant="default")
                    yield Button("󰒮", id="btn_prev")
                    yield Button("󰐊", id="btn_play_pause")
                    yield Button("󰒭", id="btn_next")
                with Horizontal(id="volume_group"):
                    yield Label("󰕾 ")
                    yield ProgressBar(
                        total=100,
                        show_bar=True,
                        show_percentage=False,
                        show_eta=False,
                        id="volume_bar",
                    )
