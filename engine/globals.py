import arcade.gui
import logging
import colorlog
import sys
import os

class Globals:
    def __init__(self):
        self._handlers = self._create_handlers()

    @staticmethod
    def get_save_path():
        if os.name == 'nt':  # Windows
            # Используем %APPDATA% (C:\Users\Имя\AppData\Roaming\Название_игры)
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
            save_dir = os.path.join(app_data, 'OneDay')
        else:
            # Linux/Mac
            save_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'OneDay')

        os.makedirs(save_dir, exist_ok=True)
        return save_dir

    def _create_handlers(self):
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

        class CustomLogger(logging.Logger):
            def event(self, message, *args, **kwargs):
                if self.isEnabledFor(5):
                    self._log(5, message, args, **kwargs)

        logging.addLevelName(5, "EXECUTE")
        logging.setLoggerClass(CustomLogger)

        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - [%(name)s] - [%(levelname)s]: %(message)s',
            datefmt='%H:%M:%S',
            log_colors={
                "DEBUG": "white",
                "EXECUTE": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            }
        ))

        save_folder = self.get_save_path()
        file_handler = logging.FileHandler(os.path.join(save_folder, "latest.log"), "w", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - [%(name)s] - [%(levelname)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))

        return [console_handler, file_handler]

    @property
    def handlers(self):
        return self._handlers

    def get_logger(self, name):
        logger = colorlog.getLogger(name)

        if not logger.handlers:
            for handler in self.handlers:
                logger.addHandler(handler)

        logger.setLevel(5)
        return logger

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
                border_width=5
            ),
            "hover": arcade.gui.UIFlatButton.UIStyle(
                font_size=16,
                font_name=(self.FONT_NAME,),
                font_color=arcade.color.BLACK,
                bg=(163, 134, 5, 255),
                border=(79, 67, 13, 255),
                border_width=5
            ),
            "press": arcade.gui.UIFlatButton.UIStyle(
                font_size=16,
                font_name=(self.FONT_NAME,),
                font_color=arcade.color.BLACK,
                bg=(191, 161, 25, 255),
                border=(79, 67, 13, 255),
                border_width=5
            ),
            "disabled": arcade.gui.UIFlatButton.UIStyle(
                font_size=16,
                font_name=(self.FONT_NAME,),
                font_color=arcade.color.LIGHT_STEEL_BLUE,
                bg=(66, 71, 77)
            )
        }

    @property
    def DEFAULT_DATA_FILE_NAME(self):
        return "data.json"

    fm = None  # Files manager
    sm = None  # Saves manager
    am = None  # Audio manager
    scene = None  # Scene
    wwl = None  # Work with lore
    da = None  # Discord actor

    All_views = None

    ListCharacters = None

    attributes = None

    main = None


g = Globals()