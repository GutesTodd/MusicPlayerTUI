import inspect
from typing import Callable, get_type_hints, get_args, Type, TypeVar, Any, Optional

from shared.domain.common import BaseCommand

BC = TypeVar("BC", bound=BaseCommand)


class SocketRouter:
    def __init__(self, base_schema: Type[BC]):
        self.base_schema = base_schema
        self.routes = {}

        annotation = base_schema.model_fields["action"].annotation
        self.prefix = get_args(annotation)[0]

    def handler(self, func: Optional[Callable[..., Any]] = None):
        def decorator(f: Callable[..., Any]):
            hints = get_type_hints(f)
            cmd_type = next(
                (
                    t
                    for t in hints.values()
                    if inspect.isclass(t) and issubclass(t, BaseCommand)
                ),
                None,
            )

            if not cmd_type:
                raise TypeError(
                    f"Хэндлер '{f.__name__}' должен принимать аргумент типа BaseCommand"
                )

            if not issubclass(cmd_type, self.base_schema):
                raise TypeError(
                    f"Хэндлер '{f.__name__}' ожидает {cmd_type.__name__}, но роутер настроен на {self.base_schema.__name__}"
                )

            annotation = cmd_type.model_fields["action"].annotation
            action_route = get_args(annotation)[0]

            self.routes[action_route] = (f, cmd_type)
            return f

        if func:
            return decorator(func)
        return decorator
