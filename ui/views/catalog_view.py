from __future__ import annotations

import contextlib

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Label, Static

from shared.domain.entities import Album, Track
from ui.viewmodels.catalog import AlbumDetailViewModel, ArtistDetailViewModel


class TrackItem(Static):
    def __init__(self, track: Track, **kwargs):
        super().__init__(**kwargs)
        self.track = track

    def compose(self) -> ComposeResult:
        yield Label(
            f"󰎈 {self.track.title} — {', '.join(a.name for a in self.track.artists)}"
        )

    def on_click(self) -> None:
        self.app.run_worker(
            self.app.player_vm.play_media(
                media_id=str(self.track.id),
                media_type="track",
                title=self.track.title,
                artist=", ".join(a.name for a in self.track.artists),
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
            yield VerticalScroll(id="album_tracks")

    def on_mount(self) -> None:
        self.app.run_worker(self.vm.load_album(self.album_id))

    def on_data_changed(self) -> None:
        with contextlib.suppress(Exception):
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

                tracks_container = self.query_one("#album_tracks", VerticalScroll)
                tracks_container.remove_children()
                if album.tracks:
                    for track in album.tracks:
                        tracks_container.mount(TrackItem(track))
                else:
                    tracks_container.mount(Label("Нет данных о треках"))

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
                yield Vertical(id="popular_tracks", classes="detail-section")

                yield Label("Альбомы", classes="section-title")
                yield Vertical(id="artist_albums", classes="detail-section")

                yield Label("Синглы", classes="section-title")
                yield Vertical(id="artist_singles", classes="detail-section")

    def on_mount(self) -> None:
        self.app.run_worker(self.vm.load_artist(self.artist_id))

    def on_data_changed(self) -> None:
        with contextlib.suppress(Exception):
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
                    pop_container = self.query_one("#popular_tracks", Vertical)
                    pop_container.remove_children()
                    for track in artist.details.popular_tracks:
                        pop_container.mount(TrackItem(track))
                    alb_container = self.query_one("#artist_albums", Vertical)
                    alb_container.remove_children()
                    for album in artist.details.albums:
                        alb_container.mount(AlbumItem(album))
                    sin_container = self.query_one("#artist_singles", Vertical)
                    sin_container.remove_children()
                    for single in artist.details.singles:
                        sin_container.mount(AlbumItem(single))

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
