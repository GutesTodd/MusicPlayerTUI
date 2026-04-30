from __future__ import annotations

from typing import Any, ClassVar, Final

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Button, Footer, Header, Label

from ui.infrastructure.hotkeys import PynputHotkeyProvider
from ui.utils.socket_client import SocketClient
from ui.viewmodels.auth import AuthViewModel
from ui.viewmodels.player import PlayerViewModel
from ui.viewmodels.queue import QueueViewModel
from ui.viewmodels.search import SearchViewModel
from ui.views.auth_screen import AuthScreen
from ui.views.log_view import LogPanel
from ui.views.search_view import SearchView
from ui.widgets.player_bar import PlayerBar, TickerLabel
from ui.widgets.queue_drawer import QueueDrawer
from ui.widgets.sidebar import Sidebar
from ui.widgets.slider import InteractiveSlider


class MusicPlayerApp(App[None]):
    CSS_PATH: ClassVar[list[str]] = [
        "views/statics/app.tcss",
        "views/statics/queue_drawer.tcss",
        "views/statics/search_view.tcss",
        "views/statics/log_panel.tcss",
    ]

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("q", "quit", "Выход", show=True),
        Binding("ctrl+l", "toggle_logs", "Логи", show=True),
        Binding("ctrl+q", "toggle_queue", "Очередь", show=True),
        Binding("p", "toggle_play", "Плей/Пауза", show=False),
        Binding("n", "next_track", "След.", show=False),
        Binding("b", "prev_track", "Пред.", show=False),
        Binding("right", "seek_forward(5000)", "Вперед 5с", show=False),
        Binding("left", "seek_backward(5000)", "Назад 5с", show=False),
        Binding("]", "seek_forward(30000)", "Вперед 30с", show=False),
        Binding("[", "seek_backward(30000)", "Назад 30с", show=False),
        Binding("up", "volume_up(5)", "Громкость +5%", show=False),
        Binding("down", "volume_down(5)", "Громкость -5%", show=False),
        Binding("+", "volume_up(10)", "Громкость +10%", show=False),
        Binding("=", "volume_up(10)", "Громкость +10%", show=False),
        Binding("-", "volume_down(10)", "Громкость -10%", show=False),
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

        self._hotkey_provider.start(self._on_hotkey)
        self.set_interval(1.0, self._tick_timer)

    def _on_hotkey(self, action: str) -> None:
        self.call_from_thread(self.run_action, action)

    def action_toggle_play(self) -> None:
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

    def action_seek_forward(self, ms: int) -> None:
        target = min(self.player_vm.duration_ms, self.player_vm.position_ms + ms)
        self.run_worker(self.player_vm.seek(target))

    def action_seek_backward(self, ms: int) -> None:
        target = max(0, self.player_vm.position_ms - ms)
        self.run_worker(self.player_vm.seek(target))

    def action_volume_up(self, percent: int) -> None:
        self.run_worker(self.player_vm.set_volume(self.player_vm.volume + percent))

    def action_volume_down(self, percent: int) -> None:
        self.run_worker(self.player_vm.set_volume(self.player_vm.volume - percent))

    def _tick_timer(self) -> None:
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
        try:
            if self.player_vm.current_track:
                self.query_one("#current_track", TickerLabel).update_text(
                    f"󰓇 {self.player_vm.current_track}"
                )
                btn_play = self.query_one("#btn_play_pause", Button)
                btn_play.label = "󰏤" if self.player_vm.is_playing else "󰐊"

            pos_str = self._format_time(self.player_vm.position_ms)
            dur_str = self._format_time(self.player_vm.duration_ms)
            self.query_one("#time_code", Label).update(f"{pos_str} / {dur_str}")

            vol_bar = self.query_one("#volume_bar", InteractiveSlider)
            if not vol_bar._dragging:
                vol_bar.value = self.player_vm.volume / 100

            btn_repeat = self.query_one("#btn_repeat", Button)
            repeat_icons = {"none": "󰑗", "all": "󰑖", "one": "󰑘"}
            btn_repeat.label = repeat_icons.get(self.player_vm.repeat_mode, "󰑗")
            if self.player_vm.repeat_mode != "none":
                btn_repeat.add_class("-active")
            else:
                btn_repeat.remove_class("-active")

            track_progress = self.query_one("#track_progress", InteractiveSlider)
            if self.player_vm.duration_ms > 0 and not track_progress._dragging:
                track_progress.value = (
                    self.player_vm.position_ms / self.player_vm.duration_ms
                )
        except Exception:
            pass

    @on(Button.Pressed, "#btn_repeat")
    def handle_repeat(self) -> None:
        self.run_worker(self.player_vm.toggle_repeat())

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
