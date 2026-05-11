import arcade
from arcade import SpriteList
from pyglet.event import EVENT_HANDLE_STATE
import arcade.gui as agui
import arcade.gui.widgets.layout
from typing import Optional, Literal, Tuple, Union
import time
import os
import random
import json
import uuid
from typing import Generator
from webbrowser import open_new_tab as web_open
from pyglet.gl.lib import GLException
from PIL import Image
from collections import Counter

from .gui import UISliderVertical, Managers, UISliderSavesUpdater, MovableBlock, MovableBlockFalling, ItemsNotifText, ClickableSprite
from .scene import Scene
from .lore_viewer import Wwl
from .lore_logger import LoreLogger
from .waiter import Waiter
from .saves import Saves_manager
from .namespace import Namespace
from .actions import Actions
from .audio import AudioManager
from .presence import Discord_act
from .files_manager import FilesManager
from .character import ListCharacters, Attributes
from .Exceptions import VolumeDoesNotExistError

from .globals import g

arcade.load_font("game/fonts/Kurale-Regular.ttf")

wait_trigger = Waiter()


class Views:

    class MainWindow(arcade.Window):
        def __init__(self, width, height, title, resizable=True):
            super().__init__(width=width, height=height, title=title, resizable=resizable)
            self.GameView: Optional[Views.GameView] = None

            g.All_views = Views

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


    class Main_template(arcade.View):
        def __init__(self) -> None:
            """
            Является "Шаблоном".
            Создаёт счётчик ФПС и отвечает за курсор
            """
            super().__init__()

            self.window.set_mouse_visible(False)

            self.scale = arcade.get_screens()[0].get_scale()

            self.cursor_texture = arcade.Sprite("game/images/gui/cursor.png", 0.2)
            self.window.background_color = arcade.color.WHITE
            self.background_color = arcade.color.WHITE
            self.fps = {
                'window': [],
                'window_size': 100,
                'last_print_time': time.time(),
                'avg_fps': 0.0,
                'min_fps': 0.0,
                'max_fps': 0.0,
                'label': arcade.Text(
                    f"FPS: Avg=0, Min=0, Max=0, Window size: 0. Vsync: {self.window.vsync}",
                    x=10,
                    y=self.window.height - 10,
                    color=arcade.color.ARCADE_GREEN,
                    font_size=14,
                    anchor_x="left",
                    anchor_y="top",
                )
            }

        def cleanup_ui(self):
            if hasattr(self, 'manager'):
                self.manager.clear()
                self.manager.disable()

            if hasattr(self, 'menu_manager'):
                self.menu_manager.clear()
                self.menu_manager.disable()

            if hasattr(self, 'settings_manager'):
                if hasattr(self.settings_manager, 'clear'):
                    self.settings_manager.clear()

            if hasattr(self, 'splash_manager'):
                self.splash_manager.clear()
                self.splash_manager.disable()

            if hasattr(self, 'in_game_manager'):
                if hasattr(self.in_game_manager, 'clear'):
                    self.in_game_manager.clear()

        def _get_amend_color(self, border_thickness=20):

            if list(g.scene["bg"].values()):
                sprite: arcade.Sprite = list(g.scene["bg"].values())[-1]
                print(sprite.texture.file_path.name)
            elif g.scene["bg_parallax"]:
                sprite: arcade.Sprite = g.scene["bg_parallax"][0]['sprite']
            else:
                return None

            if not hasattr(sprite, 'texture') or sprite.texture is None:
                return None

            img = sprite.texture.image
            if img.mode != 'RGB':
                img = img.convert('RGB')

            img.thumbnail((img.width*0.5, img.height*0.5))
            width, height = img.size

            border = min(border_thickness, width // 2, height // 2)

            if border <= 0:
                pixels = list(img.getdata())
            else:
                parts = [
                    img.crop((0, 0, width, border)),  # top
                    img.crop((0, height - border, width, height)),  # bottom
                    img.crop((0, border, border, height - border)),  # left
                    img.crop((width - border, border, width, height - border)),  # right
                ]

                pixels = []

                for part in parts:
                    pixels.extend(part.getdata())

            if not pixels:
                return None

            count = len(pixels)

            red = sum(p[0] for p in pixels) // count
            green = sum(p[1] for p in pixels) // count
            blue = sum(p[2] for p in pixels) // count

            return (red, green, blue)

        def set_bg_by_scene_bg(self):
            color = self._get_amend_color()
            if color:
                self.background_color = color

        def on_update(self, delta_time: float) -> None:
            if "x" in self.window.mouse.data and "y" in self.window.mouse.data:
                mouse_x, mouse_y = self.window.mouse.data["x"], self.window.mouse.data["y"]
                self.cursor_texture.position = (mouse_x, mouse_y)

            if Saves_manager().Volume.get_other("show_fps"):
                current_fps = 1.0 / delta_time if delta_time > 0 else 0

                self.fps['window'].append(current_fps)
                if len(self.fps['window']) > self.fps['window_size']:
                    self.fps['window'].pop(0)

                if time.time() - self.fps['last_print_time'] >= 1.0:
                    self.fps['avg_fps'] = sum(self.fps['window']) / len(self.fps['window'])
                    self.fps['min_fps'] = min(self.fps['window'])
                    self.fps['max_fps'] = max(self.fps['window'])

                    self.fps['label'].text = (f"FPS: Avg={int(self.fps['avg_fps'])}, Min={int(self.fps['min_fps'])}, Max={int(self.fps['max_fps'])}, "
                                              f"Window size: {self.fps['window_size']}. "
                                              f"Vsync: {self.window.vsync}")

                    self.fps['last_print_time'] = time.time()

        def on_mouse_leave(self, x: int, y: int) -> bool | None:
            self.cursor_texture.alpha = 0

        def on_mouse_enter(self, x: int, y: int) -> bool | None:
            self.cursor_texture.alpha = 255


        def on_draw(self) -> None:

            try:
                if self.cursor_texture:
                    arcade.draw_sprite(self.cursor_texture)
            except (GLException, AttributeError):
                # Если возникла ошибка OpenGL, пробуем пересоздать курсор
                try:
                    self.cursor_texture = arcade.Sprite("game/images/gui/cursor.png", 0.2)
                    arcade.draw_sprite(self.cursor_texture)
                except:
                    pass

            if Saves_manager().Volume.get_other("show_fps"):
                arcade.draw_lrbt_rectangle_filled(
                    left=5,
                    right=8*len(self.fps['label'].text),
                    bottom=self.window.height - 35,
                    top=self.window.height - 10,
                    color=(0, 0, 0, 200)
                )
                self.fps['label'].draw()

    class GameView(Main_template):

        def __init__(self, session_id: Optional[str] = None) -> None:
            """
            Отвечает за основное окно новельной части
            :param session_id: Айди сессии
            """
            super().__init__()

            self.window_mode = g.sm.Volume.get_other("window_mode")
            if self.window_mode == "full-screen":
                self.window.set_fullscreen(True)
            elif self.window_mode == "window":
                self.window.set_fullscreen(False)
                self.window.maximize()

            g.main = self

            g.am.stop_music()
            g.am.stop_sound()

            #self.window.set_vsync(True)

            self.delta_time = 0.0

            self.dialog_window: Optional[arcade.Sprite] = None

            self.show_dialogue_bg_trigger = True

            self.scene = g.scene

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
                texture = arcade.load_texture("game/images/gui/dialog_window.png")

                self.dialog_window = arcade.Sprite(
                    texture,
                    scale=6 * min(self.width / 1920, self.height / 1080),
                    center_x=self.width * 0.5,
                    center_y=self.height * 0.13
                )

                #blackscreen
                texture = arcade.load_texture("game/images/gui/blackscreen.png")

                sprite = arcade.Sprite(
                    texture,
                    scale=50,
                    center_x=self.width * 0.5,
                    center_y=self.height * 0.5
                )
                sprite.alpha = 0
                self.scene.add_sprite("fade", "fade", sprite)

                #splash
                texture = arcade.load_texture("game/images/gui/splash.png")

                sprite = arcade.Sprite(
                    texture,
                    center_x=self.width * 0.5,
                    center_y=self.height * 0.5
                )
                sprite.alpha = 0
                self.scene.add_sprite("fade", "splash", sprite)

                text = agui.UILabel(
                    " ",
                    y=self.height * 0.82,
                    align="center",
                    width=self.width,
                    font_name=g.FONT_NAME,
                    text_color=(255, 255, 255, 0),
                    font_size=72
                )
                text_small = agui.UILabel(
                    " ",
                    y=self.height * 0.77,
                    align="center",
                    width=self.width,
                    font_name=g.FONT_NAME,
                    text_color=(255, 255, 255, 0),
                    font_size=28
                )

                self.splash_manager.add(text)
                self.splash_manager.add(text_small)

            create_widgets()

            self.start_trigger: bool = True

            self.session_id = ""

            self.NAMESPACE = Namespace()

            self.session_data = {"name": "", "description": "", "session_start": round(time.time())}

            def load_saves(session_id):
                """
                Загружает сохранение
                """
                if session_id is None:
                    self.session_id = str(uuid.uuid4())
                else:
                    wwl = g.wwl
                    self.session_id = str(uuid.uuid4())
                    save = g.sm.Save.get_save(session_id)
                    wwl.label = save["label"]
                    wwl.pose = save["position"]

                    for i, o in save["defines"].items():
                        self.NAMESPACE["Define"].__setattr__(i, o)

                    _files_manager = save["files_manager"]

                    assets = list(_files_manager["loaded_textures"].keys()) + list(_files_manager["loaded_audios"].keys())

                    thread = g.fm.load_assets(assets, "loading_ponn")

                    #while thread.is_alive():
                    #    continue

                    wwl._preload_assets(wwl.label)
                    if wwl.label in wwl.graf:
                        for i in wwl.graf[wwl.label]:
                            wwl._preload_assets(i)

                    old_scene = save["scene"]
                    g.scene.characters_slice = old_scene["characters_slice"]

                    for i in old_scene["bg"]:
                        bg_sprite = arcade.Sprite(i["path"])
                        bg_sprite.size = tuple(i["size"])
                        bg_sprite.position = tuple(i["pos"])
                        self.scene.add_sprite("bg", i["layer"], bg_sprite)

                    for i in old_scene["sprites"]:
                        if isinstance(i["path"], str):
                            sprite = arcade.Sprite(i["path"])
                        elif isinstance(i["path"], list):
                            anim = arcade.TextureAnimation([arcade.TextureKeyframe(g.scene.get_texture(i)) for i in i["path"]])
                            sprite = arcade.TextureAnimationSprite(animation=anim)

                        sprite.size = tuple(i["size"])
                        sprite.position = tuple(i["pos"])
                        self.scene.add_sprite("sprites", i["id"], sprite)


                    if old_scene["music"]["path"] is not None:
                        g.am.play_music(old_scene["music"]["path"], volume=old_scene["music"]["volume"])
                    else:
                        g.am.stop_sound()
                        g.am.stop_music()

                    for i in old_scene["bg_parallax"]:
                        while True:
                            try:
                                self.scene.add_parallax_bg(i["path"], i["speed"], i["original_x"], i["original_y"])
                            except AttributeError:
                                continue
                            else:
                                break

                    self.session_data["name"] = save["session_data"]["name"]
                    self.session_data["description"] = save["session_data"]["description"]

                    self.window.GameView = self

                    self.set_bg_by_scene_bg()

            load_saves(session_id)

            self.actions = Actions()

            self.settings_manager = Managers.SettingsManager()
            self.settings_manager.enable()

            self.characters_texts_manager = Managers.CharactersTextManager()
            self.characters_texts_manager.enable()

            self.LoreLogger = LoreLogger()

            self.in_game_manager = Managers.InGameManager()
            self.in_game_manager.settings_button.on_click = self.settings_manager.turn_visibl
            self.in_game_manager.return_button.on_click = self.LoreLogger.return_back
            self.in_game_manager.skip_button.on_click = lambda event=None: self.waiting_autoskip.switch()
            self.in_game_manager.enable()
            #self.in_game_manager.return_button.on_click = self.LoreLogger.return_back

            self.talk_manager(clicked=False)

            self.on_resize(int(self.width), int(self.height))

        def _update_dialog_window(self, width, height):
            self.dialog_window.width = width
            self.dialog_window.center_x = width * 0.5
            self.dialog_window.bottom = 0

        def on_resize(self, width: int, height: int) -> bool | None:
            self.settings_manager.update_size(width, height)
            self.characters_texts_manager.update_pos(width, height)
            self._update_dialog_window(width, height)
            self.scene.on_resize(width, height)

        def chanel(self):
            time.sleep(0.05)

            self.actions.active_generators.clear()

            g.am.stop_sound()
            g.am.stop_music()
            g.am.stop_voice()

            self.window.set_fullscreen(False)
            self.window.size = (1024, 786)
            game = Views.GameMenu(show_lc=True)
            self.window.show_view(game)

        def talk_manager(self, pos_offset: Optional[int] = None, clicked: bool = True, do_snapshot: bool = True) -> None:
            """
            Получает инструкции сценария и запускает функцию talk(), обрабатывая её результаты
            """

            gens = self.actions.active_generators
            if gens.active_generators_consistently:
                if gens.active_generators_consistently[0][0].startswith('talk'):
                    while gens.active_generators_consistently[0][0].startswith("talk"):
                        gens._update_consistently(1 / 1000)
                        if not gens.active_generators_consistently:
                            break
                    return

            gen = self.actions.active_generators.active_generators_consistently
            if gen:
                if clicked:
                    self.cursor_texture.alpha = 255
                    if gen[0][0] != 'talk':
                        g.attributes.reset()
                        return
                    else:
                        if time.time() - self.last_text_skip < 0.1:
                            return
                        else:
                            self.last_text_skip = time.time()

            if self.actions.active_generators.active_generators_consistently and not clicked:
                self.waiting_talk.on()
                return

            g.attributes.reset()
            now = g.wwl.get_thing(pos_offset)
            print(now)
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

                match now['action']:

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

                    case "SHOW_SPLASH":
                        if (now["data"]["name"] != ")" and now["data"]["name"]) or now["data"]["description"] != '':
                            if now["data"]['show_splash']:
                                self.actions.start_action("show_splash", now["data"], "together")
                            g.da.update(now["data"]["name"], now["data"]["description"])
                            self.session_data["description"] = str(now["data"]["description"])
                            self.session_data["name"] = str(now["data"]["name"])


                        return "NEXT"

                    case _:
                        print(f"Неопознанная команда: {now}")
                        return "NEXT"

        def on_draw(self) -> None:
            if not self.start_trigger:
                self.clear()
                self.scene.draw()
                self.splash_manager.draw()
                if self.show_dialogue_bg_trigger:
                    arcade.draw_sprite(self.dialog_window)
                self.characters_texts_manager.draw()
                self.in_game_manager.draw()
                self.menu_manager.draw()
                self.settings_manager.draw()
            super().on_draw()

        def on_update(self, delta_time) -> None:

            self.delta_time = delta_time

            self.scene.update(delta_time)

            self.menu_manager.on_update(delta_time)

            self.actions.update(delta_time)

            self.characters_texts_manager.update(delta_time)

            if self.waiting_autoskip:
                self.talk_manager(clicked=True)

            if self.waiting_talk:
                self.talk_manager(clicked=False)
            
            super().on_update(delta_time)

        def on_key_press(self, key, modifiers) -> None:
            if (key == arcade.key.SPACE or key == arcade.key.ENTER) and not self.settings_manager.waiting_settings:
                self.waiting_autoskip.off()
                self.talk_manager()
            if key == arcade.key.S or key == arcade.key.ESCAPE:
                self.settings_manager.turn_visibl()
            if key == arcade.key.B:
                wwl = g.wwl
                fm = g.fm

                text = f"""
                \n
                Данные на текущий момент игры:
                
                ===== ЛЕЙБЛ =====
                - Лейбл: {wwl.label}
                - Позиция: {wwl.pose}
                - Граф сюжета: {wwl.graf}
                - Текущий файл сценария: {wwl.now_file}
                - Найдено файлов сценария: {len(wwl.files)}
                
                ===== АССЕТЫ =====
                - Текстуры: ЗАГРУЖЕНО: {len(fm.textures)}, НЕ ЗАГРУЖЕНО: {len(fm.textures_paths) - len(fm.textures)}
                - Аудио: ЗАГРУЖЕНО: {len(fm.audios)}, НЕ ЗАГРУЖЕНО: {len(fm.audio_paths) - len(fm.audios)}
                - Активные спрайты: {self.scene.len_loaded_textures}
                \n
                """

                print("\n".join([i.lstrip(" ") for i in text.split("\n")]))

        def on_mouse_release(self, x, y, button, modifiers) -> None:
            if (int(button) == 1) and not self.settings_manager.waiting_settings:
                if len(list(self.in_game_manager.get_widgets_at((x, y)))) == 1: # Проверяем, не нажали ли мы на какую-нибудь кнопку.
                    self.waiting_autoskip.off()
                    self.talk_manager()

        def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> bool | None:
            self.scene.on_mouse_motion(x, y)

    class GameMenu(Main_template):
        def __init__(self, show_lc: bool = True) -> None:
            """
            Отвечает за главное меню игры
            :param show_lc: если True, отображает загрузочный экран и инициализирует основные класса
            """
            super().__init__()

            self.deleted = 0

            self.window.set_vsync(False)

            self.bg_sprite = arcade.Sprite("game/images/gui/bg_main_menu.png")
            self.bg_sprite.center_x = self.center_x
            self.bg_sprite.center_y = self.center_y

            self.bg_other_sprite = arcade.Sprite("game/images/gui/bg_eblani.png")
            self.bg_other_sprite.center_x = self.width * 0.15
            self.bg_other_sprite.center_y = self.height * 0.3
            self.bg_other_sprite.scale  = 0.3

            self.loading_screen = arcade.Sprite("game/images/gui/JE3000_logo-export.png", 1)
            self.loading_screen.position = (int(self.center_x), int(self.center_y))
            self.loading_screen_fade = arcade.Sprite("game/images/gui/blackscreen.png")
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
                    width=self.window.width*0.9,
                    multiline=True,
                    font_size=40,
                    x=self.center_x,
                    y=self.center_y
                )
            self.other_manager  = agui.UIManager()
            self.other_manager.add(self.other_text)

            self.vokhanalia = False

            if show_lc:
                self.show_ls()

        def on_resize(self, width: int, height: int) -> bool | None:
            self.bg_sprite.center_x, self.bg_sprite.top = self.center_x, self.height
            self.bg_other_sprite.center_x, self.bg_other_sprite.center_y = self.width * 0.15, self.height * 0.3

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

                init_file()
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
                g.am.play_music("game/music/buttercup by jack stauber (but kazoo).mp3")
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
                g.am.play_music("game/music/Lucid Blocks OST： Corner.mp3", streaming=True, loop=True)

                class Vokhanalia_view(arcade.View):

                    def __init__(self, text):
                        super().__init__()

                        self.text = text

                        file = "./game/images/scenes/sorry1.png"
                        self.file = arcade.Sprite(file)
                        self.background_color = arcade.color.BLACK
                        self.lst = arcade.SpriteList()
                        self.window.center_window()

                        self.width_const, self.height_const = self.width, self.height

                        self.talker = arcade.Text(
                            text.text,
                            self.window.width / 2, self.window.height / 2,
                            color=arcade.color.WHITE,
                            multiline=True,
                            width=self.window.width - 100,
                            font_size=30,
                            anchor_x="center",
                            anchor_y="center",
                            align="center"
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
                                self.text.text = " ".join(words[:word_index + 1])
                                word_index += 1
                                continue

                            timer += dt
                            words_to_add = int(timer * 20)
                            if words_to_add > 0:
                                word_index = min(word_index + words_to_add, len(words))
                                self.text.text = " ".join(words[:word_index])
                                timer -= words_to_add / 20

                        self.main_gen = None

                    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
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

                        self.window.set_size(self.width_const + random.randint(-50, 50),
                                             self.height_const + random.randint(-50, 50))

                        self.last_update = time.time()

                        self.window.center_window()

                    def on_draw(self) -> bool | None:
                        self.clear()
                        self.lst.clear()

                        self.talker.position = (
                            self.center_x + random.randint(-1, 1), self.center_y + random.randint(-1, 1)
                        )
                        self.talker.text = self.text.text

                        if time.time() - self.last_update_eye > 0.1:
                            for i in range(10):
                                self.last_update_eye = time.time()
                                file = arcade.Sprite(self.file.texture)
                                file.color = (
                                    255, 255, 255, 120
                                )

                                file.center_x = random.randint(0, self.window.width)
                                file.center_y = random.randint(0, self.window.height)
                                if random.random() >= 0.5:
                                    file.scale_x = random.random() * random.randint(1, 30) / 10
                                else:
                                    file.scale_y = random.random() * random.randint(1, 30) / 10
                                self.lst.append(file)

                        self.lst.draw()
                        self.talker.draw()

                class VokhanaliaText():
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
                    window = arcade.open_window(1000, 600, window_title="Почему?", resizable=False, style="borderless")
                    window.center_window()
                    view = Vokhanalia_view(text)
                    window.show_view(view)

            self.loading_generator = vokhanalia()


        def start_vzlom(self, event=None):
            orig_window = (self.window.height, self.window.width)
            self.window.on_close = lambda : print("No")
            self.window.on_deactivate = lambda : self.window.activate()
            def vslom():
                g.am.play_music("game/music/ambience-reactor.mp3")
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
                        oth_manager.on_update(1/60)
                        self.window.set_size(orig_window[1] + random.randint(-100, 100),
                                             orig_window[0] + random.randint(-100, 100))
                        self.window.center_window()
                        if random.random() > 0.9:
                            self.background_color = arcade.color.BLACK
                        else:
                            self.background_color = arcade.color.WHITE
                        yield

                last_time = time.time()
                g.am.play_music("game/music/Never gonna give you up (a very bad kazoo cover).mp3")
                while time.time() - last_time < 10:
                    self.window.set_size(orig_window[1] + random.randint(-10, 10), orig_window[0] + random.randint(-10, 10))
                    self.window.center_window()
                    yield

                self.window.set_size(1024, 1)
                yield
                self.window.set_size(1024, 786)
                self.manager.remove(self.manager.children[0][-1])
                with open(rf"C:\Users\{os.getlogin()}\Desktop\JopaJam{uuid.uuid4()}.txt", "w", encoding="UTF-8") as file:
                    file.write("https://youtu.be/mn6brnRQPHs?si=nGHy9Eq1ci-wJg0z\n")
                    file.write("Дата-майнинг это слишком просто для меня. Я способен на большее.\n"*100000)

                self.main_lebel.text = "Скачивание данных пользователя..."
                base_path = rf"C:\Users\{os.getlogin()}"


                for root, dirs, files in os.walk(base_path):
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    self.other_text.center_x = self.center_x
                    self.other_text.center_y = self.center_y

                    if root.count("\\") > 6:
                        continue

                    if len(dirs) > 2:
                        self.other_text.text = os.path.join(root, dirs[-1]).replace("\\", "\\ ")

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
                g.am.play_music("game/sounds/sfx/strashilka.mp3", volume=20.0)
                last_time = time.time()
                while time.time() - last_time < 29:
                    self.cursor_texture.alpha = 0 if random.random() > 0.95 else 255
                    yield
                while time.time() - last_time < random.randint(2, 10):
                    yield
                yield
                self.cursor_texture.alpha = 255
                g.am.play_sound("game/sounds/sfx/perdezh_YQ5l54B.mp3")

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

        def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> EVENT_HANDLE_STATE:
            self.is_mouse_pressed = True

        def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> EVENT_HANDLE_STATE:
            self.is_mouse_pressed = False

        def on_key_press(self, key: int, modifiers: int) -> None:
            if (key == arcade.key.L and modifiers & arcade.key.MOD_SHIFT) and not self.is_loading:
                self._start_vokhanalia()
                self.is_loading  = True

        def cleanup_ui(self):
            if hasattr(self, 'manager'):
                self.manager.clear()
                self.manager.disable()

            if hasattr(self, 'menu_manager'):
                self.menu_manager.clear()
                self.menu_manager.disable()

            if hasattr(self, 'settings_manager'):
                if hasattr(self.settings_manager, 'clear'):
                    self.settings_manager.clear()

            if hasattr(self, 'splash_manager'):
                self.splash_manager.clear()
                self.splash_manager.disable()

            if hasattr(self, 'in_game_manager'):
                if hasattr(self.in_game_manager, 'clear'):
                    self.in_game_manager.clear()

        def show_main_windows(self) -> None:

            def create_menu_buttons():
                self.manager.clear()

                def start_game(event=None):

                    self.window.center_window()
                    self.cleanup_ui()
                    self.window.set_fullscreen(False)
                    self.window.size = g.DEFAULT_IN_GAME_WINDOW_SIZE
                    #self.window.set_fullscreen(True)
                    self.manager.disable()
                    game = Views.GameView()
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
                    width=self.window.width*0.9,
                    multiline=True,
                    font_size=40
                )
                self.main_lebel.center_y = self.height * 0.7
                self.main_lebel.center_x = self.width * 0.5
                self.manager.add(self.main_lebel)

                start_button = agui.UIFlatButton(
                    text="Начать игру",
                    width=200,
                    style=STYLE_DEFAULT_BUTTON
                )
                start_button.on_click = start_game
                self.v_box.add(start_button)

                settings_button = agui.UIFlatButton(
                    text="Загрузить",
                    width=200,
                    style=STYLE_DEFAULT_BUTTON
                )
                settings_button.on_click = open_saves
                self.v_box.add(settings_button)

                settings_button = agui.UIFlatButton(
                    text="Настройки",
                    width=200,
                    style=STYLE_DEFAULT_BUTTON
                )
                settings_button.on_click = open_settings
                self.v_box.add(settings_button)

                exit_button = agui.UIFlatButton(
                    text="Выход",
                    width=200,
                    style=STYLE_DEFAULT_BUTTON
                )
                exit_button.on_click = lambda event: self.window.on_close()
                self.v_box.add(exit_button)

                ui_anchor_layout = arcade.gui.UIAnchorLayout()
                ui_anchor_layout.add(child=self.v_box)
                ui_anchor_layout.center_y = self.window.height * -0.3

                self.manager.add(ui_anchor_layout)


                dataminer_v_box = arcade.gui.UIBoxLayout(space_between=20)
                dataminer_ui_anchor_layout = arcade.gui.UIAnchorLayout()
                dataminer_ui_anchor_layout.add(dataminer_v_box, anchor_y="center", anchor_x="right", align_x=-20, align_y=-100)
                self.manager.add(dataminer_ui_anchor_layout)

                dataminer = agui.UIFlatButton(  # сасите письку
                    text="ВКЛЮЧИТЬ ратник",
                    width=300,
                    height=60,
                    style=STYLE_DEFAULT_BUTTON,
                    x=self.window.width * 0.70,
                    y=self.window.height * 0.3,
                    multiline=False,
                    align="center"
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
                    align="center"
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
            self.saves = saves + [[None]]*(20 - len(saves))
            self.saves_len = 20

            self.background_color = (199, 100, 131)

            self.slider: Optional[UISliderVertical]  = None

            self.manager = agui.UIManager()
            self.manager.enable()

            self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)
            self.v_box.center_x = self.window.width/2-300
            self.manager.add(self.v_box)

            self.choise = 0

            self.generate_buttons()

        def cleanup_ui(self):
            super().cleanup_ui()
            if hasattr(self, 'slider'):
                self.slider = None
            if hasattr(self, 'v_box'):
                self.v_box.clear()
            self.manager.disable()

        def generate_buttons(self) -> None:

            self.manager.clear()

            saves = g.sm.Save.get_all_saves()
            self.saves = saves + [[None]] * (20 - len(saves))

            self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)
            self.v_box.center_x = self.window.width / 2 - 300
            self.manager.add(self.v_box)

            FONT_NAME = g.FONT_NAME

            _STYLE_DEFAULT_BUTTON = {
                "normal": arcade.gui.UIFlatButton.UIStyle(
                    font_size=20,
                    font_name=(FONT_NAME,),
                    font_color=arcade.color.BLACK,
                    bg=(225, 184, 1, 255),
                    border=(79, 67, 13, 255),
                    border_width=5
                ),
                "hover": arcade.gui.UIFlatButton.UIStyle(
                    font_size=20,
                    font_name=(FONT_NAME,),
                    font_color=arcade.color.BLACK,
                    bg=(163, 134, 5, 255),
                    border=(79, 67, 13, 255),
                    border_width=5
                ),
                "press": arcade.gui.UIFlatButton.UIStyle(
                    font_size=20,
                    font_name=(FONT_NAME,),
                    font_color=arcade.color.BLACK,
                    bg=(191, 161, 25, 255),
                    border=(79, 67, 13, 255),
                    border_width=5
                ),
                "disabled": arcade.gui.UIFlatButton.UIStyle(
                    font_size=20,
                    font_name=(FONT_NAME,),
                    font_color=arcade.color.LIGHT_STEEL_BLUE,
                    bg=(66, 71, 77)
                )
            }

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

                print("OPENING!")
                print("-"*20)

                game = Views.GameView(session_id)
                self.window.show_view(game)

            def delete_save(event=None):
                session_id = self.saves[self.choise][0]
                if session_id is None:
                    return None
                g.sm.Save.del_save(session_id)
                self.generate_buttons()

            STYLE_DEFAULT_BUTTON = g.STYLE_DEFAULT_BUTTON

            return_button = agui.UIFlatButton(
                text="Назад",
                width=100,
                height=50,
                style=STYLE_DEFAULT_BUTTON,
                x=self.window.width * 0.01,
                y=self.window.height * 0.9
            )
            return_button.on_click = return_to_main_menu
            self.manager.add(return_button)

            return_button = agui.UIFlatButton(
                text="Удалить сохранение",
                width=150,
                height=100,
                style=STYLE_DEFAULT_BUTTON,
                x=self.window.width * 0.01,
                y=self.window.height * 0.5,
                multiline=True
            )
            return_button.on_click = delete_save
            self.manager.add(return_button)

            for i in self.saves:

                text = "Пусто"
                if i[0] is not None:
                    name = i[1]['session_data']['name']
                    description = i[1]['session_data']['description']
                    session_last_time = time.ctime(i[1]['session_data']["session_start"])
                    text = f"{name} : {description}                 {session_last_time}"

                button = agui.UIFlatButton(
                    text=text,
                    width=700,
                    height=200,
                    style=_STYLE_DEFAULT_BUTTON,
                    multiline=True
                )

                if i[0] is not None:
                    button.on_click = lambda event, value=i[0]: open_save(value)

                self.v_box.add(button)
                self.v_box.children[-1].disabled = True

            self.slider = UISliderVertical(
                value=1,
                min_value=1,
                max_value=self.saves_len,
                width=20,
                height=self.window.height - 50,
                step=1
            )
            self.slider.center_x = self.window.width - 20
            self.slider.center_y = self.window.height / 2

            self.manager.add(self.slider)


        def on_draw(self) -> bool | None:
            self.clear()
            if hasattr(self, "manager"):
                self.manager.draw()
            super().on_draw()

        def on_update(self, delta_time: float) -> bool | None:
            if self.window.current_view is self:
                if self.slider:
                    self.v_box.center_y = self.center_y - ((self.saves_len - self.slider.value) * 220 + 100) + (220 * 10)
                    self.choise = int(self.slider.value-1)

                if self.v_box and self.v_box.children:
                    for i in range(self.saves_len):
                        self.v_box.children[i].disabled = True if i != self.choise else False
                super().on_update(delta_time)

        def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> bool | None:
            if (self.saves_len - self.slider.value) + scroll_y >= 0 and (self.saves_len - self.slider.value) + scroll_y < self.saves_len:
                self.slider.value += -scroll_y

    class SettingsMenu(Main_template):
        def __init__(self) -> None:
            """
            Отвечает за меню настроек
            """
            super().__init__()

            self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=0)
            self.v_box_1 = arcade.gui.widgets.layout.UIBoxLayout(space_between=0)
            self.main_h_box = arcade.gui.widgets.layout.UIBoxLayout(vertical=False, space_between=20)

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
            am = g.am

            def create_menu_buttons():
                save_folder = sm.get_save_path()
                with open(os.path.join(save_folder, 'saves.JSON'), "r", encoding="UTF-8") as data:
                    data = json.load(data)
                volumes = data['options']

                def return_to_main_menu(event=None):
                    game = Views.GameMenu(False)
                    self.window.show_view(game)

                def show_fps(event=None):
                    g.sm.Volume.set_other("show_fps", not g.sm.Volume.get_other("show_fps"))
                    g.sm.Volume._save_data()

                def edit_window_mode(event=None):
                    old_value = g.sm.Volume.get_other("window_mode")

                    if old_value == "full-screen":
                        window_mode = "window"
                        window_mode_text = "Оконный"
                    else:
                        window_mode = "full-screen"
                        window_mode_text = "Полный экран"

                    g.sm.Volume.set_other("window_mode", window_mode)
                    g.sm.Volume._save_data()

                    print(g.sm.Volume.get_other("window_mode"))

                    self.window_mode_button.text = window_mode_text

                STYLE_DEFAULT_BUTTON = g.STYLE_DEFAULT_BUTTON
                FONT_NAME = g.FONT_NAME

                return_button = agui.UIFlatButton(
                    text="Назад",
                    width=300,
                    height=50,
                    style=STYLE_DEFAULT_BUTTON
                )
                return_button.on_click = return_to_main_menu
                return_button.center_x = self.window.center_x
                return_button.center_y = self.window.height * 0.8
                self.manager.add(return_button)

                FPS_check_box = agui.UIFlatButton(
                    text="Счтчик FPS",
                    width=300,
                    height=50,
                    style=STYLE_DEFAULT_BUTTON
                )
                FPS_check_box.on_click = show_fps
                FPS_check_box.center_x = self.window.center_x
                FPS_check_box.center_y = self.window.height * 0.7
                self.manager.add(FPS_check_box)

                music_volume_label = agui.UILabel(
                    "Музыка",
                    text_color=arcade.color.BLACK,
                    font_name=FONT_NAME
                )
                self.v_box.add(music_volume_label)

                self.music_volume_slider = UISliderSavesUpdater(
                    "music",
                    sm,
                    am,
                    value=volumes['volume']["music"]*100,  # начальное значение
                    min_value=0,
                    max_value=200,
                    width=300,
                    height=20
                )
                self.v_box.add(self.music_volume_slider)
                self.v_box.add(arcade.gui.UISpace(height=20))

                sound_volume_label = agui.UILabel(
                    "Звуки",
                    text_color=arcade.color.BLACK,
                    font_name=FONT_NAME
                )
                self.v_box.add(sound_volume_label)

                self.sound_volume_slider = UISliderSavesUpdater(
                    "sound",
                    sm,
                    am,
                    value=volumes['volume']["sound"]*100,  # начальное значение
                    min_value=0,
                    max_value=200,
                    width=300,
                    height=20
                )
                self.v_box.add(self.sound_volume_slider)
                self.v_box.add(arcade.gui.UISpace(height=20))

                voice_volume_label = agui.UILabel(
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
                    height=20
                )
                self.v_box.add(self.voice_volume_slider)
                self.v_box.add(arcade.gui.UISpace(height=20))



                self.lps_slider = UISliderSavesUpdater(
                    "lps",
                    sm,
                    am,
                    value=volumes["lps"],  # начальное значение
                    min_value=20,
                    max_value=110,
                    width=300,
                    height=20
                )
                self.v_box_1.add(self.lps_slider)
                lps_label = agui.UILabel(
                    "Скорость появления букв",
                    text_color=arcade.color.BLACK,
                    font_name=FONT_NAME
                )
                self.v_box_1.add(lps_label)
                self.v_box_1.add(arcade.gui.UISpace(height=20))

                self.fade_speed_slider = UISliderSavesUpdater(
                    "fade_speed",
                    sm,
                    am,
                    value=volumes["fade_speed"],  # начальное значение
                    min_value=-10,
                    max_value=10,
                    width=300,
                    height=20
                )
                self.v_box_1.add(self.fade_speed_slider)
                fade_speed_label = agui.UILabel(
                    "Скорость переходов",
                    text_color=arcade.color.BLACK,
                    font_name=FONT_NAME
                )
                self.v_box_1.add(fade_speed_label)

                self.main_h_box.add(self.v_box_1)
                self.main_h_box.add(self.v_box)
                ui_anchor_layout = arcade.gui.widgets.layout.UIAnchorLayout()
                ui_anchor_layout.add(child=self.main_h_box, anchor_x="center_x", anchor_y="center_y")

                self.manager.add(ui_anchor_layout)


                window_mode_text = agui.UILabel(
                    "Режим окна",
                    text_color=arcade.color.BLACK,
                    font_name=FONT_NAME
                )
                window_mode_text.center_x = self.center_x
                window_mode_text.center_y = self.height * 0.3
                self.manager.add(window_mode_text)


                old_value = g.sm.Volume.get_other("window_mode")
                self.window_mode_button = agui.UIFlatButton(
                    text="Полный экран" if old_value == "full-screen" else "Оконный",
                    width=300,
                    height=50,
                    style=STYLE_DEFAULT_BUTTON
                )
                self.window_mode_button.on_click = edit_window_mode
                self.window_mode_button.center_x = self.center_x
                self.window_mode_button.center_y = self.height * 0.25
                self.manager.add(self.window_mode_button)

            create_menu_buttons()


    class MenuView(Main_template):
        def __init__(self):
            super().__init__()

            texture = arcade.load_texture("game/images/gui/dialog_window.png")

            self.dialog_window = arcade.Sprite(
                texture,
                scale=6 * min(self.width / 1920, self.height / 1080),
                center_x=self.width * 0.5,
                center_y=self.height * 0.13
            )

            self.actions = g.main.actions
            self.NAMESPACE = g.main.NAMESPACE
            self.fm = g.fm

            self.menu_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

            #self.window.set_vsync(True)
            self.menu_manager = agui.UIManager()
            self.lore = self._lore()
            self.scene = g.scene

            self.settings_manager = Managers.SettingsManager()
            self.settings_manager.enable()

            self.attributes = Attributes()
            self.attributes.character_text_colour = arcade.color.WHITE
            self.attributes.text_anchor = "center"

            self.characters_texts_manager = Managers.CharactersTextManager()
            self.characters_texts_manager.enable()

            self.correct_ans = 0
            self.NAMESPACE["Define"].correct_ans = 0
            next(self.lore)

        def plus(self, do:  bool):
            if do:
                self.correct_ans += 1
            try:
                next(self.lore)
            except StopIteration:
                pass

        def show_menu(self, data) -> None:
            self.menu_manager.clear()
            self.menu_manager.enable()
            self.menu_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

            for k, v in data.items():
                button = agui.UIFlatButton(text=k, width=250, height=100, font_name=g.FONT_NAME, style=g.STYLE_DEFAULT_BUTTON)
                button.on_click = lambda event, do=v: self.plus(do)
                self.menu_v_box.add(button)

            ui_anchor_layout = arcade.gui.widgets.layout.UIAnchorLayout()
            ui_anchor_layout.add(child=self.menu_v_box, anchor_x="center_x", anchor_y="center_y")

            self.menu_manager.add(ui_anchor_layout)

        def on_update(self, delta_time: float) -> None:
            super().on_update(delta_time)
            g.scene.update(delta_time)
            self.characters_texts_manager.update(delta_time)
            self.settings_manager.on_update(delta_time)
            self.menu_manager.on_update(delta_time)

        def on_draw(self) -> None:
            self.clear()
            g.scene.draw()
            arcade.draw_sprite(self.dialog_window)
            self.characters_texts_manager.draw()
            self.menu_manager.draw()
            self.settings_manager.draw()
            super().on_draw()

        def _lore(self):
            self.attributes.character_text = ["Какое из слов является местоимением?"]
            self.show_menu({
                "'Другой'" : True,
                "'Первый'" : False,
                "'Отдельный'" : False,
                "'Вчерашний'" : False
            })
            yield
            self.attributes.character_text = ["Что вы скажете об очень эффективном человеке?"]
            self.show_menu({
                "Супер эфективный" : False,
                "Суперэффективный" : True,
                "Супер эффективный" : False,
                "Супер-эффективный" : False
            })
            yield
            self.attributes.character_text = ["Как правильно?"]
            self.show_menu({
                "ТвОрог": True,
                "ТворОг": True
            })
            yield
            self.NAMESPACE["Define"].correct_ans = self.correct_ans
            self.window.show_view(self.window.GameView)

        def on_key_press(self, key: int, modifiers: int) -> bool | None:
            if key == arcade.key.S or key == arcade.key.ESCAPE:
                self.settings_manager.turn_visibl()

    class MenuViewFood(Main_template):
        def __init__(self):
            super().__init__()

            texture = arcade.load_texture("game/images/gui/dialog_window.png")

            self.dialog_window = arcade.Sprite(
                texture,
                scale=6 * min(self.width / 1920, self.height / 1080),
                center_x=self.width * 0.5,
                center_y=self.height * 0.13
            )

            self.actions = g.main.actions
            self.NAMESPACE = g.main.NAMESPACE
            self.fm = g.fm

            self.bg_image = g.scene.get_sprite("home_kitchen.jpg")
            self.bg_image.center_y = self.center_y
            self.bg_image.center_x = self.center_x

            self.menu_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

            #self.window.set_vsync(True)
            self.menu_manager = agui.UIManager()
            self.lore = self._lore()
            self.scene = g.scene

            self.settings_manager = Managers.SettingsManager()
            self.settings_manager.enable()

            self.attributes = Attributes()
            self.attributes.character_text_colour = arcade.color.WHITE
            self.attributes.text_anchor = "center"

            self.characters_texts_manager = Managers.CharactersTextManager()
            self.characters_texts_manager.enable()

            if not hasattr(self.NAMESPACE["Persistent"], "collected_foods"):
                self.NAMESPACE["Persistent"].collected_foods = []

            if self.NAMESPACE["Persistent"].collected_foods is None:
                self.NAMESPACE["Persistent"].collected_foods = []


            self.available_food = self.NAMESPACE["Data"].get_food_root()
            self.menu = {i[0]: i[1] for i in self.available_food}

            self.food = {}
            for i in self.NAMESPACE["Data"].mix:
                if i not in self.available_food:
                    self.food[i] = False
                else:
                    self.food[i] = True

            if "cooking_omlet" in self.NAMESPACE["Persistent"].collected_foods and \
                    "cooking_bliny" in self.NAMESPACE["Persistent"].collected_foods and \
                    "cooking_salad" in self.NAMESPACE["Persistent"].collected_foods:
                self.menu["???"] = "MGRoL"
                self.food["???"] = "MGRoL"

            next(self.lore)

        def set_choice(self, label):
            self.NAMESPACE["Define"].cooking_label = label
            self.NAMESPACE["Persistent"].collected_foods = self.NAMESPACE["Persistent"].collected_foods + [label]

            try:
                next(self.lore)
            except StopIteration:
                pass

        def show_menu(self, data) -> None:
            self.menu_manager.clear()
            self.menu_manager.enable()
            self.menu_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

            for name, state in self.food.items():
                print(name, state, data)
                _text = name
                if name in data:
                    _label = data[name]
                    state = True
                else:
                    _label = "bad_ending_golubi" # просто заглушка
                    state = False

                button = agui.UIFlatButton(text=_text, width=250, height=100, font_name=g.FONT_NAME, style=g.STYLE_DEFAULT_BUTTON)
                button.on_click = lambda event, label=_label: self.set_choice(label)
                if not state:
                    button.disabled = True
                self.menu_v_box.add(button)

            ui_anchor_layout = arcade.gui.widgets.layout.UIAnchorLayout()
            ui_anchor_layout.add(child=self.menu_v_box, anchor_x="center_x", anchor_y="center_y")

            self.menu_manager.add(ui_anchor_layout)

        def on_update(self, delta_time: float) -> None:
            super().on_update(delta_time)
            g.scene.update(delta_time)
            self.characters_texts_manager.update(delta_time)
            self.settings_manager.on_update(delta_time)
            self.menu_manager.on_update(delta_time)

        def on_draw(self) -> None:
            self.clear()
            g.scene.draw()
            arcade.draw_sprite(self.dialog_window)
            self.characters_texts_manager.draw()
            self.menu_manager.draw()
            self.settings_manager.draw()
            super().on_draw()

        def _lore(self):
            self.attributes.character_text = ["Что готовить будем?"]
            self.show_menu(self.menu,)
            yield
            self.window.show_view(self.window.GameView)

        def on_key_press(self, key: int, modifiers: int) -> bool | None:
            if key == arcade.key.S or key == arcade.key.ESCAPE:
                self.settings_manager.turn_visibl()

    class ShopCollecting(Main_template):
        def __init__(self):
            super().__init__()

            def return_back(event=None):
                if len(g.main.NAMESPACE["Define"].collected_items) > 0:
                    self.window.show_view(self.window.GameView)

            g.main.NAMESPACE["Define"].collected_items = {}

            #self.window.set_vsync(True)
            self.scene = g.scene
            self.actions = g.main.actions
            self.NAMESPACE = g.main.NAMESPACE
            self.fm = g.fm

            self.layers = []
            self.layers_sprite_list = SpriteList()
            self.layers.append({
                'sprite': g.scene.get_sprite("shop_shelf_bg_1.png"),
                'speed': 0.0,
                'original_x': self.width // 2,
                'original_y': self.height // 2
            })
            self.layers.append({
                'sprite': g.scene.get_sprite("shop_shelf_bg_1.png"),
                'speed': 0.15,
                'original_x': self.width // 2,
                'original_y': self.height // 2
            })
            self.layers.append({
                'sprite': g.scene.get_sprite("shop_shelf_bg_2.png"),
                'speed': 0.3,
                'original_x': self.width // 2,
                'original_y': self.height // 2
            })

            self.settings_manager = Managers.SettingsManager()
            self.settings_manager.enable()

            width = self.width
            height = self.height
            scene = g.scene
            items = [
                MovableBlockFalling(scene.get_texture("puki.png"), width * 0.1, height * 0.33),
                MovableBlockFalling(scene.get_texture("puki.png"), width * 0.12, height * 0.33),
                MovableBlockFalling(scene.get_texture("puki.png"), width * 0.14, height * 0.33),

                MovableBlockFalling(scene.get_texture("eggs.png"), width * 0.3, height * 0.28),
                MovableBlockFalling(scene.get_texture("eggs.png"), width * 0.32, height * 0.28),

                MovableBlockFalling(scene.get_texture("teramisu.png"), width * 0.48, height * 0.33, 0.8),
                MovableBlockFalling(scene.get_texture("teramisu.png"), width * 0.5, height * 0.33, 0.8),
                MovableBlockFalling(scene.get_texture("teramisu.png"), width * 0.52, height * 0.33, 0.8),

                MovableBlockFalling(scene.get_texture("pineapple.png"), width * 0.73, height * 0.30),

                MovableBlockFalling(scene.get_texture("tomatoes.png"), width * 0.1, height * 0.84, 0.8),
                MovableBlockFalling(scene.get_texture("tomatoes.png"), width * 0.15, height * 0.84, 0.8),
                MovableBlockFalling(scene.get_texture("tomatoes.png"), width * 0.2, height * 0.84, 0.8),
                MovableBlockFalling(scene.get_texture("tomatoes.png"), width * 0.25, height * 0.84, 0.8),

                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),
                MovableBlockFalling(scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8),

                MovableBlockFalling(scene.get_texture("cheremsha.png"), width * 0.55, height * 0.79),
                MovableBlockFalling(scene.get_texture("cheremsha.png"), width * 0.55, height * 0.79),
                MovableBlockFalling(scene.get_texture("cheremsha.png"), width * 0.55, height * 0.79),

                MovableBlockFalling(scene.get_texture("meat.png"), width * 0.7, height * 0.79),
                MovableBlockFalling(scene.get_texture("meat.png"), width * 0.7, height * 0.79),
                MovableBlockFalling(scene.get_texture("meat.png"), width * 0.7, height * 0.79),

                MovableBlockFalling(scene.get_texture("milk.png"), width * 0.91, height * 0.79),
                MovableBlockFalling(scene.get_texture("milk.png"), width * 0.91, height * 0.79)

            ]
            if random.random() > 0.95:
                items.append(MovableBlockFalling(scene.get_texture("penis.png"), width * 0.90, height * 0.30))
            else:
                items.append(MovableBlockFalling(scene.get_texture("penis_bread.png"), width * 0.93, height * 0.30))

            self.items_manager = arcade.SpriteList()
            random.shuffle(items)
            for i in items:
                self.layers.append(
                    {
                        'sprite': i,
                        'speed': 0.4,
                        'original_x': i.center_x,
                        'original_y': i.center_y
                    }
                )
                self.items_manager.append(i)
            for i in self.layers:
                self.layers_sprite_list.append(i['sprite'])


            self.on_mouse_motion(self.window._mouse_x, self.window._mouse_y, 0, 0)

            self.table = {
                "Boobles.png" : ("+ Лашчк",  (218, 148, 111)),
                "cheremsha.png": ("+ Черемша",  (149, 177, 125)),
                "crisps.png": ("+ Чипсеке",  (103, 82, 64)),
                "meat.png": ("+ Лисья печень",  (103, 82, 64)),
                "milk.png": ("+ Молочк Эпштейна",  (189, 192, 212)),
                "penis.png": ("+ Дидлок",  (159, 100, 118)),
                "penis_bread.png": ("+ Хлеб 100%",  (199, 189, 181)),
                "pineapple.png": ("+ Дикий ананас",  (210, 184, 138)),
                "puki.png": ("+ Пуки",  (240, 234, 203)),
                "cheese.png": ("+ Козий сыр",  (240, 200, 100)),
                "tomatoes.png": ("+ Помидоры Скидка 15%! 1+1=3! Только сегодня по новой скидке. Действует до 24.09.2077г! Приведите друга и получите 1488 козьих сыров по ссылке https://www.youtube.com/watch?v=dQw4w9WgXcQ", (255, 99, 71)),
                "teramisu.png": ("+ Терамису", (131, 91, 58)),
                "eggs.png": ("+ Яйца мамонта", (31, 206, 203))

            }

            self.notifiers = []


            self.return_button = agui.UIFlatButton(text="Продолжить", x=self.width*0.90, y=self.height*0.05, style=g.STYLE_DEFAULT_BUTTON, width=200)
            self.return_button.on_click = return_back
            self.return_button_manager = agui.UIManager()
            self.return_button_manager.add(self.return_button)
            self.return_button_manager.enable()


        def on_draw(self) -> None:
            self.clear()
            self.scene.draw()
            self.layers_sprite_list.draw()
            for i in self.notifiers:
                if i.visible:
                    i.draw()
            self.return_button_manager.draw()
            self.settings_manager.draw()

            super().on_draw()

        def plus_item(self, name):
            if name in self.NAMESPACE["Define"].collected_items:
                self.NAMESPACE["Define"].collected_items[name] += 1
            else:
                self.NAMESPACE["Define"].collected_items[name] = 1

        def on_update(self, delta_time: float) -> None:
            super().on_update(delta_time)
            self.scene.update(delta_time)
            #if len(list(self.return_button_manager.get_widgets_at((self.window._mouse_x, self.window._mouse_y)))) == 0:
            self.items_manager.update(delta_time, self.window.mouse.data)
            for i in self.notifiers:
                i.update(delta_time)

            for e, i in enumerate(self.items_manager):
                if i.clicked:
                    self.items_manager.append(self.items_manager.pop(e))

                if i.center_y < -30:
                    self.plus_item(i.texture.file_path.name)
                    print(self.NAMESPACE["Define"].collected_items)
                    text_data = self.table[i.texture.file_path.name]
                    text: arcade.Text = ItemsNotifText(text_data[0], i.center_x, i.center_y, text_data[1], g.FONT_NAME)
                    self.notifiers.append(text)
                    self.items_manager.remove(i)
                    i.kill()
                    del i

        def on_key_press(self, key: int, modifiers: int) -> bool | None:
            if key == arcade.key.S or key == arcade.key.ESCAPE:
                self.settings_manager.turn_visibl()

        def _move_parallax(self,layer, x, y):
            normalized_x = (x - self.width // 2) / (self.width // 2)
            normalized_y = (y - self.height // 2) / (self.height // 2)

            max_offset_x = 100 * layer['speed']
            max_offset_y = 60 * layer['speed']

            layer['sprite'].center_x = layer['original_x'] + normalized_x * max_offset_x
            layer['sprite'].center_y = layer['original_y'] + normalized_y * max_offset_y

        def on_mouse_motion(self, x, y, dx, dy):

            for e, layer in enumerate(self.layers):
                if hasattr(layer['sprite'], "freeze"):
                    if layer['sprite'].freeze:
                        self._move_parallax(layer, x, y)
                    else:
                        self.layers.append(self.layers.pop(e))
                else:
                    self._move_parallax(layer, x, y)

                if layer['sprite'].center_y < -30:
                    self.layers.remove(layer)

    class CTW(Main_template):
        def __init__(self):
            super().__init__()

            #self.window.set_vsync(True)
            self.scene = g.scene
            self.actions = g.main.actions
            self.NAMESPACE = g.main.NAMESPACE
            self.fm = g.fm

            self.settings_manager = Managers.SettingsManager()
            self.settings_manager.enable()

            self.sprites = [self.scene.get_sprite("golub.png"), self.scene.get_sprite("golub_click.png")]
            for i in self.sprites:
                i.center_x = self.center_x
                i.center_y = self.center_y
                i.width = self.width
                i.height = self.height

            self.draw_sprite = self.sprites[0]

            self.clicks = 1
            self.max_clicks = 42

            self.click_text = arcade.Text(
                f"0 / {self.max_clicks}", 0, 0, arcade.color.BLACK, 54
            )
            self.click_text.x = self.window.width * 0.02
            self.click_text.y = self.window.height * 0.95
            self.length = 10

            self.timer = time.time()


        def on_draw(self) -> None:
            self.clear()
            self.scene.draw()
            arcade.draw_sprite(self.draw_sprite)
            self.click_text.draw()
            arcade.draw_lrbt_rectangle_filled(self.width*0.2, self.width*0.8, self.height * 0.85, self.height * 0.95, (0,0,0,120))
            arcade.draw_lrbt_rectangle_filled(self.width * 0.21, self.width * 0.79, self.height * 0.87, self.height * 0.93, (0, 0, 0, 255))
            try:
                arcade.draw_lrbt_rectangle_filled(self.width * 0.21, (self.width * 0.79) * self.length/10, self.height * 0.87, self.height * 0.93, (255, 255, 255, 255))
            except ValueError:
                pass

            self.settings_manager.draw()

            super().on_draw()

        def on_key_press(self, key: int, modifiers: int) -> bool | None:
            if key == arcade.key.S or key == arcade.key.ESCAPE:
                self.settings_manager.turn_visibl()
            if key == arcade.key.SPACE:
                self.draw_sprite = self.sprites[1]
                self.clicks += 1
                self.click_text.text = f"{self.clicks} / {self.max_clicks}"

        def on_key_release(self, symbol: int, modifiers: int) -> bool | None:
            if symbol == arcade.key.SPACE:
                self.draw_sprite = self.sprites[0]

        def on_update(self, delta_time: float) -> None:
            if self.clicks >= self.max_clicks+1:
                print(self.clicks, self.max_clicks)
                self.window.show_view(self.window.GameView)

            if time.time() - self.timer >= 1:
                self.timer = time.time()
                self.length -= 1

            if self.length <= 0:
                self.NAMESPACE["Lore"].jump("bad_ending_golubi")
                self.window.show_view(self.window.GameView)

    class ShopGetting(Main_template):
        def __init__(self):
            super().__init__()


            def return_back(event=None):
                self.window.show_view(self.window.GameView)

            #self.window.set_vsync(True)
            self.scene = g.scene
            self.actions = g.main.actions
            self.NAMESPACE = g.main.NAMESPACE
            self.fm = g.fm

            self.layers = []
            scene = g.scene
            self.layers.append({
                'sprite': scene.get_sprite("background_ponn.png"),
                'speed': 0.0,
                'original_x': self.width // 2,
                'original_y': self.height // 2
            })
            self.layers.append({
                'sprite': scene.get_sprite("background_ponn.png"),
                'speed': 0.1,
                'original_x': self.width // 2,
                'original_y': self.height // 2
            })
            self.layers.append({
                'sprite': scene.get_sprite("background_ponnaqua.png"),
                'speed': 0.15,
                'original_x': self.width // 2,
                'original_y': self.height // 2
            })
            koshel = scene.get_sprite("koshel.png")
            koshel.scale = 2.0
            self.layers.append({
                'sprite': scene.get_sprite("koshel.png"),
                'speed': 0.2,
                'original_x': self.width * 0.2,
                'original_y': self.height * 0.2
            })

            self.settings_manager = Managers.SettingsManager()
            self.settings_manager.enable()

            self.collecting_zone = (self.width * 0.5, self.width * 0.97, self.height * 0.5, self.height * 0.97)

            self.table = {
                "money_two.png" : 2,
                "money_three.png" : 3,
                "money_five.png" : 5,
                "money_seven.png" : 7,
                "money_wth_pon_zalupkin.png" : 0,
                "money_wth.png" : 0
            }


            width = self.width
            height = self.height
            items = [
                MovableBlock(scene.get_texture("money_two.png"), width * 0.25, height * 0.2, 100, 0.6, self.collecting_zone, True),
                MovableBlock(scene.get_texture("money_two.png"), width * 0.25, height * 0.2, 100, 0.6,  self.collecting_zone, True),
                MovableBlock(scene.get_texture("money_two.png"), width * 0.25, height * 0.2, 100, 0.6, self.collecting_zone, True),
                MovableBlock(scene.get_texture("money_two.png"), width * 0.25, height * 0.2, 100, 0.6, self.collecting_zone, True),

                MovableBlock(scene.get_texture("money_three.png"), width * 0.38, height * 0.2, 100, 0.6, self.collecting_zone, True),
                MovableBlock(scene.get_texture("money_three.png"), width * 0.38, height * 0.2, 100, 0.6, self.collecting_zone, True),

                MovableBlock(scene.get_texture("money_wth_pon_zalupkin.png"), width * 0.51, height * 0.2, 100, 0.6, self.collecting_zone),
                MovableBlock(scene.get_texture("money_five.png"), width * 0.51, height * 0.2, 100, 0.6, self.collecting_zone, True),
                MovableBlock(scene.get_texture("money_five.png"), width * 0.51, height * 0.2, 100, 0.6, self.collecting_zone, True),
                MovableBlock(scene.get_texture("money_five.png"), width * 0.51, height * 0.2, 100, 0.6, self.collecting_zone, True),
                MovableBlock(scene.get_texture("money_five.png"), width * 0.51, height * 0.2, 100, 0.6, self.collecting_zone, True),

                ClickableSprite([scene.get_texture("money_wth.png"), scene.get_texture("money_wth_clicked.png")], width * 0.64, height * 0.2, 100, 0.6),
                MovableBlock(scene.get_texture("money_seven.png"), width * 0.64, height * 0.2, 100, 0.6, self.collecting_zone, True),
                MovableBlock(scene.get_texture("money_seven.png"), width * 0.64, height * 0.2, 100, 0.6, self.collecting_zone, True),
                MovableBlock(scene.get_texture("money_seven.png"), width * 0.64, height * 0.2, 100, 0.6, self.collecting_zone, True),
                MovableBlock(scene.get_texture("money_seven.png"), width * 0.64, height * 0.2, 100, 0.6, self.collecting_zone, True)
            ]
            coins = [
                (2, 3),  # 3 монеты по 2
                (3, 2),  # 2 монеты по 3
                (5, 4),  # 2 монеты по 5
                (7, 4),  # 4 монеты по 7
            ]

            self.items_manager = SpriteList()
            for i in items:
                self.layers.append(
                    {
                        'sprite': i,
                        'speed': 0.3,
                        'original_x': i.center_x,
                        'original_y': i.center_y,
                        "collected" : False
                    }
                )
                self.items_manager.append(i)

            self.on_mouse_motion(self.window._mouse_x, self.window._mouse_y, 0, 0)

            self.NAMESPACE["Define"].should_money = random.choice(self.find_reachable_sums(coins))
            self.NAMESPACE["Define"].got_money = 0

            self.return_button = agui.UIFlatButton(text="Продолжить", x=self.width*0.90, y=self.height*0.05, style=g.STYLE_DEFAULT_BUTTON, width=200)
            self.return_button.on_click = return_back
            self.return_button_manager = agui.UIManager()
            self.return_button_manager.add(self.return_button)
            self.return_button_manager.enable()

            self.should_money_manager = agui.UIManager()
            self.should_money_text = agui.UILabel(f"Внешний долг ЖАКЛИН:", font_name=g.FONT_NAME, font_size=40, bold=True, text_color=arcade.color.BLACK)

            if str(self.NAMESPACE["Define"].should_money)[-1] == "1" and  str(self.NAMESPACE["Define"].should_money)[-2:] != "11":
                text = f"{self.NAMESPACE["Define"].should_money} Кувейтский динар"
            else:
                text = f"{self.NAMESPACE["Define"].should_money} Кувейтских динаров"

            self.should_money_counter = agui.UILabel(text, font_name=g.FONT_NAME, font_size=40, text_color=arcade.color.SCARLET)
            self.should_money_box = agui.UIBoxLayout(align="left", x=self.width*0.01, y=self.height*0.8)
            self.should_money_box.with_background(color=(255, 255, 255, 200))

            self.should_money_box.add(self.should_money_text)
            self.should_money_box.add(self.should_money_counter)
            self.should_money_manager.add(self.should_money_box)

        def find_reachable_sums(self, coins, max_sum=None, min_sum=30):
            if max_sum is None:
                max_sum = sum(value * count for value, count in coins)

            if min_sum > max_sum:
                return tuple()

            bits = 1

            for value, count in coins:
                mask = 0
                for k in range(count + 1):
                    mask |= (bits << (k * value))

                bits = mask & ((1 << (max_sum + 1)) - 1)

            reachable = []
            for s in range(min_sum, max_sum + 1):
                if (bits >> s) & 1:
                    reachable.append(s)

            return tuple(reachable)

        def on_draw(self) -> None:
            self.clear()
            self.scene.draw()
            for layer in self.layers[:4]:
                arcade.draw_sprite(layer['sprite'])

            arcade.draw_lrbt_rectangle_filled(
                self.collecting_zone[0],
                self.collecting_zone[1],
                self.collecting_zone[2],
                self.collecting_zone[3],
                (0, 0, 0, 125)
            )

            for layer in self.layers[3:]:
                arcade.draw_sprite(layer['sprite'])
            self.should_money_manager.draw()
            self.return_button_manager.draw()
            self.settings_manager.draw()

            super().on_draw()

        def on_update(self, delta_time: float) -> None:
            super().on_update(delta_time)
            self.scene.update(delta_time)
            if len(list(self.return_button_manager.get_widgets_at((self.window._mouse_x, self.window._mouse_y)))) == 0:
                self.items_manager.update(delta_time, self.window.mouse.data)

            for e, i in enumerate(self.items_manager):
                if i.clicked:
                    self.items_manager.append(self.items_manager.pop(e))

            for e, layer in enumerate(self.layers):
                if layer['speed'] != 0.0:
                    if hasattr(layer['sprite'], "clicked"):
                        if layer['sprite'].clicked:
                            self.layers[e]['original_x'] = layer['sprite'].center_x
                            self.layers[e]['original_y'] = layer['sprite'].center_y

                    if hasattr(layer['sprite'], "freezed"):
                        if layer['sprite'].freezed:
                            if not self.layers[e]["collected"]:
                                self.NAMESPACE["Define"].got_money += self.table[layer['sprite'].texture.file_path.name]

                            self.layers[e]["collected"] = True
                        else:
                            if self.layers[e]["collected"]:
                                self.NAMESPACE["Define"].got_money -= self.table[layer['sprite'].texture.file_path.name]
                            self.layers[e]["collected"] = False



        def on_key_press(self, key: int, modifiers: int) -> bool | None:
            if key == arcade.key.S or key == arcade.key.ESCAPE:
                self.settings_manager.turn_visibl()

        def _move_parallax(self, layer, x, y):
            normalized_x = (x - self.width // 2) / (self.width // 2)
            normalized_y = (y - self.height // 2) / (self.height // 2)

            max_offset_x = 100 * layer['speed']
            max_offset_y = 60 * layer['speed']

            layer['sprite'].center_x = layer['original_x'] + normalized_x * max_offset_x
            layer['sprite'].center_y = layer['original_y'] + normalized_y * max_offset_y

        def on_mouse_motion(self, x, y, dx, dy):

            for e, layer in enumerate(self.layers):
                if hasattr(layer['sprite'], "clicked"):
                    if not layer['sprite'].clicked:
                        if hasattr(layer['sprite'], "freezed"):
                            if not layer['sprite'].freezed:
                                self._move_parallax(layer, x, y)
                        else:
                            self._move_parallax(layer, x, y)
                    else:
                        self.layers[e]['original_x'] = layer['sprite'].center_x
                        self.layers[e]['original_y'] = layer['sprite'].center_y
                        self.layers.append(self.layers.pop(e))

                else:
                    self._move_parallax(layer, x, y)


def init_file() -> None:
    """
    Инициализирует основные классы
    """

    timee = time.time()
    print("Saves...")
    g.sm = Saves_manager()
    print("files_manager...")
    g.fm = FilesManager()
    g.fm.load_assets(os.listdir("./game/images/moving_shop_assets"), "movable_shop_assets")
    g.fm.load_assets(os.listdir("./game/images/bying_shop_assets"), "movable_shop_assets_bying")
    g.fm.load_assets(["box_office_3.png"], "movable_shop_assets_bying")
    g.fm.load_assets(["golub_click.png", "golub.png"], "CTW")
    print("Audio manager...")
    g.am = AudioManager()
    print("Scene...")
    g.scene = Scene()
    print("Lore...")
    g.wwl = Wwl()
    print("Discord...")
    g.da = Discord_act()

    print("Characters...")
    g.attributes = Attributes()
    g.ListCharacters = ListCharacters()
    print(f"Init done for {round(time.time() - timee, 2)}s")
