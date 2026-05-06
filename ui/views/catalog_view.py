from __future__ import annotations

from loguru import logger
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Label, Static, OptionList

from shared.domain.entities import Album, Track
from ui.viewmodels.catalog import AlbumDetailViewModel, ArtistDetailViewModel


class TrackItem(Static):
    def __init__(
        self,
        track: Track,
        context_id: str | None = None,
        context_type: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.track = track
        self.context_id = context_id
        self.context_type = context_type

    def compose(self) -> ComposeResult:
        yield Label(
            f"󰎈 {self.track.title} — {', '.join(a.name for a in self.track.artists)}"
        )

    def on_click(self) -> None:
        media_id = self.context_id or str(self.track.id)
        media_type = self.context_type or "track"
        start_from = str(self.track.id) if self.context_id else None

        self.app.run_worker(
            self.app.player_vm.play_media(
                media_id=media_id,
                media_type=media_type,
                title=self.track.title,
                artist=", ".join(a.name for a in self.track.artists),
                duration_ms=self.track.duration_ms,
                start_from_track_id=start_from,
            )
        )


class AlbumItem(Static):
    def __init__(self, album: Album, **kwargs):
        super().__init__(**kwargs)
        self.album = album

    def compose(self) -> ComposeResult:
        yield Label(f"󰓀 {self.album.title} ({self.album.year or '?'})")

    def on_click(self) -> None:
        self.post_message(self.Selected(self.album))

    class Selected(Message):
        def __init__(self, album: Album):
            self.album = album
            super().__init__()


class AlbumDetailView(Static):
    def __init__(self, viewmodel: AlbumDetailViewModel, album_id: str, **kwargs):
        super().__init__(**kwargs)
        self.vm = viewmodel
        self.album_id = album_id
        self.vm.subscribe(self.on_data_changed)

    def compose(self) -> ComposeResult:
        with Vertical(id="album_detail_container"):
            with Horizontal(id="album_header"):
                yield Button("󰁍 Назад", id="btn_back")
                yield Label(id="album_title", classes="detail-title")
            yield Label(id="album_info")
            yield Label("Список треков:", classes="section-title")
            yield OptionList(id="album_tracks_list")

    def on_mount(self) -> None:
        self.app.run_worker(self.vm.load_album(self.album_id))

    def on_unmount(self) -> None:
        self.vm.unsubscribe(self.on_data_changed)

    def on_data_changed(self) -> None:
        try:
            if self.vm.is_loading:
                self.query_one("#album_title", Label).update("⏳ Загрузка альбома...")
                return

            if self.vm.error_message:
                self.query_one("#album_title", Label).update(f"{self.vm.error_message}")
                return

            if self.vm.album:
                album = self.vm.album
                self.query_one("#album_title", Label).update(f"󰓀 {album.title}")
                self.query_one("#album_info", Label).update(
                    f"Исполнитель: {', '.join(a.name for a in album.artists)}"
                    f"| Год: {album.year or '?'}"
                )

                list_widget = self.query_one("#album_tracks_list", OptionList)
                list_widget.clear_options()
                if album.tracks:
                    for track in album.tracks:
                        list_widget.add_option(
                            f"󰎈 {track.title} — {', '.join(a.name for a in track.artists)}"
                        )
                else:
                    list_widget.add_option("Нет данных о треках")
        except Exception as e:
            logger.error(f"Ошибка рендеринга AlbumDetailView: {e}")

    @on(OptionList.OptionSelected, "#album_tracks_list")
    def on_track_selected(self, event: OptionList.OptionSelected) -> None:
        if not self.vm.album or not self.vm.album.tracks:
            return
            
        track = self.vm.album.tracks[event.option_index]
        self.app.run_worker(
            self.app.player_vm.play_media(
                media_id=self.album_id,
                media_type="album",
                title=track.title,
                artist=", ".join(a.name for a in track.artists),
                duration_ms=track.duration_ms,
                start_from_track_id=str(track.id),
            )
        )

    @on(Button.Pressed, "#btn_back")
    def handle_back(self) -> None:
        self.post_message(self.GoBack())

    class GoBack(Message):
        pass


class ArtistDetailView(Static):
    def __init__(self, viewmodel: ArtistDetailViewModel, artist_id: str, **kwargs):
        super().__init__(**kwargs)
        self.vm = viewmodel
        self.artist_id = artist_id
        self.vm.subscribe(self.on_data_changed)

    def compose(self) -> ComposeResult:
        with Vertical(id="artist_detail_container"):
            with Horizontal(id="artist_header"):
                yield Button("󰁍 Назад", id="btn_back")
                yield Label(id="artist_name", classes="detail-title")

            with VerticalScroll(id="artist_content"):
                yield Label("Популярные треки", classes="section-title")
                yield VerticalScroll(id="popular_tracks", classes="detail-section")

                yield Label("Альбомы", classes="section-title")
                yield VerticalScroll(id="artist_albums", classes="detail-section")

                yield Label("Синглы", classes="section-title")
                yield VerticalScroll(id="artist_singles", classes="detail-section")

    def on_mount(self) -> None:
        self.app.run_worker(self.vm.load_artist(self.artist_id))

    def on_unmount(self) -> None:
        self.vm.unsubscribe(self.on_data_changed)

    def on_data_changed(self) -> None:
        try:
            if self.vm.is_loading:
                self.query_one("#artist_name", Label).update("Загрузка артиста...")
                return

            if self.vm.error_message:
                self.query_one("#artist_name", Label).update(f"{self.vm.error_message}")
                return

            if self.vm.artist:
                artist = self.vm.artist
                self.query_one("#artist_name", Label).update(f"󰓦 {artist.name}")

                if artist.details:
                    pop_container = self.query_one("#popular_tracks", VerticalScroll)
                    pop_container.remove_children()
                    for track in artist.details.popular_tracks:
                        pop_container.mount(
                            TrackItem(
                                track, context_id=self.artist_id, context_type="artist"
                            )
                        )
                    alb_container = self.query_one("#artist_albums", VerticalScroll)
                    alb_container.remove_children()
                    for album in artist.details.albums:
                        alb_container.mount(AlbumItem(album))
                    sin_container = self.query_one("#artist_singles", VerticalScroll)
                    sin_container.remove_children()
                    for single in artist.details.singles:
                        sin_container.mount(AlbumItem(single))
        except Exception as e:
            logger.error(f"Ошибка рендеринга ArtistDetailView: {e}")

    @on(Button.Pressed, "#btn_back")
    def handle_back(self) -> None:
        self.post_message(self.GoBack())

    @on(AlbumItem.Selected)
    def on_album_selected(self, event: AlbumItem.Selected) -> None:
        self.post_message(self.AlbumRequested(event.album.id))

    class GoBack(Message):
        pass

    class AlbumRequested(Message):
        def __init__(self, album_id: str):
            self.album_id = album_id
            super().__init__()
