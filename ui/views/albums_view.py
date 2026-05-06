from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Button, Label, Static, ContentSwitcher
from textual.message import Message
from shared.domain.entities import Album
from ui.viewmodels.catalog import AlbumDetailViewModel
from ui.viewmodels.albums import AlbumListViewModel
from ui.views.catalog_view import AlbumDetailView

class AlbumListItem(Static):
    """Виджет альбома в общем списке."""
    def __init__(self, album: Album, **kwargs):
        super().__init__(**kwargs)
        self.album = album

    def compose(self) -> ComposeResult:
        yield Label(f"󰓀 {self.album.title} ({self.album.year or '?'})")

    def on_click(self) -> None:
        self.post_message(self.Selected(self.album.id))

    class Selected(Message):
        def __init__(self, album_id: str | int):
            self.album_id = str(album_id)
            super().__init__()

class UserAlbumsView(Static):
    def __init__(self, list_vm: AlbumListViewModel, detail_vm: AlbumDetailViewModel, **kwargs):
        super().__init__(**kwargs)
        self.list_vm = list_vm
        self.detail_vm = detail_vm
        self.list_vm.subscribe(self.on_data_changed)

    def compose(self) -> ComposeResult:
        with ContentSwitcher(initial="album_list", id="album_switcher"):
            with VerticalScroll(id="album_list"):
                yield Label("Мои Альбомы", classes="section-title")
                yield Vertical(id="albums_container")
            
            with Vertical(id="album_detail"):
                # Контейнер для деталей альбома
                pass

    def on_mount(self) -> None:
        self.app.run_worker(self.list_vm.load_user_albums())

    def on_data_changed(self) -> None:
        if self.list_vm.is_loading: return
        
        container = self.query_one("#albums_container", Vertical)
        container.remove_children()
        for a in self.list_vm.albums:
            container.mount(AlbumListItem(a))

    @on(AlbumListItem.Selected)
    def on_album_selected(self, event: AlbumListItem.Selected) -> None:
        # Переключаемся на детали альбома
        detail_view = AlbumDetailView(self.detail_vm, event.album_id)
        detail_container = self.query_one("#album_detail", Vertical)
        detail_container.remove_children()
        detail_container.mount(detail_view)
        self.query_one("#album_switcher", ContentSwitcher).current = "album_detail"

    @on(AlbumDetailView.GoBack)
    def handle_back(self) -> None:
        self.query_one("#album_switcher", ContentSwitcher).current = "album_list"
