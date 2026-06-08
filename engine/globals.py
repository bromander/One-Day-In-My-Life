import json
import traceback
import arcade.gui
import logging
import colorlog
import sys
import os
import re
from hawk_python_sdk import Hawk
import hawk_python_sdk.core as hawk_core
from .tk_error_inform import show_error, has_internet


class Globals:
    def __init__(self):
        self._handlers = self._create_handlers()
        self.hawk = self._get_hawk()

        self.cant_unload = []
        self.cant_unload += (
            os.listdir("./game/images/moving_shop_assets")
            + os.listdir("./game/images/bying_shop_assets")
            + ["box_office_3.png", "golub_click.png", "golub.png"]
        )

        self.cant_unload = frozenset(self.cant_unload)

    def notice_crash(self, e: Exception):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        logger = self.get_logger("__main__")

        logger.critical(text)
        show_error(exc_type, self.sm.Volume.telemetry)

        save_folder = self.get_save_path()

        file = os.path.join(save_folder, "latest_full.log")

        def get_full_logs():
            with open(file, "r", encoding="UTF-8") as logs:
                logs = logs.read()
            return [i for i in logs.split("\n")]

        custom_data = {"logs": str(get_full_logs())}

        if g.sm.Volume.telemetry and has_internet:
            self.hawk.send(e, context=custom_data)
        else:
            logger.error(
                "Не получилось отправить лог! Отсутствует подключение к интернету или отключена телеметрия..."
            )

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

        save_folder = self.get_save_path()
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

        save_folder = self.get_save_path()
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
            for handler in self.handlers:
                logger.addHandler(handler)

        logger.setLevel(5)
        return logger

    @staticmethod
    def get_save_path():
        if os.name == "nt":  # Windows
            # Используем %APPDATA% (C:\Users\Имя\AppData\Roaming\Название_игры)
            app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
            save_dir = os.path.join(app_data, "OneDay")
        else:
            # Linux/Mac
            save_dir = os.path.join(
                os.path.expanduser("~"), ".local", "share", "OneDay"
            )

        os.makedirs(save_dir, exist_ok=True)
        return save_dir

    @staticmethod
    def _get_hawk():

        def _safe_get_near_filelines(filepath, line, margin=10):
            with open(filepath, encoding="UTF-8") as file:
                content = file.readlines()
                content = [x.rstrip() for x in content]

            error_line_in_array = line - 1
            start = max(0, error_line_in_array - margin)

            end = min(len(content), error_line_in_array + margin + 1)

            lines = content[start:end]

            pon = [
                {"line": array_line + 1, "content": lines[array_line - start]}
                for array_line in range(start, end)
            ]

            return pon

        hawk_core.Hawk.get_near_filelines = staticmethod(_safe_get_near_filelines)

        with open("./game/game_data.JSON", "r", encoding="UTF-8") as f:
            f = json.load(f)
            key = f["hawk_integration_API"]
        hawk = Hawk(key)
        return hawk

    @property
    def handlers(self):
        return self._handlers

    @property
    def TOPICAL_SAVES_VERSION(self):
        return 0

    @property
    def DEFAULT_OPTIONS_PARAM(self):
        return {
            "volume": {"music": 1.0, "sound": 1.0, "voice": 1.0},
            "lps": 1.0,
            "fade_speed": 1.0,
            "show_fps": False,
            "window_mode": "full-screen",
            "telemetry": True,
        }

    @property
    def DEFAULT_IN_GAME_WINDOW_SIZE(self):
        return (1920, 1080)

    @property
    def GAME_NAME(self):
        return "ОДИН ДЕНЬ из моей оБыЧнОй ЖиЗнИ с моей женой соседкой которая, возможно, демон или вампир :D"

    @property
    def WINDOW_TITLE(self):
        return "ОДИН ДЕНЬ"

    @property
    def FONT_NAME(self):
        return "Kurale"

    @property
    def STYLE_DEFAULT_BUTTON(self):
        return {
            "normal": arcade.gui.UIFlatButton.UIStyle(
                font_size=16,
                font_name=(self.FONT_NAME,),
                font_color=arcade.color.BLACK,
                bg=(225, 184, 1, 255),
                border=(79, 67, 13, 255),
                border_width=5,
            ),
            "hover": arcade.gui.UIFlatButton.UIStyle(
                font_size=16,
                font_name=(self.FONT_NAME,),
                font_color=arcade.color.BLACK,
                bg=(163, 134, 5, 255),
                border=(79, 67, 13, 255),
                border_width=5,
            ),
            "press": arcade.gui.UIFlatButton.UIStyle(
                font_size=16,
                font_name=(self.FONT_NAME,),
                font_color=arcade.color.BLACK,
                bg=(191, 161, 25, 255),
                border=(79, 67, 13, 255),
                border_width=5,
            ),
            "disabled": arcade.gui.UIFlatButton.UIStyle(
                font_size=16,
                font_name=(self.FONT_NAME,),
                font_color=arcade.color.LIGHT_STEEL_BLUE,
                bg=(66, 71, 77),
            ),
        }

    @property
    def DEFAULT_DATA_FILE_NAME(self):
        return "data.json"

    @property
    def DEFAULT_LORE_FILE_EXT(self):
        return ".jpy"

    @property
    def DEFAULT_LORE_COMPILED_FILE_EXT(self):
        return ".jpyc"

    @property
    def DEFAULT_START_LABEL(self):
        return "main"

    @property
    def SUPPORTED_AUDIO_FORMATS(self):
        return frozenset((".mp3", ".wav", ".ogg"))

    @property
    def SUPPORTED_IMAGE_FORMATS(self):
        return frozenset((".png", ".jpg", ".jpeg", ".PNG", ".JPEG", ".gif", ".GIF"))

    @property
    def IGNORE_FILES_FOR_UNLOADING(self):
        return self.cant_unload

    fm = None  # Files manager
    sm = None  # Saves manager
    am = None  # Audio manager
    scene = None  # Scene
    lm = None  # Lore Manager
    da = None  # Discord actor

    actions = None

    All_views = None

    ListCharacters = None

    attributes = None

    main = None


g = Globals()
