import colorlog
import sys
import re
import os
import logging
from .globals import g


def _get_save_path() -> str:
    if os.name == "nt":  # Windows
        # Используем %APPDATA% (C:\Users\Имя\AppData\Roaming\Название_игры)
        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        save_dir = os.path.join(app_data, g.GAME_SAVES_FOLDER_NAME)
    else:
        # Linux/Mac
        save_dir = os.path.join(
            os.path.expanduser("~"), ".local", "share", g.GAME_SAVES_FOLDER_NAME
        )

    os.makedirs(save_dir, exist_ok=True)
    return save_dir

class LoggerManager:

    def __init__(self):
        self._handlers = self._create_handlers()

    def _create_handlers(self):
        if sys.platform == "win32":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

        class Tee:
            def __init__(self, file_path):
                self.file = open(file_path, "w", encoding="utf-8")

                self.stdout = sys.stdout
                self.stderr = sys.stderr

                self.ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

            def write(self, data):
                # В консоль — как есть
                self.stdout.write(data)

                # В файл — без ANSI
                clean = self.ANSI_ESCAPE.sub("", data)
                self.file.write(clean)

                self.stdout.flush()
                self.file.flush()

            def flush(self):
                self.stdout.flush()
                self.file.flush()

        save_folder = _get_save_path()
        file = os.path.join(save_folder, "latest_full.log")
        tee = Tee(file)

        sys.stdout = tee
        sys.stderr = tee

        class CustomLogger(logging.Logger):
            def event(self, message, *args, **kwargs):
                if self.isEnabledFor(5):
                    self._log(5, message, args, **kwargs)

        logging.addLevelName(5, "EXECUTE")
        logging.setLoggerClass(CustomLogger)

        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s - [%(name)s] - [%(levelname)s]: %(message)s",
                datefmt="%H:%M:%S",
                log_colors={
                    "DEBUG": "white",
                    "EXECUTE": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            )
        )

        save_folder = _get_save_path()
        file_handler = logging.FileHandler(
            os.path.join(save_folder, "latest.log"), "w", encoding="utf-8"
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - [%(name)s] - [%(levelname)s]: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        return [console_handler, file_handler]

    def get_logger(self, name):
        logger = colorlog.getLogger(name)

        if not logger.handlers:
            for handler in self._handlers:
                logger.addHandler(handler)

        logger.setLevel(5)
        return logger

get_logger = LoggerManager().get_logger