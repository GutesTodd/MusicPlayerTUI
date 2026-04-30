import asyncio

from loguru import logger
from yandex_music import ClientAsync

from backend.contexts.auth.domain import AuthSessionStore, AuthStatusEnum
from backend.infrastructure.config.service import ConfigService


class YandexDeviceAuthFlow:
    def __init__(self, session_store: AuthSessionStore, config_service: ConfigService):
        self.session_store = session_store
        self.config_service = config_service
        self._background_tasks = set()

    async def start_auth(self, global_client: ClientAsync):
        status = self.session_store.get_status()
        if status and status.status == AuthStatusEnum.PENDING:
            logger.warning("Попытка запустить авторизацию, пока она уже идет.")
            return status.user_code, status.verification_url

        loop = asyncio.get_running_loop()
        code_future = loop.create_future()

        def on_code_callback(code):
            user_code = code.user_code
            verification_url = code.verification_url
            logger.info(f"Получен код авторизации: {user_code}")
            code_future.set_result((user_code, verification_url))

        try:
            fresh_client = ClientAsync()
            auth_task = asyncio.create_task(
                fresh_client.device_auth(on_code=on_code_callback)
            )
            self._background_tasks.add(auth_task)
            auth_task.add_done_callback(self._background_tasks.discard)

            user_code, verification_url = await code_future
            self.session_store.update(
                status=AuthStatusEnum.PENDING,
                user_code=user_code,
                verification_url=verification_url,
            )
            task = asyncio.create_task(
                self._wait_for_completion(auth_task, global_client)
            )
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            return user_code, verification_url

        except Exception as e:
            logger.exception("Ошибка при запуске Device Auth")
            self.session_store.update(status=AuthStatusEnum.ERROR, error_message=str(e))
            raise

    async def _wait_for_completion(self, auth_task, client: ClientAsync):
        try:
            token_obj = await auth_task
            token_str = getattr(token_obj, "access_token", token_obj)
            if token_str:
                client.token = token_str
                self.config_service.save_token(token_str)
                await client.init()
                self.session_store.update(status=AuthStatusEnum.SUCCESS)
                logger.success("Авторизация успешно завершена")
            else:
                raise RuntimeError("Токен не был получен после завершения flow")

        except Exception as e:
            logger.error(f"Ошибка во время ожидания подтверждения авторизации: {e}")
            self.session_store.update(status=AuthStatusEnum.ERROR, error_message=str(e))
