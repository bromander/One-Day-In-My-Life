import threading
import arcade
from arcade import SpriteList
from pyglet.event import EVENT_HANDLE_STATE
from pyglet.graphics import Batch
import arcade.gui as agui
import arcade.gui.widgets.layout
from typing import Optional, Literal, Tuple, Union
import time
import pyglet
import ctypes
from ctypes import wintypes
import re
import os
import random
import json
import uuid
from .gui import UISliderVertical, Managers, UISliderSavesUpdater, MovableBlock, MovableBlockFalling, ItemsNotifText
from .scene import Scene
from .lore_viewer import Wwl, LoreLogger
from .waiter import Waiter
from .saves import Saves_manager
from .namespace import Namespace
from .actions import Actions
from .audio import AudioManager
from .presence import Discord_act
from .files_manager import FilesManager
from .character import ListCharacters

arcade.load_font("game/fonts/Kurale-Regular.ttf")

FONT_NAME = "Kurale"
STYLE_DEFAULT_BUTTON = {
    "normal": arcade.gui.UIFlatButton.UIStyle(
        font_size=16,
        font_name=(FONT_NAME, ),
        font_color=arcade.color.WHITE,
        bg=(44, 62, 80)
    ),
    "hover": arcade.gui.UIFlatButton.UIStyle(
        font_size=16,
        font_name=(FONT_NAME, ),
        font_color=arcade.color.LIGHT_SKY_BLUE,
        bg=(24, 37, 49)
    ),
    "press": arcade.gui.UIFlatButton.UIStyle(
        font_size=16,
        font_name=(FONT_NAME, ),
        font_color=arcade.color.LIGHT_STEEL_BLUE,
        bg=(44, 62, 80)
    ),
    "disabled" : arcade.gui.UIFlatButton.UIStyle(
        font_size=16,
        font_name=(FONT_NAME, ),
        font_color=arcade.color.LIGHT_STEEL_BLUE,
        bg=(66, 71, 77)
    )
}


wait_trigger = Waiter()

GAME_NAME = ""

