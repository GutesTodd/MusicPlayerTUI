import threading

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Select, Static

from ui.viewmodels.auth import AuthViewModel


class AuthScreen(Screen):
    CSS_PATH = "statics/auth_screen.tcss"

    def __init__(self, viewmodel: AuthViewModel, **kwargs):
        super().__init__(**kwargs)
        self.vm = viewmodel

    def compose(self) -> ComposeResult:
        with Center(), Vertical(id="auth_dialog"):
            yield Label("Вход в Music Player", id="auth_title")

            # Контейнер выбора платформы
            with Vertical(id="platform_selection"):
                yield Select(
                    self.vm.platforms,
                    prompt="Выберите сервис",
                    id="platform_select",
                )
                yield Button("Получить код", variant="primary", id="btn_get_code")

            # Контейнер отображения кода (скрыт по умолчанию)
            with Vertical(id="code_display"):
                yield Label(
                    "Введите этот код на странице подтверждения:", id="instructions"
                )
                yield Label("", id="user_code_label")
                yield Static("", id="link_label")
                yield Label("Ожидание подтверждения...", id="polling_status")

            yield Label("", id="auth_error")

    def on_mount(self) -> None:
        self.vm.subscribe(self.update_ui_state)
        self.update_ui_state()

    def on_unmount(self) -> None:
        self.vm.unsubscribe(self.update_ui_state)
        self.vm.stop_polling()

    def update_ui_state(self) -> None:
        if getattr(self.app, "_thread_id", None) == threading.get_ident():
            self._perform_update()
        else:
            try:
                self.app.call_from_thread(self._perform_update)
            except RuntimeError:
                self._perform_update()

    def _perform_update(self) -> None:
        error_label = self.query_one("#auth_error", Label)
        error_label.update(self.vm.error_message or "")

        platform_sel = self.query_one("#platform_selection")
        code_disp = self.query_one("#code_display")

        if self.vm.auth_code:
            platform_sel.display = False
            code_disp.display = True

            self.query_one("#user_code_label", Label).update(self.vm.auth_code)

            link = self.vm.auth_url or "https://yandex.ru/device"
            self.query_one("#link_label", Static).update(
                f"Перейдите по ссылке: [link='{link}']{link}[/link]"
            )
        else:
            platform_sel.display = True
            code_disp.display = False

        if self.vm.is_authenticated_successfully:
            self.app.notify("Авторизация успешна!")
            self.app.pop_screen()

        btn = self.query_one("#btn_get_code", Button)
        btn.disabled = self.vm.is_loading
        if self.vm.is_loading:
            btn.label = "Загрузка..."
        else:
            btn.label = "Получить код"

    @on(Button.Pressed, "#btn_get_code")
    @work(exclusive=True)
    async def handle_get_code(self) -> None:
        platform = self.query_one("#platform_select", Select).value
        if not platform or platform == Select.BLANK:
            self.vm.set_error("Выберите платформу")
            return

        await self.vm.request_device_code(str(platform))
