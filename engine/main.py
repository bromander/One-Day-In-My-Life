import copy

import arcade
from arcade import View
from pyglet.event import EVENT_HANDLE_STATE
import arcade.gui as agui
import arcade.gui.widgets.layout
from typing import Optional
import time
import os
import random
import json
import uuid
from typing import Generator
from webbrowser import open_new_tab as web_open
from pyglet.gl.lib import GLException

from .gui import (
    UISliderVertical,
    InGameManager,
    CharactersTextManager,
    SettingsManager,
    UISliderSavesUpdater,
    ColorsPaletteButton,
)
from .scene import Scene
from .lore_manager import LoreManager
from .lore_logger import LoreLogger
from .waiter import Waiter
from .saves import Saves_manager
from .namespace import *
from .actions import Actions
from .audio import AudioManager
from .presence import Discord_act
from .files_manager import FilesManager
from .character import ListCharacters, Attributes

from .globals import g
from .logger import get_logger

logger = get_logger(__name__)

wait_trigger = Waiter()


class Views:
    class MainWindow(arcade.Window):
        def __init__(self, width, height, title, resizable=True):
            super().__init__(
                width=width, height=height, title=title, resizable=resizable
            )
            self.GameView: Optional[Views.GameView] = None

            g.All_main_views = Views

            self.ctx.default_atlas.resize((16384, 16384))

            self.detect_and_block_resize = resizable

        def on_close(self) -> None:
            arcade.close_window()

        def on_activate(self) -> EVENT_HANDLE_STATE:
            am = g.am
            if am:
                try:
                    if am.music.paused:
                        am.music.resume()
                    if am.sound.paused:
                        am.sound.resume()
                    am.voice.fade_modifier = 1.0
                except NameError:
                    pass

        def on_deactivate(self) -> EVENT_HANDLE_STATE:
            am = g.am
            if am:
                try:
                    if not am.music.paused:
                        am.music.pause()
                    if not am.sound.paused:
                        am.sound.pause()
                    am.voice.fade_modifier = 0.0
                except NameError:
                    pass

        def on_resize(self, width: int, height: int) -> EVENT_HANDLE_STATE:
            if self.detect_and_block_resize:
                pass

        def show_view(self, new_view: View) -> None:
            super().show_view(new_view)
            logger.warning(f"Открываем новое View: {new_view}")
            if hasattr(self.current_view, "set_bg_by_scene_bg") and g.scene:
                self.current_view.set_bg_by_scene_bg()

    class Main_template(arcade.View):
        def __init__(self) -> None:
            """
            Является "Шаблоном".
            Создаёт счётчик ФПС и отвечает за курсор
            """
            super().__init__()

            self.window.set_mouse_visible(False)

            self.scale = arcade.get_screens()[0].get_scale()

            self.cursor_texture = arcade.Sprite(g.fm.get_texture("cursor.png"), 0.2)
            self.window.background_color = arcade.color.WHITE
            self.background_color = arcade.color.WHITE
            self.fps = {
                "window": [],
                "window_size": 100,
                "last_print_time": time.time(),
                "avg_fps": 0.0,
                "min_fps": 0.0,
                "max_fps": 0.0,
                "label": arcade.Text(
                    f"FPS: Avg=0, Min=0, Max=0, Window size: 0. Vsync: {self.window.vsync}",
                    x=10,
                    y=self.window.height - 10,
                    color=arcade.color.ARCADE_GREEN,
                    font_size=14,
                    anchor_x="left",
                    anchor_y="top",
                ),
            }

        def cleanup_ui(self):
            if hasattr(self, "manager"):
                self.manager.clear()
                self.manager.disable()

            if hasattr(self, "menu_manager"):
                self.menu_manager.clear()
                self.menu_manager.disable()

            if hasattr(self, "settings_manager"):
                if hasattr(self.settings_manager, "clear"):
                    self.settings_manager.clear()

            if hasattr(self, "splash_manager"):
                self.splash_manager.clear()
                self.splash_manager.disable()

            if hasattr(self, "in_game_manager"):
                if hasattr(self.in_game_manager, "clear"):
                    self.in_game_manager.clear()

        def _get_amend_color(self, border_thickness=20, min_border=2):
            sprite = None
            bg_values = list(g.scene["bg"].values())
            if bg_values:
                sprite = bg_values[-1]
            elif g.scene["bg_parallax"]:
                sprite = g.scene["bg_parallax"][0]["sprite"]
            if not sprite or not hasattr(sprite, "texture") or sprite.texture is None:
                return None

            img = sprite.texture.image.copy()
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img.thumbnail((img.width // 2, img.height // 2))
            width, height = img.size

            border = min(border_thickness, width // 2, height // 2)
            pixels = img.load()

            visible_pixels = []

            while border >= min_border:
                for x in range(width):
                    for y in range(border):
                        if pixels[x, y][3] > 0:
                            visible_pixels.append(pixels[x, y])
                    for y in range(height - border, height):
                        if pixels[x, y][3] > 0:
                            visible_pixels.append(pixels[x, y])
                for y in range(border, height - border):
                    for x in range(border):
                        if pixels[x, y][3] > 0:
                            visible_pixels.append(pixels[x, y])
                    for x in range(width - border, width):
                        if pixels[x, y][3] > 0:
                            visible_pixels.append(pixels[x, y])

                if visible_pixels:
                    break
                border //= 2

            if not visible_pixels:
                cx0, cy0 = width // 4, height // 4
                cx1, cy1 = width * 3 // 4, height * 3 // 4
                for x in range(cx0, cx1):
                    for y in range(cy0, cy1):
                        if pixels[x, y][3] > 0:
                            visible_pixels.append(pixels[x, y])
                if not visible_pixels:
                    return None

            count = len(visible_pixels)
            red = sum(p[0] for p in visible_pixels) // count
            green = sum(p[1] for p in visible_pixels) // count
            blue = sum(p[2] for p in visible_pixels) // count

            return (red, green, blue)

        def set_bg_by_scene_bg(self):
            color = self._get_amend_color()
            if color:
                self.background_color = color
                logger.debug(f"Бекгрунд установлен на {color}")
            else:
                logger.warning(
                    "При попытке вызова Main_template._get_amend_color, возвращено None. Бекграунд не установлен"
                )

        def on_update(self, delta_time: float) -> None:
            if "x" in self.window.mouse.data and "y" in self.window.mouse.data:
                mouse_x, mouse_y = (
                    self.window.mouse.data["x"],
                    self.window.mouse.data["y"],
                )
                self.cursor_texture.position = (mouse_x, mouse_y)

            if not g.sm:
                return None

            if g.sm.Volume.show_fps:
                current_fps = 1.0 / delta_time if delta_time > 0 else 0

                self.fps["window"].append(current_fps)
                if len(self.fps["window"]) > self.fps["window_size"]:
                    self.fps["window"].pop(0)

                if time.time() - self.fps["last_print_time"] >= 1.0:
                    self.fps["avg_fps"] = sum(self.fps["window"]) / len(
                        self.fps["window"]
                    )
                    self.fps["min_fps"] = min(self.fps["window"])
                    self.fps["max_fps"] = max(self.fps["window"])

                    self.fps["label"].text = (
                        f"FPS: Avg={int(self.fps['avg_fps'])}, Min={int(self.fps['min_fps'])}, Max={int(self.fps['max_fps'])}, "
                        f"Window size: {self.fps['window_size']}. "
                        f"Vsync: {self.window.vsync}"
                    )

                    self.fps["last_print_time"] = time.time()

        def on_mouse_leave(self, x: int, y: int) -> bool | None:
            self.cursor_texture.alpha = 0

        def on_mouse_enter(self, x: int, y: int) -> bool | None:
            self.cursor_texture.alpha = 255

        def on_draw(self) -> None:

            if self.cursor_texture:
                arcade.draw_sprite(self.cursor_texture)

            if not g.sm:
                return None

            if g.sm.Volume.show_fps:
                arcade.draw_lrbt_rectangle_filled(
                    left=5,
                    right=8 * len(self.fps["label"].text),
                    bottom=self.window.height - 35,
                    top=self.window.height - 10,
                    color=(0, 0, 0, 200),
                )
                self.fps["label"].x = 10
                self.fps["label"].y = self.window.height - 10
                self.fps["label"].draw()

    class GameView(Main_template):
        def __init__(self, session_id: Optional[str] = None) -> None:
            """
            Отвечает за основное окно новельной части
            :param session_id: Айди сессии
            """
            super().__init__()

            self.window_mode = g.sm.Volume.window_mode
            if self.window_mode == "full-screen":
                self.window.set_fullscreen(True)
            elif self.window_mode == "window":
                self.window.set_fullscreen(False)
                self.window.maximize()

            g.main = self

            g.am.stop_music()
            g.am.stop_sound()

            # self.window.set_vsync(True)

            self.delta_time = 0.0

            self.dialog_window: Optional[arcade.Sprite] = None

            self.show_dialogue_bg_trigger = True

            self.menu_manager = agui.UIManager()
            self.menu_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

            self.splash_manager = agui.UIManager()

            self.waiting_dialogue = Waiter(True)
            self.waiting_autoskip = Waiter(False)
            self.waiting_talk = Waiter(False)

            self.last_text_skip = time.time()

            self.last_text = " "

            def create_widgets():
                # dialog window
                texture = g.fm.get_texture("dialog_window.png")

                self.dialog_window = arcade.Sprite(
                    texture,
                    scale=6 * min(self.width / 1920, self.height / 1080),
                    center_x=self.width * 0.5,
                    center_y=self.height * 0.13,
                )

                # blackscreen
                texture = g.fm.get_texture("blackscreen.png")

                sprite = arcade.Sprite(
                    texture,
                    scale=50,
                    center_x=self.width * 0.5,
                    center_y=self.height * 0.5,
                )
                sprite.alpha = 0
                g.scene.add_sprite("fade", "fade", sprite)

                # splash
                texture = g.fm.get_texture("splash.png")

                sprite = arcade.Sprite(
                    texture, center_x=self.width * 0.5, center_y=self.height * 0.5
                )
                sprite.alpha = 0
                g.scene.add_sprite("fade", "splash", sprite)

                text = agui.UILabel(
                    " ",
                    y=self.height * 0.82,
                    align="center",
                    width=self.width,
                    font_name=g.FONT_NAME,
                    text_color=(255, 255, 255, 0),
                    font_size=72,
                )
                text_small = agui.UILabel(
                    " ",
                    y=self.height * 0.77,
                    align="center",
                    width=self.width,
                    font_name=g.FONT_NAME,
                    text_color=(255, 255, 255, 0),
                    font_size=28,
                )

                self.splash_manager.add(text)
                self.splash_manager.add(text_small)

            create_widgets()

            self.start_trigger: bool = True

            self.loaded_session_id = session_id
            self.session_id = session_id

            self.NAMESPACE = Namespace(g)

            self.session_data = {
                "name": "",
                "description": "",
                "session_start": round(time.time()),
            }

            self.loaded_from_save = False
            if self.loaded_session_id:
                self._load_save(session_id)
                self.loaded_from_save = True
            self.session_id = str(uuid.uuid4())

            self.settings_manager = SettingsManager()
            self.settings_manager.enable()

            self.characters_texts_manager = CharactersTextManager()
            self.characters_texts_manager.enable()

            self.LoreLogger = LoreLogger()

            self.in_game_manager = InGameManager()
            self.in_game_manager.settings_button.on_click = (
                self.settings_manager.turn_visibl
            )
            self.in_game_manager.return_button.on_click = self.LoreLogger.return_back
            self.in_game_manager.skip_button.on_click = lambda event=None: (
                self.waiting_autoskip.switch()
            )
            self.in_game_manager.enable()
            # self.in_game_manager.return_button.on_click = self.LoreLogger.return_back

            if not self.loaded_from_save:
                g.lm.jump(g.DEFAULT_START_LABEL, 0)

            self.talk_manager(clicked=False)

            self.on_resize(int(self.width), int(self.height))

            if not hasattr(self.NAMESPACE["Persistent"], "sessions"):
                self.NAMESPACE["Persistent"].sessions = 1
            else:
                self.NAMESPACE["Persistent"].sessions += 1

        def _load_save(self, session_id):
            g.sm.Save.load_save(session_id)
            self.window.GameView = self

        def _update_dialog_window(self, width, height):
            self.dialog_window.width = width
            self.dialog_window.center_x = width * 0.5
            self.dialog_window.bottom = 0

        def on_resize(self, width: int, height: int) -> bool | None:
            self.settings_manager.update_size(width, height)
            self.characters_texts_manager.update_pos(width, height)
            self._update_dialog_window(width, height)
            g.scene.on_resize(width, height)

        def chanel(self):
            time.sleep(0.05)

            g.actions.active_generators.clear()

            g.lm.unload_assets(g.DEFAULT_START_LABEL)

            g.am.stop_sound()
            g.am.stop_music()
            g.am.stop_voice()

            self.window.set_fullscreen(True)
            time.sleep(0.01)
            self.window.set_fullscreen(False)
            self.window.size = (1024, 786)
            game = Views.GameMenu(show_lc=True)
            self.window.show_view(game)
            self.window.center_window()

        def talk_manager(
            self, pos_offset: int = 0, clicked: bool = True, do_snapshot: bool = True
        ) -> None:
            """
            Получает инструкции сценария и запускает функцию talk(), обрабатывая её результаты
            """

            gens = g.actions.active_generators
            if gens.active_generators_consistently and clicked:

                if time.time() - self.last_text_skip < 0.1:
                    return None
                else:
                    self.last_text_skip = time.time()

                if gens.active_generators_consistently[0][0].startswith("talk"):
                    while gens.active_generators_consistently[0][0].startswith("talk"):
                        gens._update_consistently(1000.0)
                        if not gens.active_generators_consistently:
                            break
                    return None
                else:
                    g.attributes.reset()
                    g.main.characters_texts_manager.prepare()
                    return None
            else:
                g.attributes.reset()
                g.main.characters_texts_manager.prepare()

            if (
                g.actions.active_generators.active_generators_consistently
                and not clicked
            ):
                self.waiting_talk.on()
                return None

            g.attributes.reset()
            now = g.lm.get_thing(pos_offset)

            if now["action"] == "EXECUTE":
                logger.log(5, repr(str(now["data"])))

            res = self.talk(now)

            if self.start_trigger:
                self.start_trigger = False

            self.waiting_talk.off()

            match res:
                case "NEXT":
                    self.talk_manager(clicked=False)
                case "REPEAT":
                    return None
                case "END":
                    return None
                case "END_text":
                    if do_snapshot:
                        self.LoreLogger.create_log()
                    return None

        def talk(self, now) -> str:
            """
            Запускает основные действия сценария
            :param now:
            :return:
            """

            while True:
                if now is None:
                    return "NEXT"

                match now["action"]:
                    case "EXECUTE":
                        att = 0
                        res = None
                        while att < 10:
                            try:
                                att += 1
                                res = self.NAMESPACE.execute(now["data"])
                            except FileNotFoundError:
                                continue
                            else:
                                break

                        res = res if res is not None else "NEXT"
                        return res

                    case _:
                        logger.error(f"Неопознанная команда: {now}")
                        return "NEXT"

        def on_draw(self) -> None:
            if not self.start_trigger:
                self.clear()
                g.scene.draw()
                self.splash_manager.draw()

                if self.show_dialogue_bg_trigger:
                    arcade.draw_sprite(self.dialog_window)

                self.characters_texts_manager.draw()

                if self.show_dialogue_bg_trigger:
                    self.in_game_manager.draw()

                self.menu_manager.draw()
                self.settings_manager.draw()
            super().on_draw()

        def on_update(self, delta_time) -> None:

            if self.show_dialogue_bg_trigger:
                if not self.in_game_manager._enabled:
                    self.in_game_manager.enable()

            else:
                if self.in_game_manager._enabled:
                    self.in_game_manager.disable()

            self.delta_time = delta_time

            g.scene.update(delta_time)

            self.menu_manager.on_update(delta_time)

            g.actions.update(delta_time)

            self.characters_texts_manager.update(delta_time)

            if self.waiting_autoskip:
                self.talk_manager(clicked=True)

            if self.waiting_talk:
                self.talk_manager(clicked=False)

            super().on_update(delta_time)

        def on_key_press(self, key, modifiers) -> None:
            if (
                key == arcade.key.SPACE or key == arcade.key.ENTER
            ) and not self.settings_manager.waiting_settings:
                self.waiting_autoskip.off()
                self.talk_manager()
            if key == arcade.key.S or key == arcade.key.ESCAPE:
                self.settings_manager.turn_visibl()
            if key == arcade.key.B:
                text = f"""
                \n
                Данные на текущий момент игры:
                
                ===== ЛЕЙБЛ =====
                - Лейбл: {g.lm.label}
                - Позиция: {g.lm.pose}
                - Граф сюжета: {g.lm.graf}
                - Следующие лейблы: {g.lm.graf[g.lm.label] if g.lm.label in g.lm.graf else "Нет"}
                
                ===== АССЕТЫ =====
                - Текстуры: ЗАГРУЖЕНО: {len(g.fm.textures)}, НЕ ЗАГРУЖЕНО: {len(g.fm.textures_paths) - len(g.fm.textures)}
                - Аудио: ЗАГРУЖЕНО: {len(g.fm.audios)}, НЕ ЗАГРУЖЕНО: {len(g.fm.audio_paths) - len(g.fm.audios)}
                - Активные спрайты: {g.scene.len_loaded_textures}
                \n
                """

                logger.debug("\n".join([i.lstrip(" ") for i in text.split("\n")]))

                self.window.ctx.default_atlas.show()

        def on_mouse_release(self, x, y, button, modifiers) -> None:
            if (int(button) == 1) and not self.settings_manager.waiting_settings:
                if (
                    len(list(self.in_game_manager.get_widgets_at((x, y)))) == 1
                ):  # Проверяем, не нажали ли мы на какую-нибудь кнопку.
                    self.waiting_autoskip.off()
                    self.talk_manager()

        def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
            g.scene.on_mouse_motion(x, y)

    class GameMenu(Main_template):
        def __init__(self, show_lc: bool = True) -> None:
            """
            Отвечает за главное меню игры
            :param show_lc: если True, отображает загрузочный экран и инициализирует основные класса
            """
            super().__init__()

            self.deleted = 0

            self.window.set_vsync(False)

            self.bg_sprite = arcade.Sprite(g.fm.get_texture("bg_main_menu.png"))
            self.bg_sprite.center_x = self.center_x
            self.bg_sprite.center_y = self.center_y

            self.bg_other_sprite = arcade.Sprite(g.fm.get_texture("bg_eblani.png"))
            self.bg_other_sprite.center_x = self.width * 0.15
            self.bg_other_sprite.center_y = self.height * 0.3
            self.bg_other_sprite.scale = 0.3

            self.loading_screen = arcade.Sprite(
                g.fm.get_texture("JE3000_logo-export.png"), 1
            )
            self.loading_screen.position = (int(self.center_x), int(self.center_y))
            self.loading_screen_fade = arcade.Sprite(g.fm.get_texture("blackscreen.png"))
            self.loading_screen_fade.position = (int(self.center_x), int(self.center_y))
            self.loading_screen_fade.alpha = 0
            self.loading_screen_fade.size = (2500, 2500)
            self.loading_screen.alpha = 0

            self.background_color = (199, 100, 131)

            self.manager = agui.UIManager()
            self.manager.disable()

            self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

            self.show_main_windows()
            self.is_loading = False
            self.is_mouse_pressed = False

            self.other_text = agui.UILabel(
                " ",
                text_color=arcade.color.MIDNIGHT_BLUE,
                font_name=g.FONT_NAME,
                align="center",
                width=self.window.width * 0.9,
                multiline=True,
                font_size=40,
                x=self.center_x,
                y=self.center_y,
            )
            self.other_manager = agui.UIManager()
            self.other_manager.add(self.other_text)

            self.vokhanalia = False

            if show_lc:
                self.show_ls()

        def on_resize(self, width: int, height: int) -> bool | None:
            self.bg_sprite.center_x, self.bg_sprite.top = self.center_x, self.height
            self.bg_other_sprite.center_x, self.bg_other_sprite.center_y = (
                self.width * 0.15,
                self.height * 0.3,
            )

        def show_ls(self) -> None:
            """
            Отображает загрузочный экран
            """

            def loading(self):
                self.background_color = (0, 69, 255)
                self.loading_screen_fade.alpha = 255
                for i in range(0, int(250 / 2)):
                    if random.random() > 0.9:
                        continue
                    if self.is_mouse_pressed:
                        self.loading_screen_fade.alpha = 0
                        break
                    self.loading_screen_fade.alpha = 255 - i * 2
                    yield
                yield
                g.am.stop_music()

                try:
                    g.sm.Persistent.get_persistent("bossfight")
                except AttributeError:
                    g.sm.Persistent.set_persistent("bossfight", False)

                for i in range(20, 50):
                    yield
                self.loading_screen_fade.alpha = 0
                for i in range(random.randint(1, 2)):
                    self.loading_screen_fade.alpha = 255
                    for i in range(random.randint(1, 3)):
                        yield
                    self.loading_screen.alpha = 0
                    self.loading_screen_fade.alpha = 0
                    yield
                self.is_loading = False
                g.am.play_music(g.fm.get_audio("buttercup by jack stauber (but kazoo).mp3"))
                self.background_color = (199, 100, 131)

            self.loading_screen.alpha = 255
            self.is_loading = True
            self.loading_generator = loading(self)

        def on_draw(self) -> None:
            self.clear()
            arcade.draw_sprite(self.bg_sprite)
            arcade.draw_sprite(self.bg_other_sprite, pixelated=True)
            self.manager.draw()
            self.other_manager.draw()
            arcade.draw_sprite(self.loading_screen)
            arcade.draw_sprite(self.loading_screen_fade)
            super().on_draw()

        def _start_vokhanalia(self):

            def gen(text):
                with open("./game/other/thinking.json", "r", encoding="UTF-8") as f:
                    f = json.load(f)

                for i in f:
                    text.should_text = i
                    yield

            def vokhanalia():
                self.window.set_visible(False)
                g.am.play_music(
                    "Lucid Blocks OST： Corner.mp3",
                    streaming=True,
                    loop=True,
                )

                class Vokhanalia_view(arcade.View):
                    def __init__(self, text):
                        super().__init__()

                        self.text = text

                        file = g.fm.get_texture("sorry1.png")
                        self.file = arcade.Sprite(file)
                        self.background_color = arcade.color.BLACK
                        self.lst = arcade.SpriteList()
                        self.window.center_window()

                        self.width_const, self.height_const = self.width, self.height

                        self.talker = arcade.Text(
                            text.text,
                            self.window.width / 2,
                            self.window.height / 2,
                            color=arcade.color.WHITE,
                            multiline=True,
                            width=self.window.width - 100,
                            font_size=30,
                            anchor_x="center",
                            anchor_y="center",
                            align="center",
                        )
                        self.window.center_window()
                        self.last_update = time.time()
                        self.last_update_eye = time.time()

                        self.main_gen: Optional[Generator] = None

                    def text_animation(self):
                        self.text.text = ""
                        timer = 0
                        word_index = 0
                        words = self.text.should_text.split(" ")

                        while word_index < len(words):
                            dt = yield
                            if dt is None or dt <= 0:
                                self.text.text = " ".join(words[: word_index + 1])
                                word_index += 1
                                continue

                            timer += dt
                            words_to_add = int(timer * 20)
                            if words_to_add > 0:
                                word_index = min(word_index + words_to_add, len(words))
                                self.text.text = " ".join(words[:word_index])
                                timer -= words_to_add / 20

                        self.main_gen = None

                    def on_mouse_press(
                        self, x: int, y: int, button: int, modifiers: int
                    ) -> bool | None:
                        if button == 1:
                            if self.main_gen is None:
                                self.text.next()

                                self.main_gen = None
                                text_animation = self.text_animation()
                                next(text_animation)
                                self.main_gen = text_animation

                            else:
                                self.text.text = self.text.should_text
                                self.main_gen = None

                    def on_update(self, delta_time: float) -> bool | None:

                        if self.main_gen:
                            try:
                                self.main_gen.send(delta_time)
                            except StopIteration:
                                self.main_gen = None

                        if time.time() - self.last_update < 0.1:
                            return None

                        self.window.set_size(
                            self.width_const + random.randint(-50, 50),
                            self.height_const + random.randint(-50, 50),
                        )

                        self.last_update = time.time()

                        self.window.center_window()

                    def on_draw(self) -> bool | None:
                        self.clear()
                        self.lst.clear()

                        self.talker.position = (
                            self.center_x + random.randint(-1, 1),
                            self.center_y + random.randint(-1, 1),
                        )
                        self.talker.text = self.text.text

                        if time.time() - self.last_update_eye > 0.1:
                            for i in range(10):
                                self.last_update_eye = time.time()
                                file = arcade.Sprite(self.file.texture)
                                file.color = (255, 255, 255, 120)

                                file.center_x = random.randint(0, self.window.width)
                                file.center_y = random.randint(0, self.window.height)
                                if random.random() >= 0.5:
                                    file.scale_x = (
                                        random.random() * random.randint(1, 30) / 10
                                    )
                                else:
                                    file.scale_y = (
                                        random.random() * random.randint(1, 30) / 10
                                    )
                                self.lst.append(file)

                        self.lst.draw()
                        self.talker.draw()

                class VokhanaliaText:
                    def __init__(self):

                        self.text = "..."
                        self.should_text = "..."
                        self.gen = gen(self)

                    def next(self):
                        self.should_text = ""
                        self.text = ""
                        try:
                            next(self.gen)
                        except StopIteration:
                            web_open("https://youtu.be/mn6brnRQPHs")
                            arcade.exit()

                text = VokhanaliaText()
                self.VokhanaliaText = text
                self.vokhanalia = True
                self.main_generator = None

                for i in range(2):
                    window = arcade.open_window(
                        1000,
                        600,
                        window_title="Почему?",
                        resizable=False,
                        style="borderless",
                    )
                    window.center_window()
                    view = Vokhanalia_view(text)
                    window.show_view(view)

            self.loading_generator = vokhanalia()

        def start_vzlom(self, event=None):
            orig_window = (self.window.height, self.window.width)
            self.window.on_close = lambda: print("No")
            self.window.on_deactivate = lambda: self.window.activate()

            def vslom():
                g.am.play_music(g.fm.get_audio("ambience-reactor.mp3"))
                oth_manager = agui.UIManager()
                oth_manager.add(self.main_lebel)
                for i in range(10):
                    self.main_lebel.text = "Загрузка."
                    for i in range(10):
                        self.main_lebel.center_y = self.main_lebel.center_y - i
                        for i in self.manager.children[0]:
                            if type(i) is not type(agui.UILabel()):
                                oth_manager.add(i)
                                i.center_x = i.center_x + random.randint(-100, 100)
                                i.center_y = i.center_x + random.randint(-100, 100)
                        oth_manager.on_update(1 / 60)
                        self.window.set_size(
                            orig_window[1] + random.randint(-100, 100),
                            orig_window[0] + random.randint(-100, 100),
                        )
                        self.window.center_window()
                        if random.random() > 0.9:
                            self.background_color = arcade.color.BLACK
                        else:
                            self.background_color = arcade.color.WHITE
                        yield

                last_time = time.time()
                g.am.play_music(
                    "Never gonna give you up (a very bad kazoo cover).mp3"
                )
                while time.time() - last_time < 10:
                    self.window.set_size(
                        orig_window[1] + random.randint(-10, 10),
                        orig_window[0] + random.randint(-10, 10),
                    )
                    self.window.center_window()
                    yield

                self.window.set_size(1024, 1)
                yield
                self.window.set_size(1024, 786)
                self.manager.remove(self.manager.children[0][-1])
                with open(
                    rf"C:\Users\{os.getlogin()}\Desktop\JopaJam{uuid.uuid4()}.txt",
                    "w",
                    encoding="UTF-8",
                ) as file:
                    file.write("https://youtu.be/mn6brnRQPHs?si=nGHy9Eq1ci-wJg0z")

                self.main_lebel.text = "Скачивание данных пользователя..."
                base_path = rf"C:\Users\{os.getlogin()}"

                for root, dirs, files in os.walk(base_path):
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    self.other_text.center_x = self.center_x
                    self.other_text.center_y = self.center_y

                    if root.count("\\") > 6:
                        continue

                    if len(dirs) > 2:
                        self.other_text.text = os.path.join(root, dirs[-1]).replace(
                            "\\", "\\ "
                        )

                    yield

                self.manager.clear()
                self.show_main_windows()
                g.am.stop_music()
                self.is_loading = False
                self.window.on_deactivate = lambda: arcade.close_window()

            self.is_loading = True
            self.loading_generator = vslom()

        def del_vzlom(self, event=None):
            def dele():
                g.am.play_music("strashilka.mp3", volume=20.0)
                last_time = time.time()
                while time.time() - last_time < 29:
                    self.cursor_texture.alpha = 0 if random.random() > 0.95 else 255
                    yield
                while time.time() - last_time < random.randint(2, 10):
                    yield
                yield
                self.cursor_texture.alpha = 255
                g.am.play_sound("perdezh_YQ5l54B.mp3")

                if self.deleted < 1:
                    self.manager.remove(self.manager.children[0][-2])
                    self.deleted += 1
                else:
                    time.sleep(0.5)
                    arcade.close_window()
                    arcade.exit()
                    self.window.on_close()
                self.is_loading = False

            self.is_loading = True
            self.loading_generator = dele()

        def on_update(self, delta_time) -> None:
            self.bg_other_sprite.angle = self.bg_other_sprite.angle + 90 * delta_time
            if not self.is_loading:
                self.manager.enable()
            else:
                if self.loading_generator:
                    try:
                        next(self.loading_generator)
                    except StopIteration:
                        self.loading_generator = None
                self.manager.disable()

            super().on_update(delta_time)

        def on_mouse_press(
            self, x: int, y: int, button: int, modifiers: int
        ) -> EVENT_HANDLE_STATE:
            self.is_mouse_pressed = True

        def on_mouse_release(
            self, x: int, y: int, button: int, modifiers: int
        ) -> EVENT_HANDLE_STATE:
            self.is_mouse_pressed = False

        def on_key_press(self, key: int, modifiers: int) -> None:
            if (
                key == arcade.key.L and modifiers & arcade.key.MOD_SHIFT
            ) and not self.is_loading:
                self._start_vokhanalia()
                self.is_loading = True

        def cleanup_ui(self):
            if hasattr(self, "manager"):
                self.manager.clear()
                self.manager.disable()

            if hasattr(self, "menu_manager"):
                self.menu_manager.clear()
                self.menu_manager.disable()

            if hasattr(self, "settings_manager"):
                if hasattr(self.settings_manager, "clear"):
                    self.settings_manager.clear()

            if hasattr(self, "splash_manager"):
                self.splash_manager.clear()
                self.splash_manager.disable()

            if hasattr(self, "in_game_manager"):
                if hasattr(self.in_game_manager, "clear"):
                    self.in_game_manager.clear()

        def show_main_windows(self) -> None:

            def create_menu_buttons():
                self.manager.clear()

                def start_game(event=None):

                    self.window.center_window()
                    self.cleanup_ui()
                    self.window.set_fullscreen(False)
                    self.window.size = g.DEFAULT_IN_GAME_WINDOW_SIZE
                    # self.window.set_fullscreen(True)
                    self.manager.disable()
                    game = Views.GameView()
                    self.window.GameView = game
                    self.window.show_view(game)

                def start_vopros_game(event=None):

                    self.window.center_window()
                    self.cleanup_ui()
                    self.window.set_fullscreen(False)
                    self.window.size = g.DEFAULT_IN_GAME_WINDOW_SIZE
                    # self.window.set_fullscreen(True)
                    self.manager.disable()
                    game = g.GameViews.GD_super_duper_game()
                    self.window.GameView = game
                    self.window.show_view(game)

                def open_saves(event=None):
                    self.cleanup_ui()
                    settings = Views.SaveMenu()
                    self.window.show_view(settings)

                def open_settings(event=None):
                    self.cleanup_ui()
                    settings = Views.SettingsMenu()
                    self.window.show_view(settings)

                FONT_NAME = g.FONT_NAME
                STYLE_DEFAULT_BUTTON = g.STYLE_DEFAULT_BUTTON

                self.main_lebel = agui.UILabel(
                    "",
                    text_color=arcade.color.MIDNIGHT_BLUE,
                    font_name=FONT_NAME,
                    align="center",
                    width=self.window.width * 0.9,
                    multiline=True,
                    font_size=40,
                )
                self.main_lebel.center_y = self.height * 0.7
                self.main_lebel.center_x = self.width * 0.5
                self.manager.add(self.main_lebel)

                start_button = agui.UIFlatButton(
                    text="Начать игру", width=200, style=STYLE_DEFAULT_BUTTON
                )
                start_button.on_click = start_game
                self.v_box.add(start_button)

                vopros_button_style = copy.deepcopy(STYLE_DEFAULT_BUTTON)
                vopros_button_style["normal"]["bg"] = (3, 152, 252)
                vopros_button_style["hover"]["bg"] = (8, 101, 163)
                vopros_button = agui.UIFlatButton(
                    text="???", width=200, style=vopros_button_style
                )
                vopros_button.on_click = start_vopros_game
                self.v_box.add(vopros_button)

                settings_button = agui.UIFlatButton(
                    text="Загрузить", width=200, style=STYLE_DEFAULT_BUTTON
                )
                settings_button.on_click = open_saves
                self.v_box.add(settings_button)

                settings_button = agui.UIFlatButton(
                    text="Настройки", width=200, style=STYLE_DEFAULT_BUTTON
                )
                settings_button.on_click = open_settings
                self.v_box.add(settings_button)

                exit_button = agui.UIFlatButton(
                    text="Выход", width=200, style=STYLE_DEFAULT_BUTTON
                )
                exit_button.on_click = lambda event: self.window.on_close()
                self.v_box.add(exit_button)

                ui_anchor_layout = arcade.gui.UIAnchorLayout()
                ui_anchor_layout.add(child=self.v_box)
                ui_anchor_layout.center_y = self.window.height * -0.27

                self.manager.add(ui_anchor_layout)

                dataminer_v_box = arcade.gui.UIBoxLayout(space_between=20)
                dataminer_ui_anchor_layout = arcade.gui.UIAnchorLayout()
                dataminer_ui_anchor_layout.add(
                    dataminer_v_box,
                    anchor_y="center",
                    anchor_x="right",
                    align_x=-20,
                    align_y=-100,
                )
                self.manager.add(dataminer_ui_anchor_layout)

                dataminer = agui.UIFlatButton(  # сасите письку
                    text="ВКЛЮЧИТЬ ратник",
                    width=300,
                    height=60,
                    style=STYLE_DEFAULT_BUTTON,
                    x=self.window.width * 0.70,
                    y=self.window.height * 0.3,
                    multiline=False,
                    align="center",
                )
                dataminer.on_click = self.start_vzlom
                dataminer_v_box.add(dataminer)

                dataminer = agui.UIFlatButton(  # сасите письку
                    text="ВЫКЛЮЧИТЬ ратник",
                    width=300,
                    height=60,
                    style=STYLE_DEFAULT_BUTTON,
                    x=self.window.width * 0.70,
                    y=self.window.height * 0.2,
                    multiline=False,
                    align="center",
                )
                dataminer.on_click = self.del_vzlom
                dataminer_v_box.add(dataminer)

            create_menu_buttons()

    class SaveMenu(Main_template):
        def __init__(self):
            """
            Отвечает за экран загрузки сохранений
            """
            super().__init__()

            saves = g.sm.Save.get_all_saves()
            self.saves = saves + [[None]] * (20 - len(saves))
            self.saves_len = 20

            self.background_color = (199, 100, 131)

            self.slider = UISliderVertical(
                value=1,
                min_value=1,
                max_value=self.saves_len,
                width=20,
                height=self.window.height - 50,
                step=1,
            )

            self.manager = agui.UIManager()
            self.manager.enable()

            self.colors_palette_choose = ColorsPaletteButton()

            self.choose = 0

            self.v_box_anchor = agui.UIAnchorLayout()
            self.manager.add(self.v_box_anchor)

            self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

            self.generate_buttons()

        def cleanup_ui(self):
            super().cleanup_ui()
            if hasattr(self, "slider"):
                self.slider = None
            if hasattr(self, "v_box"):
                self.v_box.clear()
            self.manager.disable()

        def _get_button_style(self, color):
            STYLE_SAVE_BUTTON = g.STYLE_DEFAULT_BUTTON.copy()
            STYLE_SAVE_BUTTON["normal"]["bg"] = color
            STYLE_SAVE_BUTTON["hover"]["bg"] = tuple(i + 25 if i + 25 < 256 else i for i in color)
            STYLE_SAVE_BUTTON["press"]["bg"] = tuple(i - 25 if i - 25 > 0 else i for i in color)
            _r, _g, _b = color
            gray = int(0.299 * _r + 0.587 * _g + 0.114 * _b)
            factor = 0.4
            darkness = 0.65
            STYLE_SAVE_BUTTON["disabled"]["bg"] = (
                (_r + (gray - _r) * factor) * (1 - darkness),
                (_g + (gray - _g) * factor) * (1 - darkness),
                (_b + (gray - _b) * factor) * (1 - darkness)
            )
            return STYLE_SAVE_BUTTON

        def generate_buttons(self) -> None:

            self.manager.clear()

            saves = g.sm.Save.get_all_saves()
            self.saves = saves + [[None]] * (20 - len(saves))

            self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

            self.v_box_anchor = agui.UIAnchorLayout()

            self.v_box_anchor.add(
                self.v_box,
                anchor_x="center",
                anchor_y="center",
                align_x=60
            )

            self.manager.add(self.v_box_anchor)

            def return_to_main_menu(event=None):

                self.cleanup_ui()
                game = Views.GameMenu(False)
                self.window.show_view(game)

            def open_save(session_id: str, event=None):
                self.window.center_window()
                self.window.set_fullscreen(False)
                self.window.size = g.DEFAULT_IN_GAME_WINDOW_SIZE
                self.window.set_fullscreen(True)

                self.cleanup_ui()

                game = Views.GameView(session_id)
                self.window.show_view(game)

            def delete_save(event=None):
                session_id = self.saves[self.choose][0]
                if session_id is None:
                    return None
                g.sm.Save.del_save(session_id)
                self.generate_buttons()

            def change_save_colour(event=None):
                self.colors_palette_choose.now_color = self.colors_palette_choose._get_color()

                session_id = self.saves[self.choose][0]
                if session_id is None:
                    self.colors_palette_choose.now_color = None
                    return None

                self.colors_palette_choose.update()

                g.sm.Save.set_save_color(session_id, self.colors_palette_choose.now_color)
                self.generate_buttons()

            def double_save(event=None):
                session_id = self.saves[self.choose][0]
                if session_id is None:
                    return None
                g.sm.Save.double_save(session_id, str(uuid.uuid4()))
                self.generate_buttons()

            STYLE_DEFAULT_BUTTON = g.STYLE_DEFAULT_BUTTON

            return_button = agui.UIFlatButton(
                text="Назад",
                width=100,
                height=50,
                style=STYLE_DEFAULT_BUTTON,
                x=self.window.width * 0.01,
                y=self.window.height * 0.9,
            )
            return_button_anchor = agui.UIAnchorLayout()
            return_button_anchor.add(
                return_button,
                anchor_x="left",
                anchor_y="top",
                align_x=10, align_y=-10
            )
            return_button.on_click = return_to_main_menu
            self.manager.add(return_button_anchor)

            del_save_button = agui.UIFlatButton(
                text="Удалить сохранение",
                width=150,
                height=100,
                style=STYLE_DEFAULT_BUTTON,
                x=self.window.width * 0.01,
                y=self.window.height * 0.5,
                multiline=True,
            )
            del_save_button.on_click = delete_save

            double_save_button = agui.UIFlatButton(
                text="Дублировать сохранение",
                width=170,
                height=100,
                style=STYLE_DEFAULT_BUTTON,
                x=self.window.width * 0.01,
                y=self.window.height * 0.5,
                multiline=True,
            )
            double_save_button.on_click = double_save

            del_save_button_anchor = agui.UIAnchorLayout()
            del_save_button_anchor.add(
                del_save_button,
                anchor_x="left",
                anchor_y="center",
                align_x=10
            )
            del_save_button_anchor.add(
                double_save_button,
                anchor_x="left",
                anchor_y="center",
                align_x=10, align_y=-110
            )
            self.colors_palette_choose = ColorsPaletteButton()
            session_id = self.saves[self.choose][0]
            if session_id is not None:
                color = g.sm.Save.get_save(session_id)["color"]
                self.colors_palette_choose.set_color(color)
            self.colors_palette_choose.on_click = change_save_colour
            del_save_button_anchor.add(
                self.colors_palette_choose,
                anchor_x="left",
                anchor_y="center",
                align_x=10, align_y=100
            )
            self.manager.add(del_save_button_anchor)

            for i in self.saves:
                text = "Пусто"
                STYLE_SAVE_BUTTON = copy.deepcopy(g.STYLE_DEFAULT_BUTTON)
                if i[0] is not None:
                    name = i[1]["session_data"]["name"]
                    description = i[1]["session_data"]["description"]
                    session_last_time = time.ctime(
                        i[1]["session_data"]["session_start"]
                    )
                    text = f"{name} : {description}                 {session_last_time}"
                    color = i[1]["color"]
                    STYLE_SAVE_BUTTON = self._get_button_style(color)

                button = agui.UIFlatButton(
                    text=text,
                    width=700,
                    height=200,
                    multiline=True,
                )
                button.style = STYLE_SAVE_BUTTON

                if i[0] is not None:
                    button.on_click = lambda event, value=i[0]: open_save(value)

                self.v_box.add(button)
                self.v_box.children[-1].disabled = True

            self.slider.center_x = self.window.width - 20
            self.slider.center_y = self.window.height / 2

            slider_anchor = agui.UIAnchorLayout()
            slider_anchor.add(
                self.slider,
                anchor_x="right",
                anchor_y="center",
                align_x=-10
            )
            self.manager.add(slider_anchor)

        def on_draw(self) -> bool | None:
            self.clear()
            if hasattr(self, "manager"):
                self.manager.draw()
            super().on_draw()

        def on_update(self, delta_time: float) -> bool | None:
            if self.window.current_view is self:
                if self.slider:
                    self.v_box_anchor.center_y = (
                        self.center_y
                        - ((self.saves_len - self.choose-1) * 220 + 100)
                        + (220 * 10)
                    )
                    self.choose = int(self.slider.value - 1)

                if self.v_box and self.v_box.children:
                    for i in range(self.saves_len):
                        self.v_box.children[i].disabled = (
                            True if i != self.choose else False
                        )
                super().on_update(delta_time)

        def on_mouse_scroll(
            self, x: int, y: int, scroll_x: int, scroll_y: int
        ) -> bool | None:
            if (self.saves_len - self.slider.value) + scroll_y >= 0 and (
                self.saves_len - self.slider.value
            ) + scroll_y < self.saves_len:
                self.slider.value += -scroll_y

        def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
            if symbol == arcade.key.ESCAPE:
                self.cleanup_ui()
                game = Views.GameMenu(False)
                self.window.show_view(game)

    class SettingsMenu(Main_template):
        def __init__(self) -> None:
            """
            Отвечает за меню настроек
            """
            super().__init__()

            self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=0)
            self.v_box_1 = arcade.gui.widgets.layout.UIBoxLayout(space_between=0)
            self.main_h_box = arcade.gui.widgets.layout.UIBoxLayout(
                vertical=False, space_between=20
            )

            self.manager = agui.UIManager()
            self.manager.enable()
            self.other_buttons = []

            self.manager.add(self.main_h_box)

            self.music_volume_slider: Optional[UISliderSavesUpdater] = None
            self.sound_volume_slider: Optional[UISliderSavesUpdater] = None
            self.voice_volume_slider: Optional[UISliderSavesUpdater] = None
            self.lps_slider: Optional[UISliderSavesUpdater] = None
            self.fade_speed_slider: Optional[UISliderSavesUpdater] = None

            self.background_color = (199, 100, 131)

            self.show_main_windows()

        def on_draw(self) -> None:
            self.clear()
            self.manager.draw()
            super().on_draw()

        def on_update(self, delta_time: float) -> bool | None:
            super().on_update(delta_time)

        def show_main_windows(self) -> None:

            sm = g.sm

            def create_menu_buttons():
                save_folder = g.get_save_path()
                with open(
                    os.path.join(save_folder, g.DEFAULT_DATA_FILE_NAME),
                    "r",
                    encoding="UTF-8",
                ) as data:
                    data = json.load(data)
                volumes = data["options"]

                def return_to_main_menu(event=None):
                    game = Views.GameMenu(False)

                    self.manager.clear()

                    self.window.show_view(game)

                def show_fps(event=None):
                    g.sm.Volume.show_fps = not g.sm.Volume.show_fps

                def edit_window_mode(event=None):
                    old_value = g.sm.Volume.window_mode

                    if old_value == "full-screen":
                        window_mode = "window"
                        window_mode_text = "Оконный"
                    else:
                        window_mode = "full-screen"
                        window_mode_text = "Полный экран"

                    g.sm.Volume.window_mode = window_mode

                    self.window_mode_button.text = window_mode_text

                def edit_telemetry(event=None):
                    g.sm.Volume.telemetry = not g.sm.Volume.telemetry
                    self.telemetry_button.text = (
                        "Включено" if g.sm.Volume.telemetry else "Выключено"
                    )

                STYLE_DEFAULT_BUTTON = g.STYLE_DEFAULT_BUTTON
                FONT_NAME = g.FONT_NAME

                everything_vbox = arcade.gui.UIBoxLayout(space_between=20)
                everything_ui_anchor_layout = arcade.gui.UIAnchorLayout()
                everything_ui_anchor_layout.add(
                    child=everything_vbox, anchor_x="center_x", anchor_y="center_y"
                )

                self.manager.add(everything_ui_anchor_layout)

                buttons_1_vbox = arcade.gui.UIBoxLayout(space_between=0)

                return_button = agui.UIFlatButton(
                    text="Назад", width=300, height=50, style=STYLE_DEFAULT_BUTTON
                )
                return_button.on_click = return_to_main_menu
                buttons_1_vbox.add(return_button)

                buttons_1_vbox.add(arcade.gui.UISpace(height=20))

                FPS_check_box = agui.UIFlatButton(
                    text="Счтчик FPS", width=300, height=50, style=STYLE_DEFAULT_BUTTON
                )
                FPS_check_box.on_click = show_fps
                buttons_1_vbox.add(FPS_check_box)

                ui_anchor_layout = arcade.gui.UIAnchorLayout()
                ui_anchor_layout.add(
                    buttons_1_vbox, anchor_x="center_x", anchor_y="center_y"
                )

                everything_vbox.add(ui_anchor_layout)

                everything_vbox.add(arcade.gui.UISpace(height=50))

                music_volume_label = agui.UILabel(
                    "Музыка", text_color=arcade.color.BLACK, font_name=FONT_NAME
                )
                self.v_box.add(music_volume_label)

                self.music_volume_slider = UISliderSavesUpdater(
                    "music",
                    value=volumes["volume"]["music"] * 100,  # начальное значение
                    min_value=0,
                    max_value=200,
                    width=300,
                    height=20,
                    start_value=g.DEFAULT_OPTIONS_PARAM["volume"]["music"] * 100,
                )
                self.v_box.add(self.music_volume_slider)
                self.v_box.add(arcade.gui.UISpace(height=20))

                sound_volume_label = agui.UILabel(
                    "Звуки", text_color=arcade.color.BLACK, font_name=FONT_NAME
                )
                self.v_box.add(sound_volume_label)

                self.sound_volume_slider = UISliderSavesUpdater(
                    "sound",
                    value=volumes["volume"]["sound"] * 100,  # начальное значение
                    min_value=0,
                    max_value=200,
                    width=300,
                    height=20,
                    start_value=g.DEFAULT_OPTIONS_PARAM["volume"]["sound"] * 100,
                )
                self.v_box.add(self.sound_volume_slider)
                self.v_box.add(arcade.gui.UISpace(height=20))

                """voice_volume_label = agui.UILabel(
                    "Голос",
                    text_color=arcade.color.BLACK,
                    font_name=FONT_NAME
                )
                self.v_box.add(voice_volume_label)

                self.voice_volume_slider = UISliderSavesUpdater(
                    "voice",
                    sm,
                    am,
                    value=volumes['volume']["voice"]*100,  # начальное значение
                    min_value=0,
                    max_value=200,
                    width=300,
                    height=20,
                    start_value=g.DEFAULT_OPTIONS_PARAM["volume"]["voice"]*100
                )
                self.v_box.add(self.voice_volume_slider)
                self.v_box.add(arcade.gui.UISpace(height=20))"""

                self.lps_slider = UISliderSavesUpdater(
                    "lps",
                    value=volumes["lps"],  # начальное значение
                    min_value=0.1,
                    max_value=3.0,
                    width=300,
                    height=20,
                    start_value=g.DEFAULT_OPTIONS_PARAM["lps"],
                )
                self.v_box_1.add(self.lps_slider)
                lps_label = agui.UILabel(
                    "Скорость появления букв",
                    text_color=arcade.color.BLACK,
                    font_name=FONT_NAME,
                )
                self.v_box_1.add(lps_label)
                self.v_box_1.add(arcade.gui.UISpace(height=20))

                self.fade_speed_slider = UISliderSavesUpdater(
                    "fade_speed",
                    value=volumes["fade_speed"],  # начальное значение
                    min_value=0.0,
                    max_value=2.0,
                    width=300,
                    height=20,
                    start_value=g.DEFAULT_OPTIONS_PARAM["fade_speed"],
                )
                self.v_box_1.add(self.fade_speed_slider)
                fade_speed_label = agui.UILabel(
                    "Скорость переходов",
                    text_color=arcade.color.BLACK,
                    font_name=FONT_NAME,
                )
                self.v_box_1.add(fade_speed_label)

                self.main_h_box.add(self.v_box_1)
                self.main_h_box.add(self.v_box)

                everything_vbox.add(self.main_h_box)

                buttons_2_vbox = arcade.gui.UIBoxLayout(space_between=10)

                window_mode_text = agui.UILabel(
                    "Режим окна", text_color=arcade.color.BLACK, font_name=FONT_NAME
                )
                window_mode_text.center_x = self.center_x
                window_mode_text.center_y = self.height * 0.3
                buttons_2_vbox.add(window_mode_text)

                old_value = g.sm.Volume.window_mode
                self.window_mode_button = agui.UIFlatButton(
                    text="Полный экран" if old_value == "full-screen" else "Оконный",
                    width=300,
                    height=50,
                    style=STYLE_DEFAULT_BUTTON,
                )
                self.window_mode_button.on_click = edit_window_mode
                self.window_mode_button.center_x = self.center_x
                self.window_mode_button.center_y = self.height * 0.25
                buttons_2_vbox.add(self.window_mode_button)

                buttons_2_vbox.add(arcade.gui.UISpace(height=20))

                window_mode_text = agui.UILabel(
                    "Телеметрия", text_color=arcade.color.BLACK, font_name=FONT_NAME
                )
                window_mode_text.center_x = self.center_x
                window_mode_text.center_y = self.height * 0.18
                buttons_2_vbox.add(window_mode_text)

                if not hasattr(g.sm.Volume, "telemetry"):
                    g.sm.Volume.telemetry = True

                self.telemetry_button = agui.UIFlatButton(
                    text="Включено" if g.sm.Volume.telemetry else "Выключено",
                    width=300,
                    height=50,
                    style=STYLE_DEFAULT_BUTTON,
                )
                self.telemetry_button.on_click = edit_telemetry
                self.telemetry_button.center_x = self.center_x
                self.telemetry_button.center_y = self.height * 0.13
                buttons_2_vbox.add(self.telemetry_button)

                everything_vbox.add(buttons_2_vbox)

            create_menu_buttons()

        def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
            if symbol == arcade.key.ESCAPE:
                game = Views.GameMenu(False)
                self.manager.clear()
                self.window.show_view(game)


def init_file() -> None:
    """
    Инициализирует основные классы
    """

    logger.info("Инициализация...")

    timee = time.time()

    g.actions = Actions()

    logger.debug("Инициализация [1/8]: Saves_manager")
    g.sm = Saves_manager()

    logger.debug("Инициализация [2/8]: FilesManager")
    g.fm = FilesManager()

    from .game_views import GameViews
    g.GameViews = GameViews()

    logger.debug("Инициализация [3/8]: AudioManager")
    g.am = AudioManager()

    logger.debug("Инициализация [4/8]: Scene")
    g.scene = Scene()

    logger.debug("Инициализация [5/8]: LoreManager")
    g.lm = LoreManager()

    logger.debug("Инициализация [6/8]: DiscordActor")
    g.da = Discord_act()

    logger.debug("Инициализация [7/8]: Attributes")
    g.attributes = Attributes()

    logger.debug("Инициализация [8/8]: ListCharacters")
    g.ListCharacters = ListCharacters()

    logger.info(f"Инициализация завершена за {round(time.time() - timee, 3)} сек")
