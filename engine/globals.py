import arcade.gui
import logging
import colorlog
import sys
import os
import re


class Globals:
    def __init__(self):

        self._cant_unload = []
        self._cant_unload += (
            os.listdir("./game/images/moving_shop_assets")
            + os.listdir("./game/images/bying_shop_assets")
            + ["box_office_3.png", "golub_click.png", "golub.png"]
        )

        self._cant_unload = frozenset(self._cant_unload)

    def get_save_path(self) -> str:
        if os.name == "nt":  # Windows
            # Используем %APPDATA% (C:\Users\Имя\AppData\Roaming\Название_игры)
            app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
            save_dir = os.path.join(app_data, self.GAME_SAVES_FOLDER_NAME)
        else:
            # Linux/Mac
            save_dir = os.path.join(
                os.path.expanduser("~"), ".local", "share", self.GAME_SAVES_FOLDER_NAME
            )

        os.makedirs(save_dir, exist_ok=True)
        return save_dir

    @property
    def TOPICAL_SAVES_VERSION(self) -> int:
        return 0

    @property
    def DEFAULT_OPTIONS_PARAM(self) -> dict:
        return {
            "volume": {"music": 1.0, "sound": 1.0, "voice": 1.0},
            "lps": 1.0,
            "fade_speed": 1.0,
            "show_fps": False,
            "window_mode": "full-screen",
            "telemetry": True,
        }

    @property
    def DEFAULT_IN_GAME_WINDOW_SIZE(self) -> tuple[int]:
        return (1920, 1080)

    @property
    def GAME_SAVES_FOLDER_NAME(self) -> str:
        return "OneDay"

    @property
    def GAME_NAME(self) -> str:
        return "ОДИН ДЕНЬ из моей оБыЧнОй ЖиЗнИ с моей женой соседкой которая, возможно, демон или вампир :D"

    @property
    def WINDOW_TITLE(self) -> str:
        return "ОДИН ДЕНЬ"

    @property
    def FONT_NAME(self) -> str:
        return "Kurale"

    @property
    def STYLE_DEFAULT_BUTTON(self) -> dict:
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
    def DEFAULT_DATA_FILE_NAME(self) -> str:
        return "data.json"

    @property
    def DEFAULT_LORE_FILE_EXT(self) -> str:
        return ".jpy"

    @property
    def DEFAULT_LORE_COMPILED_FILE_EXT(self) -> str:
        return ".jpyc"

    @property
    def DEFAULT_START_LABEL(self) -> str:
        return "main"

    @property
    def SUPPORTED_AUDIO_FORMATS(self) -> frozenset:
        return frozenset((".mp3", ".wav", ".ogg"))

    @property
    def SUPPORTED_IMAGE_FORMATS(self) -> frozenset:
        return frozenset((".png", ".jpg", ".jpeg", ".PNG", ".JPEG", ".gif", ".GIF"))

    @property
    def IGNORE_FILES_FOR_UNLOADING(self) -> frozenset:
        return self._cant_unload

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
