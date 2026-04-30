from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label, Static

from ui.viewmodels.queue import QueueViewModel


class QueueItem(Static):
    def __init__(self, title: str, artist: str, is_current: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.artist = artist
        self.is_current = is_current
        self.can_focus = True

    def compose(self) -> ComposeResult:
        icon = "󰐊 " if self.is_current else "  "
        yield Label(f"{icon}{self.artist} — {self.title}")
        if self.is_current:
            self.add_class("current-track")

    def on_click(self) -> None:
        self.app.notify(
            f"Выбран трек: {self.artist} — {self.title}", severity="information"
        )


class QueueDrawer(Vertical):  # Изменили на Vertical
    def __init__(self, viewmodel: QueueViewModel, **kwargs):
        super().__init__(**kwargs)
        self.vm = viewmodel
        self.vm.subscribe(self.on_data_changed)

    def compose(self) -> ComposeResult:
        yield Label("󰎈 ОЧЕРЕДЬ ВОСПРОИЗВЕДЕНИЯ", id="queue_title")
        with Horizontal(id="queue_controls"):
            yield Button("󰒮 Назад", id="btn_prev", variant="default")
            yield Button("Вперед 󰒭", id="btn_next", variant="default")

        yield Static(classes="queue-separator")
        yield Label("⌛ Загрузка...", id="queue_loading")
        with VerticalScroll(id="queue_list"):
            pass

    def on_data_changed(self) -> None:
        self.refresh_queue()

    def refresh_queue(self) -> None:
        try:
            loading = self.query_one("#queue_loading", Label)
            container = self.query_one("#queue_list", VerticalScroll)

            if self.vm.is_loading:
                loading.display = True
                return

            loading.display = False
            container.remove_children()

            for track in self.vm.tracks:
                is_active = str(track.get("id")) == str(self.vm.current_track_id)
                container.mount(
                    QueueItem(
                        title=track.get("title", "Unknown"),
                        artist=", ".join(
                            a.get("name") for a in track.get("artists", [])
                        ),
                        is_current=is_active,
                    )
                )
        except Exception:
            # Виджет может быть еще не смонтирован
            pass

    @on(Button.Pressed, "#btn_next")
    async def on_next(self) -> None:
        await self.vm.next_track()

    @on(Button.Pressed, "#btn_prev")
    async def on_prev(self) -> None:
        await self.vm.prev_track()
