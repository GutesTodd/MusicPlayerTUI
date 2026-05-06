from __future__ import annotations
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Button, Label, Static, ContentSwitcher, OptionList
from textual.message import Message
from shared.domain.entities import Playlist
from ui.viewmodels.playlists import PlaylistViewModel


class PlaylistItem(Static):
    """Виджет плейлиста в общем списке."""

    def __init__(self, playlist: Playlist, **kwargs):
        super().__init__(**kwargs)
        self.playlist = playlist

    def compose(self) -> ComposeResult:
        icon = "󰎈" if self.playlist.title != "Мне нравится" else "<3"
        yield Label(f"{icon} {self.playlist.title} ({self.playlist.track_count})")

    def on_click(self) -> None:
        self.post_message(self.Selected(self.playlist.kind))

    class Selected(Message):
        def __init__(self, playlist_id: str | int):
            self.playlist_id = str(playlist_id)
            super().__init__()


class PlaylistView(Static):
    def __init__(self, viewmodel: PlaylistViewModel, **kwargs):
        super().__init__(**kwargs)
        self.vm = viewmodel
        self.vm.subscribe(self.on_data_changed)

    def compose(self) -> ComposeResult:
        with ContentSwitcher(initial="playlist_list", id="playlist_switcher"):
            with VerticalScroll(id="playlist_list"):
                yield Label("Мои Плейлисты", classes="section-title")
                yield Vertical(id="playlists_container")
            with Vertical(id="playlist_detail"):
                with Horizontal(id="playlist_header"):
                    yield Button("󰁍 Назад", id="btn_back_playlists")
                    yield Label(id="playlist_title", classes="detail-title")

                yield OptionList(id="playlist_tracks_list")

    def on_mount(self) -> None:
        self.app.run_worker(self.vm.load_user_playlists())

    def on_data_changed(self) -> None:
        if self.vm.is_loading:
            return
        if (
            self.query_one("#playlist_switcher", ContentSwitcher).current
            == "playlist_list"
        ):
            container = self.query_one("#playlists_container", Vertical)
            container.remove_children()
            for p in self.vm.playlists:
                container.mount(PlaylistItem(p))
        elif self.vm.current_playlist:
            self._render_tracks()

    def _render_tracks(self) -> None:
        if not self.vm.current_playlist or not self.vm.current_playlist.tracks:
            return
        list_widget = self.query_one("#playlist_tracks_list", OptionList)
        list_widget.clear_options()
        tracks = self.vm.current_playlist.tracks
        for track in tracks:
            list_widget.add_option(
                f"󰎈 {track.title} — {', '.join(a.name for a in track.artists)}"
            )
        icon = "<3" if self.vm.current_playlist.title == "Мне нравится" else "󰎈"
        self.query_one("#playlist_title", Label).update(
            f"{icon} {self.vm.current_playlist.title}"
        )

    @on(OptionList.OptionSelected, "#playlist_tracks_list")
    def on_track_selected(self, event: OptionList.OptionSelected) -> None:
        if not self.vm.current_playlist or not self.vm.current_playlist.tracks:
            return

        track = self.vm.current_playlist.tracks[event.option_index]
        self.app.run_worker(
            self.app.player_vm.play_media(
                media_id=str(self.vm.current_playlist.kind),
                media_type="playlist",
                title=track.title,
                artist=", ".join(a.name for a in track.artists),
                duration_ms=track.duration_ms,
                start_from_track_id=str(track.id),
            )
        )

    @on(PlaylistItem.Selected)
    def on_playlist_selected(self, event: PlaylistItem.Selected) -> None:
        self.query_one("#playlist_tracks_list", OptionList).clear_options()
        self.query_one(
            "#playlist_switcher", ContentSwitcher
        ).current = "playlist_detail"
        self.app.run_worker(self.vm.load_playlist_details(event.playlist_id))

    @on(Button.Pressed, "#btn_back_playlists")
    def handle_back(self) -> None:
        self.query_one("#playlist_switcher", ContentSwitcher).current = "playlist_list"
