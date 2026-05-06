from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Static, OptionList

from ui.viewmodels.queue import QueueViewModel


class QueueDrawer(Vertical):
    def __init__(self, viewmodel: QueueViewModel, **kwargs):
        super().__init__(**kwargs)
        self.vm = viewmodel
        self.vm.subscribe(self.on_data_changed)

    def compose(self) -> ComposeResult:
        yield Label("󰎈 ОЧЕРЕДЬ ВОСПРОИЗВЕДЕНИЯ", id="queue_title")
        yield Static(classes="queue-separator")
        yield Label("Загрузка...", id="queue_loading")
        yield OptionList(id="queue_list_widget")

    def on_data_changed(self) -> None:
        self.refresh_queue()

    def refresh_queue(self) -> None:
        try:
            loading = self.query_one("#queue_loading", Label)
            list_widget = self.query_one("#queue_list_widget", OptionList)

            if self.vm.is_loading:
                loading.display = True
                return
            loading.display = False
            list_widget.clear_options()
            current_index = None
            for i, track in enumerate(self.vm.tracks):
                is_active = str(track.get("id")) == str(self.vm.current_track_id)
                icon = "󰐊 " if is_active else "  "
                artist = ", ".join(a.get("name") for a in track.get("artists", []))
                title = track.get("title", "Unknown")

                list_widget.add_option(f"{icon}{artist} — {title}")
                if is_active:
                    current_index = i
            if current_index is not None:
                list_widget.highlighted = current_index
                list_widget.scroll_to_highlight()
        except Exception:
            # Виджет может быть еще не смонтирован
            pass

    @on(OptionList.OptionSelected, "#queue_list_widget")
    async def on_track_selected(self, event: OptionList.OptionSelected) -> None:
        # Здесь можно добавить логику переключения на конкретный трек в очереди,
        # если бэкенд это поддерживает (например, через playback.play_from_queue)
        track = self.vm.tracks[event.option_index]
        self.app.notify(f"В очереди: {track.get('title')}", severity="information")
