from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Label, Static


class Sidebar(Static):
    def compose(self) -> ComposeResult:
        yield Label("󰎈 YANDEX MUSIC", id="logo")
        with Vertical(classes="nav-menu"):
            yield Button(
                "󰄉  Поиск", id="btn_search", variant="default", classes="-active"
            )
            yield Button("󰓇  Моя волна", id="btn_wave", variant="default")
            yield Button("󰒍  Очередь", id="btn_toggle_queue")
            yield Static(classes="separator")
            yield Label("МЕДИАТЕКА", classes="section-title")
            yield Button("󰓦  Плейлисты", id="btn_playlists")
            yield Button("󰓀  Альбомы", id="btn_albums")
