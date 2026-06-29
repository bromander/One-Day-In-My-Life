import arcade.gui
import os


class Globals:

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
    def UNSEEN_TEXT_PLACEHOLDER(self):
        """
        Обозначает символ, который будет стоять вместо букв, что во время речи персонажа ещё не видны.
        По умолчанию строит пустой символ Брайля (U+2800)
        """
        return "⠀"

    @property
    def TOPICAL_SAVES_VERSION(self) -> int:
        return 1

    @property
    def EXCLUDE_LABELS_FOR_UNLOAD(self) -> frozenset[str]:
        return frozenset(["init_gui_sprites"])

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
    def MAX_SAVESFILE_SIZE_LIMIT(self) -> int:
        """
        Максимальный порог веса файла в байтах.
        Если файл сохранения его переступит, то отныне будет сжиматься
        """
        return 20000

    @property
    def SAVES_COLOR_PALLETE(self) -> frozenset[tuple[int, int, int]]:
        return frozenset(
            [
                (255, 138, 158),  # Розовый фламинго
                (255, 179, 122),  # Персиковый закат
                (252, 229, 112),  # Лимонный сорбет
                (124, 219, 154),  # Мятный бриз
                (155, 158, 255),  # Лавандовый туман
                (255, 118, 200),  # Магнолия
                (255, 210, 90),  # Янтарный мёд
                (90, 230, 200),  # Бирюзовая волна
                (200, 160, 255),  # Сиреневый крем
                (255, 160, 100),  # Мандариновый щербет
                (180, 230, 120),  # Лаймовый фреш
                (120, 200, 255),  # Небесная лазурь
                (255, 200, 180),  # Лососёвый мусс
                (220, 180, 255),  # Глициния
                (100, 255, 180)  # Аквамариновый лёд
            ]
        )

    @property
    def SHOULD_ZIP_SAVES_DATA(self) -> bool:
        """
        True - принудительное сжатие
        False - Принудительное игнорирование
        None - Если размер превышает MAX_SAVESFILE_SIZE_LIMIT, то будет применено сжатие
        """
        return None

    @property
    def DEFAULT_IN_GAME_WINDOW_SIZE(self) -> tuple[int,  int]:
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
    def SUPPORTED_FONT_FORMATS(self) -> frozenset:
        return frozenset((".tff", ".otf"))

    fm = None  # Files manager
    sm = None  # Saves manager
    am = None  # Audio manager
    scene = None  # Scene
    lm = None  # Lore Manager
    da = None  # Discord actor

    actions = None

    All_main_views = None
    GameViews = None

    ListCharacters = None

    attributes = None

    main = None


g = Globals()