class Views:

    class MainWindow(arcade.Window):
        def __init__(self, width, height, title, resizable):
            super().__init__(width=width, height=height, title=title, resizable=resizable)
            self.GameView: Optional[Views.GameView] = None

        def on_close(self) -> None:
            try:
                da.stop_thread_flag = True
            except NameError:
                pass

            arcade.close_window()

        def on_activate(self) -> EVENT_HANDLE_STATE:
            try:
                if am.music.paused:
                    am.music.resume()
                if am.sound.paused:
                    am.sound.resume()
                am.voice.fade_modifier = 1.0
            except NameError:
                pass

        def on_deactivate(self) -> EVENT_HANDLE_STATE:
            try:
                if not am.music.paused:
                    am.music.pause()
                if not am.sound.paused:
                    am.sound.pause()
                am.voice.fade_modifier = 0.0
            except NameError:
                pass

    class Main_template(arcade.View):
        def __init__(self) -> None:
            """
            Является "Шаблоном".
            Создаёт счётчик ФПС и отвечает за курсор
            """
            super().__init__()
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

        def on_update(self, delta_time: float) -> None:
            self.cursor_texture.position = (self.window._mouse_x, self.window._mouse_y)
            self.window.set_mouse_visible(False)

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


        def on_draw(self) -> None:
            arcade.draw_sprite(self.cursor_texture)
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

            self.window.set_vsync(True)

            self.delta_time = 0.0

            self.dialog_window: Optional[arcade.Sprite] = None

            self.scene = scene

            self.menu_manager = agui.UIManager()
            self.menu_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

            self.splash_manager = agui.UIManager()

            self.waiting_dialogue = Waiter(True)
            self.waiting_autoskip = Waiter(False)

            self.last_text_skip = time.time()

            self.last_text = " "

            self.lc = ListCharacters(sm, am, fm, wait_trigger)
            self.attributes = self.lc.attributes

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
                    font_name=FONT_NAME,
                    text_color=(255, 255, 255, 0),
                    font_size=72
                )
                text_small = agui.UILabel(
                    " ",
                    y=self.height * 0.77,
                    align="center",
                    width=self.width,
                    font_name=FONT_NAME,
                    text_color=(255, 255, 255, 0),
                    font_size=28
                )

                self.splash_manager.add(text)
                self.splash_manager.add(text_small)

            create_widgets()

            self.start_trigger: bool = True

            self.session_id = ""
            def load_saves(session_id):
                """
                Загружает сохранение
                """
                if session_id is None:
                    self.session_id = str(uuid.uuid4())
                else:
                    self.session_id = session_id
                    save = sm.Save.get_save(self.session_id)
                    wwl.label = save["label"]
                    wwl.pose = save["position"]
                    for i, o in save["defines"].items():
                        self.NAMESPACE["Define"].defines[i] = o

                    scene = save["scene"]

                    for i in scene["bg"]:
                        bg_sprite = arcade.Sprite(i["path"])
                        bg_sprite.size = tuple(i["size"])
                        bg_sprite.position = tuple(i["pos"])
                        self.scene.add_sprite("bg", i["layer"], bg_sprite)

                    for i in scene["sprites"]:
                        character_sprite = arcade.Sprite(i["path"])
                        character_sprite.size = tuple(i["size"])
                        character_sprite.position = tuple(i["pos"])
                        self.scene.add_sprite("sprites", i["id"], character_sprite)

                    if scene["music"] is not None:
                        am.play_music(scene["music"])
                    else:
                        am.stop_sound()
                        am.stop_music()

            load_saves(session_id)

            self.actions = Actions(self, sm)

            print(self.session_id)

            self.NAMESPACE = Namespace(self, Views, self.lc, wwl, am, wait_trigger, sm)

            self.settings_manager = Managers.SettingsManager(self, am, sm, wwl, self.session_id, FONT_NAME, STYLE_DEFAULT_BUTTON, Views)
            self.settings_manager.enable()

            self.characters_texts_manager = Managers.CharactersTextManager(self.attributes, self.window, FONT_NAME)
            self.characters_texts_manager.enable()

            self.LoreLogger = LoreLogger(self, wwl)

            self.in_game_manager = Managers.InGameManager(FONT_NAME, self.window, autoskip_waiter = self.waiting_autoskip)
            self.in_game_manager.settings_button.on_click = self.settings_manager.turn_visibl
            self.in_game_manager.return_button.on_click = self.LoreLogger.return_back
            self.in_game_manager.skip_button.on_click = lambda event=None: self.waiting_autoskip.switch()
            self.in_game_manager.enable()
            #self.in_game_manager.return_button.on_click = self.LoreLogger.return_back

            self.talk_manager(clicked=False)

        def chanel(self):
            da.stop_thread_flag = True
            time.sleep(0.05)

            self.actions.active_generators.clear()

            am.stop_sound()
            am.stop_music()
            am.stop_voice()

            self.window.set_fullscreen(False)
            self.window.size = (1024, 786)
            game = Views.GameMenu(show_lc=True)
            self.window.show_view(game)

        def talk_manager(self, pos_offset: Optional[int] = None, clicked: bool = True) -> None:
            """
            Получает инструкции сценария и запускает функцию talk(), обрабатывая её результаты
            """
            gens = self.actions.active_generators
            if gens.active_generators_consistently:
                if gens.active_generators_consistently[0][0] == 'talk':
                    while gens.active_generators_consistently[0][0] == "talk":
                        gens.update(1 / 1000)
                        if not gens.active_generators_consistently:
                            break
                    return

            gen = self.actions.active_generators.active_generators_consistently
            if gen:
                if clicked:
                    if gen[0][0] != 'talk':
                        return
                    else:
                        if time.time() - self.last_text_skip < 0.05:
                            return
                        else:
                            self.last_text_skip = time.time()

            now = wwl.get_thing(pos_offset)
            res = self.talk(now)
            self.start_trigger = False


            match res:
                case "NEXT":
                    self.talk_manager(clicked=False)
                case "REPEAT":
                    return None
                case "END":
                    return None
                case "END_text":
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
                        res = self.NAMESPACE.execute(now["data"])
                        res = res if res is not None else "NEXT"
                        return res

                    case "SHOW_SPLASH":
                        if now["data"]['show_splash']:
                            self.actions.start_action("show_splash", now["data"], "together")
                        da.update(now["data"]["name"], now["data"]["description"])
                        return "NEXT"

                    case _:
                        print(f"Неопознанная команда: {now}")
                        return "NEXT"

        def on_draw(self) -> None:
            if not self.start_trigger:
                self.clear()
                self.scene.draw()
                self.splash_manager.draw()
                arcade.draw_sprite(self.dialog_window)
                self.characters_texts_manager.draw()
                self.in_game_manager.draw()
                self.menu_manager.draw()
                self.settings_manager.draw()
            super().on_draw()

        def show_menu(self, data) -> None:
            global wait_trigger

            def jump(label: str):
                global wait_trigger
                wwl.pose = 0
                wwl.label = label
                self.menu_manager.clear()
                self.menu_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)
                wait_trigger.off()
                self.talk_manager()

            wait_trigger.on()

            for k, v in data.items():
                button = agui.UIFlatButton(
                    text=k,
                    width=200,
                    font_name=FONT_NAME,
                    style=STYLE_DEFAULT_BUTTON
                )
                button.on_click = lambda event, label=v: jump(label)
                self.menu_v_box.add(button)

            wait_trigger.on()

            ui_anchor_layout = arcade.gui.widgets.layout.UIAnchorLayout()
            ui_anchor_layout.add(child=self.menu_v_box, anchor_x="center_x", anchor_y="center_y")

            self.menu_manager.add(ui_anchor_layout)

        def on_update(self, delta_time) -> None:

            self.delta_time = delta_time

            self.scene.update()

            self.actions.update(delta_time)

            self.characters_texts_manager.update(delta_time)

            if self.waiting_autoskip:
                self.talk_manager(clicked=True)
            
            super().on_update(delta_time)

        def on_key_press(self, key, modifiers) -> None:
            if (key == arcade.key.SPACE or key == arcade.key.ENTER) and not self.settings_manager.waiting_settings:
                self.waiting_autoskip.off()
                self.talk_manager()
            if key == arcade.key.S or key == arcade.key.ESCAPE:
                self.settings_manager.turn_visibl()
            if key == arcade.key.B:
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
                if len(list(self.in_game_manager.get_widgets_at((x, y)))) == 1: # Проверяем, нажали ли мы на какую-нибудь кнопку.
                    self.waiting_autoskip.off()
                    self.talk_manager()

    class GameMenu(Main_template):
        def __init__(self, show_lc: bool = True) -> None:
            """
            Отвечает за главное меню игры
            :param show_lc: если True, отображает загрузочный экран и инициализирует основные класса
            """
            super().__init__()

            self.window.set_vsync(False)

            self.loading_screen = arcade.Sprite("game/images/gui/JE3000_logo-export.png", 1)
            self.loading_screen.position = (int(self.center_x), int(self.center_y))
            self.loading_screen_fade = arcade.Sprite("game/images/gui/blackscreen.png")
            self.loading_screen_fade.position = (int(self.center_x), int(self.center_y))
            self.loading_screen_fade.alpha = 0
            self.loading_screen_fade.size = (2500, 2500)
            self.loading_screen.alpha = 0

            self.manager = agui.UIManager()
            self.manager.disable()

            self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

            self.why = arcade.Sprite("game/images/gui/what_are_you_so_afraid_of.png", center_x=self.window.width / 2, center_y=self.window.height / 2)
            self.why.alpha = 0

            self.show_main_windows()
            self.is_loading = False
            self.is_mouse_pressed = False

            self.vokhanalia = False

            if show_lc:
                self.show_ls()

        def show_ls(self) -> None:
            """
            Отображает загрузочный экран
            """
            def loading(self):
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

            self.loading_screen.alpha = 255
            self.is_loading = True
            self.loading_generator = loading(self)

        def on_draw(self) -> None:
            self.clear()
            self.manager.draw()
            arcade.draw_sprite(self.loading_screen)
            arcade.draw_sprite(self.loading_screen_fade)
            arcade.draw_sprite(self.why)
            super().on_draw()

        def _start_vokhanalia(self):

            class Vokhanalia_view(arcade.View):

                def __init__(self, text):
                    super().__init__()

                    self.text = text

                    file = "./game/images/gui/767e4a851516f55e2471809744295141.jpg"
                    self.file = arcade.Sprite(file)
                    self.background_color = arcade.color.BLACK
                    self.lst = arcade.SpriteList()
                    self.window.center_window()

                    self.width_const, self.height_const =  self.width, self.height

                    self.talker = arcade.Text(
                        text.text,
                        self.window.width / 2, self.window.height / 2,
                        color=arcade.color.WHITE,
                        multiline=True,
                        width=self.window.width-100,
                        font_size=30,
                        anchor_x="center",
                        anchor_y="center",
                        align="center"
                    )
                    self.window.center_window()
                    self.last_update = time.time()
                    self.last_update_eye = time.time()

                def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
                    if button == 1:
                        self.text.next()


                def on_update(self, delta_time: float) -> bool | None:
                    if time.time() - self.last_update < 0.1:
                        return None

                    screen_width, screen_height = arcade.get_display_size()
                    window_width, window_height = self.window.get_framebuffer_size()
                    self.window.set_location(int((screen_width - window_width) * random.random()), int((screen_height - window_height) * random.random()))

                    self.window.width = self.width_const + random.randint(-50, 50)
                    self.window.height = self.height_const + random.randint(-50, 50)

                    self.last_update = time.time()

                    self.window.center_window()

                def on_draw(self) -> bool | None:
                    self.clear()
                    self.lst.clear()

                    self.talker.position = (
                    self.center_x + random.randint(-2, 2), self.center_y + random.randint(-2, 2))
                    self.talker.text = self.text.text

                    if time.time() - self.last_update_eye > 0.1:
                        for i in range(10):
                            self.last_update_eye = time.time()
                            file = arcade.Sprite(self.file.texture)

                            file.center_x = random.randint(0, self.window.width)
                            file.center_y = random.randint(0, self.window.height)
                            if random.random() >= 0.5:
                                file.scale_x = random.random() * random.randint(1, 30)/10
                            else:
                                file.scale_y = random.random() * random.randint(1, 30)/10
                            self.lst.append(file)



                    self.lst.draw()
                    self.talker.draw()

            def vokhanalia():
                self.window.set_visible(False)
                am.play_music("game/music/Lucid Blocks OST： Corner.mp3", streaming=True)

                class VokhanaliaText():
                    def __init__(self):
                        def gen():
                            with open("./game/other/thinking.json", "r", encoding="UTF-8") as f:
                                f = json.load(f)
                            for i in f:
                                self.text = i
                                yield
                            arcade.exit()

                        self.text = "..."
                        self.gen = gen()

                    def next(self):
                        next(self.gen)

                text = VokhanaliaText()
                self.VokhanaliaText = text
                self.vokhanalia = True

                for  i in range(2):
                    window = arcade.open_window(1000, 600, window_title="Почему?", resizable=False, style="borderless")
                    window.center_window()
                    view = Vokhanalia_view(text)
                    window.show_view(view)

            self.loading_generator = vokhanalia()


        def on_update(self, delta_time) -> None:
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

        def show_main_windows(self) -> None:

            def create_menu_buttons():

                def start_game(event=None):
                    self.window.set_fullscreen(False)
                    self.window.size = (1920, 1080)
                    self.window.set_fullscreen(True)
                    self.manager.disable()
                    class pon:
                        def __init__(self):
                            pass
                    game = Views.GameView()
                    self.window.GameView = game
                    self.window.show_view(game)

                def open_saves(event=None):
                    settings = Views.SaveMenu()
                    self.window.show_view(settings)

                def open_settings(event=None):
                    settings = Views.SettingsMenu()
                    self.window.show_view(settings)

                main_lebel = agui.UILabel(
                    GAME_NAME,
                    text_color=arcade.color.MIDNIGHT_BLUE,
                    font_name=FONT_NAME,
                    align="center",
                    width=self.window.width*0.9,
                    multiline=True,
                    font_size=40
                )
                main_lebel.center_y = self.height * 0.7
                main_lebel.center_x = self.width * 0.5
                self.manager.add(main_lebel)

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

                ui_anchor_layout = arcade.gui.widgets.layout.UIAnchorLayout()
                ui_anchor_layout.add(child=self.v_box)
                ui_anchor_layout.center_y = self.window.height * -0.2

                self.manager.add(ui_anchor_layout)

            create_menu_buttons()

    class SaveMenu(Main_template):
        def __init__(self):
            """
            Отвечает за экран загрузки сохранений
            """
            super().__init__()

            saves = sm.Save.get_all_saves()
            self.saves = saves + [[None]]*(20 - len(saves))
            self.saves_len = 20

            self.slider: Optional[UISliderVertical]  = None

            self.manager = agui.UIManager()
            self.manager.enable()

            self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)
            self.v_box.center_x = self.window.width/2-300
            self.manager.add(self.v_box)

            self.choise = 0

            self.generate_buttons()

        def generate_buttons(self) -> None:

            def return_to_main_menu(event=None):
                am.stop_voice()
                am.stop_sound()
                am.stop_music()
                game = Views.GameMenu(False)
                self.window.show_view(game)

            def open_save(session_id: str, event=None):
                self.window.set_fullscreen(False)
                self.window.size = (1920, 1080)
                self.window.set_fullscreen(True)
                self.manager.disable()
                game = Views.GameView(session_id)
                self.window.show_view(game)

            return_button = agui.UIFlatButton(
                text="Назад",
                width=100,
                height=50,
                style=STYLE_DEFAULT_BUTTON,
                x=10,
                y=self.window.height-65
            )
            return_button.on_click = return_to_main_menu
            self.manager.add(return_button)

            for i in self.saves:

                button = agui.UIFlatButton(text=f"{i[0]} <", width=700, height=200, style=STYLE_DEFAULT_BUTTON)

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

            #self.v_box.center_y = ((self.v_box.children[0].height + self.v_box._space_between) * 2) - (self.v_box.children[0].height + self.v_box._space_between) * (self.saves_len - self.slider.value)


        def on_draw(self) -> bool | None:
            self.clear()
            self.manager.draw()
            super().on_draw()

        def on_update(self, delta_time: float) -> bool | None:
            self.v_box.center_y = self.center_y - ((self.saves_len - self.slider.value) * 220 + 100) + (220 * 10)
            self.choise = int(self.slider.value-1)

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

            self.show_main_windows()

        def on_draw(self) -> None:
            self.clear()
            self.manager.draw()
            super().on_draw()

        def on_update(self, delta_time: float) -> bool | None:
            super().on_update(delta_time)

        def show_main_windows(self) -> None:

            def create_menu_buttons():
                with open("game/saves.JSON", "r", encoding="UTF-8") as data:
                    data = json.load(data)
                volumes = data['options']

                def return_to_main_menu(event=None):
                    am.stop_voice()
                    am.stop_sound()
                    am.stop_music()
                    game = Views.GameMenu(False)
                    self.window.show_view(game)

                def show_fps(event=None):
                    sm.Volume.set_other("show_fps", not sm.Volume.get_other("show_fps"))
                    sm.Volume._save_data()


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

            create_menu_buttons()


    class ShopCollecting(Main_template):
        def __init__(self, session_id: str, NAMESPACE, actions):
            super().__init__()


            def return_back(event=None):
                self.window.show_view(self.window.GameView)

            NAMESPACE.Define.collected_items = {}

            self.window.set_vsync(True)
            self.scene = scene
            self.actions = actions
            self.NAMESPACE = NAMESPACE

            self.layers = []
            self.layers.append({
                'sprite': scene.get_sprite("shop_shelf_bg_1.png"),
                'speed': 0.0,
                'original_x': self.width // 2,
                'original_y': self.height // 2
            })
            self.layers.append({
                'sprite': scene.get_sprite("shop_shelf_bg_1.png"),
                'speed': 0.15,
                'original_x': self.width // 2,
                'original_y': self.height // 2
            })
            self.layers.append({
                'sprite': scene.get_sprite("shop_shelf_bg_2.png"),
                'speed': 0.3,
                'original_x': self.width // 2,
                'original_y': self.height // 2
            })

            self.settings_manager = Managers.SettingsManager(self, am, sm, wwl, session_id, FONT_NAME, STYLE_DEFAULT_BUTTON, Views)
            self.settings_manager.enable()

            width = self.width
            height = self.height
            items = [
                MovableBlockFalling(scene.get_texture("Boobles.png"), width * 0.1, height * 0.33),
                MovableBlockFalling(scene.get_texture("Boobles.png"), width * 0.15, height * 0.33),
                MovableBlockFalling(scene.get_texture("Boobles.png"), width * 0.2, height * 0.33),
                MovableBlockFalling(scene.get_texture("Boobles.png"), width * 0.25, height * 0.33),
                MovableBlockFalling(scene.get_texture("Boobles.png"), width * 0.3, height * 0.33),

                MovableBlockFalling(scene.get_texture("crisps.png"), width * 0.48, height * 0.33),
                MovableBlockFalling(scene.get_texture("crisps.png"), width * 0.45, height * 0.33),
                MovableBlockFalling(scene.get_texture("crisps.png"), width * 0.5, height * 0.33),

                MovableBlockFalling(scene.get_texture("pineapple.png"), width * 0.73, height * 0.30),

                MovableBlockFalling(scene.get_texture("puki.png"), width * 0.1, height * 0.84),
                MovableBlockFalling(scene.get_texture("puki.png"), width * 0.15, height * 0.84),
                MovableBlockFalling(scene.get_texture("puki.png"), width * 0.2, height * 0.84),
                MovableBlockFalling(scene.get_texture("puki.png"), width * 0.25, height * 0.84),

                MovableBlockFalling(scene.get_texture("cheremsha.png"), width * 0.4, height * 0.79),
                MovableBlockFalling(scene.get_texture("cheremsha.png"), width * 0.4, height * 0.79),
                MovableBlockFalling(scene.get_texture("cheremsha.png"), width * 0.4, height * 0.79),

                MovableBlockFalling(scene.get_texture("cheremsha.png"), width * 0.55, height * 0.79),
                MovableBlockFalling(scene.get_texture("cheremsha.png"), width * 0.55, height * 0.79),
                MovableBlockFalling(scene.get_texture("cheremsha.png"), width * 0.55, height * 0.79),

                MovableBlockFalling(scene.get_texture("meat.png"), width * 0.7, height * 0.79),
                MovableBlockFalling(scene.get_texture("meat.png"), width * 0.7, height * 0.79),
                MovableBlockFalling(scene.get_texture("meat.png"), width * 0.7, height * 0.79),

                MovableBlockFalling(scene.get_texture("milk.png"), width * 0.91, height * 0.79),
                MovableBlockFalling(scene.get_texture("milk.png"), width * 0.91, height * 0.79)

            ]
            if random.random() > 0.9:
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
                "puki.png": ("+ Пуки",  (240, 234, 203))
            }

            self.notifiers = []


            self.return_button = agui.UIFlatButton(text="Продолжить", x=self.width*0.90, y=self.height*0.05, style=STYLE_DEFAULT_BUTTON, width=200)
            self.return_button.on_click = return_back
            self.return_button_manager = agui.UIManager()
            self.return_button_manager.add(self.return_button)
            self.return_button_manager.enable()


        def on_draw(self) -> None:
            self.clear()
            self.scene.draw()
            for layer in self.layers:
                arcade.draw_sprite(layer['sprite'])
            for i in self.notifiers:
                if i.visible:
                    i.draw()
            self.return_button_manager.draw()
            self.settings_manager.draw()

            super().on_draw()

        def plus_item(self, name):
            if name in self.NAMESPACE.Define.collected_items:
                self.NAMESPACE.Define.collected_items[name] += 1
            else:
                self.NAMESPACE.Define.collected_items[name] = 1

        def on_update(self, delta_time: float) -> None:
            super().on_update(delta_time)
            self.scene.update()
            if len(list(self.return_button_manager.get_widgets_at((self.window._mouse_x, self.window._mouse_y)))) == 0:
                self.items_manager.update(delta_time, self.window.mouse.data)
            for i in self.notifiers:
                i.update(delta_time)

            for e, i in enumerate(self.items_manager):
                if i.clicked:
                    self.items_manager.append(self.items_manager.pop(e))

                if i.center_y < -30:
                    self.plus_item(i.texture.file_path.name)
                    print(self.NAMESPACE.Define.collected_items)
                    text_data = self.table[i.texture.file_path.name]
                    text: arcade.Text = ItemsNotifText(text_data[0], i.center_x, i.center_y, text_data[1], FONT_NAME)
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



def init_file() -> None:
    """
    Инициализирует основные классы
    """
    global sm, am, da, wwl, scene, fm

    timee = time.time()
    print("files_manager...")
    fm = FilesManager()
    fm.load_assets(os.listdir("./game/images/moving_shop_assets"), "movable_shop_assets")
    print("Saves...")
    sm = Saves_manager()
    print("Audio manager...")
    am = AudioManager(sm, fm)
    print("Scene...")
    scene = Scene(fm)
    print("Lore...")
    wwl = Wwl(fm)
    print("Discord...")
    da = Discord_act()
    print(f"Init done for {round(time.time() - timee, 2)}s")
