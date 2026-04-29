from __future__ import annotations

import math
import random
from typing import Final, Any

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Header, Footer, Static, Button, Label, ProgressBar
from textual.binding import Binding

from ui.utils.socket_client import SocketClient
from ui.viewmodels.search import SearchViewModel
from ui.viewmodels.player import PlayerViewModel
from ui.viewmodels.auth import AuthViewModel
from ui.viewmodels.queue import QueueViewModel
from ui.views.auth_screen import AuthScreen
from ui.views.search_view import SearchView
from ui.views.log_view import LogPanel
from ui.widgets.queue_drawer import QueueDrawer
from ui.infrastructure.hotkeys import PynputHotkeyProvider


class Visualizer(Static):
    def on_mount(self) -> None:
        self.width_cells: int = 30
        self.points: list[float] = [0.0] * self.width_cells
        self.phase: float = 0.0
        self.set_interval(0.05, self._update_wave)

    def _update_wave(self) -> None:
        app = self.app
        if not isinstance(app, MusicPlayerApp):
            return

        if app.player_vm.is_playing:
            self.phase += 0.5
            self.points = [
                (math.sin(self.phase + i * 0.5) * 2 + random.uniform(-1, 1))
                for i in range(self.width_cells)
            ]
            self.update(self._render_wave())
        else:
            self.points = [p * 0.8 for p in self.points]
            self.update(self._render_wave())

    def _render_wave(self) -> str:
        glyphs: Final = " ▂▃▄▅▆▇█"
        res = ""
        for p in self.points:
            idx = int(abs(p) * 2) % len(glyphs)
            color = "$accent" if abs(p) < 1.5 else "white"
            res += f"[{color}]{glyphs[idx]}[/]"
        return res


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


class MusicPlayerApp(App[None]):
    CSS_PATH = [
        "views/statics/app.tcss",
        "views/statics/queue_drawer.tcss",
        "views/statics/search_view.tcss",
        "views/statics/log_panel.tcss",
    ]

    BINDINGS = [
        Binding("q", "quit", "Выход", show=True),
        Binding("ctrl+l", "toggle_logs", "Логи", show=True),
        Binding("ctrl+q", "toggle_queue", "Очередь", show=True),
        Binding("p", "toggle_play", "Плей/Пауза", show=False),
        Binding("n", "next_track", "След.", show=False),
        Binding("b", "prev_track", "Пред.", show=False),
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.client: Final[SocketClient] = SocketClient(host="127.0.0.1", port=8888)

        self.search_vm: Final[SearchViewModel] = SearchViewModel(self.client)
        self.player_vm: Final[PlayerViewModel] = PlayerViewModel(self.client)
        self.auth_vm: Final[AuthViewModel] = AuthViewModel(self.client)
        self.queue_vm: Final[QueueViewModel] = QueueViewModel(self.client)

        self.player_vm.subscribe(self._on_player_update)
        self._hotkey_provider: Final[PynputHotkeyProvider] = PynputHotkeyProvider()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Sidebar(id="sidebar")
        with Horizontal(id="main_content"):
            with Container(id="main_container"):
                yield SearchView(viewmodel=self.search_vm, id="search_view")
            yield QueueDrawer(
                viewmodel=self.queue_vm, id="queue_drawer", classes="-hidden"
            )
        yield PlayerBar(id="player_bar")
        yield LogPanel(id="log_panel")
        yield Footer()

    def on_mount(self) -> None:
        if not self.auth_vm.is_authenticated("yandex"):
            self.push_screen(AuthScreen(self.auth_vm))

        self._hotkey_provider.start(lambda action: self._on_hotkey(action))
        self.set_interval(1.0, self._tick_timer)

    def _on_hotkey(self, action: str) -> None:
        self.call_from_thread(self.run_action, action)

    def action_toggle_play(self) -> None:
        """Переключение воспроизведения через Worker (Thread-safe)."""
        self.run_worker(self.player_vm.toggle_pause())

    def action_next_track(self) -> None:
        self.run_worker(self.player_vm.next_track())

    def action_prev_track(self) -> None:
        self.run_worker(self.player_vm.prev_track())

    def action_toggle_logs(self) -> None:
        self.query_one(LogPanel).toggle_class("-visible")

    def action_toggle_queue(self) -> None:
        drawer = self.query_one(QueueDrawer)
        drawer.toggle_class("-hidden")
        if not drawer.has_class("-hidden"):
            self.run_worker(self.queue_vm.load_queue())

    def _tick_timer(self) -> None:
        """Мнимый таймер для обновления прогресса."""
        if self.player_vm.is_playing:
            self.player_vm.position_ms += 1000
            if self.player_vm.position_ms > self.player_vm.duration_ms:
                self.player_vm.position_ms = 0
            self._on_player_update()

    def _format_time(self, ms: int) -> str:
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def _on_player_update(self) -> None:
        """Реакция на изменения в PlayerViewModel."""
        try:
            if self.player_vm.current_track:
                self.query_one("#current_track", TickerLabel).update_text(
                    f"󰓇 {self.player_vm.current_track}"
                )
                btn_play = self.query_one("#btn_play_pause", Button)
                btn_play.label = "󰏤" if self.player_vm.is_playing else "󰐊"

            # Обновление времени и прогресс-бара
            pos_str = self._format_time(self.player_vm.position_ms)
            dur_str = self._format_time(self.player_vm.duration_ms)
            self.query_one("#time_code", Label).update(f"{pos_str} / {dur_str}")

            vol_bar = self.query_one("#volume_bar", ProgressBar)
            vol_bar.progress = float(self.player_vm.volume)

            track_progress = self.query_one("#track_progress", ProgressBar)
            if self.player_vm.duration_ms > 0:
                track_progress.progress = (
                    self.player_vm.position_ms / self.player_vm.duration_ms
                ) * 100
        except Exception:
            pass

    @on(Button.Pressed, "#btn_play_pause")
    def handle_play_pause(self) -> None:
        self.action_toggle_play()

    @on(Button.Pressed, "#btn_next")
    def handle_next(self) -> None:
        self.action_next_track()

    @on(Button.Pressed, "#btn_prev")
    def handle_prev(self) -> None:
        self.action_prev_track()

    @on(Button.Pressed, "#btn_toggle_queue")
    def handle_toggle_queue(self) -> None:
        self.action_toggle_queue()

    @on(Button.Pressed, "#btn_search")
    def handle_sidebar_search(self) -> None:
        self.notify("Поиск уже активен", severity="information")

    @on(Button.Pressed, "#btn_wave")
    def handle_my_wave(self) -> None:
        self.notify("󰓇 Запуск Моей Волны...", severity="information")

    @on(Button.Pressed, "#btn_playlists")
    def handle_playlists(self) -> None:
        self.notify("Плейлисты: Функция в разработке", severity="information")

    @on(Button.Pressed, "#btn_albums")
    def handle_albums(self) -> None:
        self.notify("Альбомы: Функция в разработке", severity="information")


if __name__ == "__main__":
    MusicPlayerApp().run()
