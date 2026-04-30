import atexit
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

from loguru import logger

# Глобальная переменная для процесса бэкенда
backend_proc = None


def cleanup():
    """Гарантированная остановка бэкенда при выходе."""
    global backend_proc
    if backend_proc and backend_proc.poll() is None:
        logger.info("Завершение процесса бэкенда...")
        backend_proc.terminate()
        try:
            backend_proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            backend_proc.kill()
        logger.info("Бэкенд успешно остановлен.")


def signal_handler(sig, frame):
    """Обработка системных сигналов."""
    sys.exit(0)


atexit.register(cleanup)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def is_port_open(host: str, port: int) -> bool:
    """Проверяет, открыт ли TCP-порт."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def start_backend():
    """Запускает бэкенд как модуль."""
    logger.info("Запуск бэкенда...")

    # Создаем папку для логов, если её нет
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    err_log = (log_dir / "backend_errors.log").open("a")

    return subprocess.Popen(
        [sys.executable, "-m", "backend.main"],
        cwd=str(Path.cwd()),
        stdout=subprocess.DEVNULL,
        stderr=err_log,
    )


def main():
    global backend_proc

    # 1. Проверяем, не запущен ли уже бэкенд
    if not is_port_open("127.0.0.1", 8888):
        backend_proc = start_backend()

        # Ждем запуска (максимум 5 секунд)
        for _ in range(10):
            if is_port_open("127.0.0.1", 8888):
                logger.success("Бэкенд успешно запущен.")
                break
            time.sleep(0.5)
        else:
            logger.error("Не удалось дождаться запуска бэкенда.")
            if backend_proc:
                backend_proc.terminate()
            sys.exit(1)
    else:
        logger.info("Бэкенд уже запущен.")

    # 2. Запускаем UI
    logger.info("Запуск интерфейса...")
    try:
        # Импортируем и запускаем прямо в этом процессе для лучшей интеграции
        from ui.main import MusicPlayerApp

        app = MusicPlayerApp()
        app.run()
    except Exception as e:
        logger.exception(f"Критическая ошибка UI: {e}")
    finally:
        cleanup()


if __name__ == "__main__":
    # Фиксируем рабочую директорию как корень проекта (где лежит launcher.py)
    base_dir = Path(__file__).parent.resolve()
    os.chdir(base_dir)
    sys.path.append(str(base_dir))

    # Проверка критических директорий
    for d in ["backend", "ui", "shared"]:
        if not (base_dir / d).is_dir():
            logger.error(f"Критическая ошибка: Директория {d} не найдена в {base_dir}")
            sys.exit(1)

    main()
