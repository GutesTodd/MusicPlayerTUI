from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Input, Label, Static

from shared.domain.entities import Album, Artist, Track
from ui.viewmodels.search import SearchViewModel


class MediaItem(Static):
    class Selected(Message):
        def __init__(
            self, item: MediaItem, media_id: str, media_type: str, title: str, artist: str
        ) -> None:
            self.item = item
            self.media_id = media_id
            self.media_type = media_type
            self.title = title
            self.artist = artist
            super().__init__()

        @property
        def control(self) -> MediaItem:
            return self.item

    def __init__(
        self, media_id: str, media_type: str, title: str, artist: str, **kwargs
    ):
        super().__init__(**kwargs)
        self.media_id = media_id
        self.media_type = media_type
        self.title = title
        self.artist = artist
        self.can_focus = True

    def compose(self) -> ComposeResult:
        icon = "󰎈"
        if self.media_type == "album":
            icon = "󰓀"
        elif self.media_type == "artist":
            icon = "󰓦"

        display_text = (
            f"{icon} {self.artist} — {self.title}"
            if self.artist
            else f"{icon} {self.title}"
        )
        yield Label(display_text)

    def on_click(self) -> None:
        self.post_message(
            self.Selected(self, self.media_id, self.media_type, self.title, self.artist)
        )


class SearchView(Static):
    def __init__(self, viewmodel: SearchViewModel, **kwargs):
        super().__init__(**kwargs)
        self.vm = viewmodel
        self.vm.subscribe(self.on_data_changed)
        self.current_search_type = "track"

    def compose(self) -> ComposeResult:
        with Vertical(id="search_container"):
            with Horizontal(id="search_type_selector"):
                yield Button("Треки", id="type_track", classes="-active")
                yield Button("Альбомы", id="type_album")
                yield Button("Артисты", id="type_artist")

            yield Input(placeholder="Введите запрос...", id="search_input")
            yield Label(id="loading_indicator")
            yield VerticalScroll(id="search_results")

    @on(Button.Pressed, "#search_type_selector Button")
    def handle_type_change(self, event: Button.Pressed) -> None:
        """Обработка переключения типа поиска."""
        if not event.button.id:
            return
        for btn in self.query("#search_type_selector Button"):
            btn.remove_class("-active")
        event.button.add_class("-active")
        self.current_search_type = event.button.id.replace("type_", "")
        query = self.query_one("#search_input", Input).value
        if query.strip():
            self.run_worker(
                self.vm.search(query, search_type=self.current_search_type),
                exclusive=True,
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value
        if not query.strip():
            return

        self.run_worker(
            self.vm.search(query, search_type=self.current_search_type), exclusive=True
        )

    def on_data_changed(self) -> None:
        self._refresh_ui()

    @on(MediaItem.Selected)
    async def play_selected_media(self, event: MediaItem.Selected) -> None:
        await self.app.player_vm.play_media(  # pyright: ignore
            media_id=event.media_id,
            media_type=event.media_type,
            title=event.title,
            artist=event.artist,
        )

    def _refresh_ui(self) -> None:
        indicator = self.query_one("#loading_indicator", Label)
        results_container = self.query_one("#search_results", VerticalScroll)
        if self.vm.is_loading:
            indicator.update("⏳ Ищем в Яндексе...")
            return
        indicator.update("")
        results_container.remove_children()
        if self.vm.error_message:
            results_container.mount(Label(f"❌ Ошибка: {self.vm.error_message}"))
            return
        if not self.vm.results:
            if self.vm.last_query:
                results_container.mount(Label("Ничего не найдено."))
            return

        for item in self.vm.results:
            if isinstance(item, Track):
                results_container.mount(
                    MediaItem(
                        media_id=str(item.id),
                        media_type="track",
                        title=item.title,
                        artist=", ".join(a.name for a in item.artists),
                    )
                )
            elif isinstance(item, Album):
                results_container.mount(
                    MediaItem(
                        media_id=str(item.id),
                        media_type="album",
                        title=item.title,
                        artist=", ".join(a.name for a in item.artists),
                    )
                )
            elif isinstance(item, Artist):
                results_container.mount(
                    MediaItem(
                        media_id=str(item.id),
                        media_type="artist",
                        title=item.name,
                        artist="",
                    )
                )
