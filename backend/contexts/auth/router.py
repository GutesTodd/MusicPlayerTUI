from dishka import FromDishka
from yandex_music import ClientAsync

from backend.contexts.auth.domain import AuthSessionStore
from backend.contexts.auth.use_cases import YandexDeviceAuthFlow
from shared.domain.commands import AuthCommand, GetAuthCodeCommand, GetAuthStatusCommand
from shared.infrastructure.socket.app import SocketRouter

router = SocketRouter(AuthCommand)


@router.handler
async def get_auth_code(
    cmd: GetAuthCodeCommand,
    flow: FromDishka[YandexDeviceAuthFlow],
    client: FromDishka[ClientAsync],
) -> dict:
    """Запускает процесс получения кода для Device Flow."""
    user_code, url = await flow.start_auth(client)
    return {"status": "pending", "user_code": user_code, "verification_url": url}


@router.handler
async def check_auth_status(
    cmd: GetAuthStatusCommand, store: FromDishka[AuthSessionStore]
) -> dict:
    """Возвращает текущий статус процесса авторизации."""
    status = store.get_status()
    return {
        "status": status.status.value,
        "user_code": status.user_code,
        "verification_url": status.verification_url,
        "error": status.error_message,
    }
