import threading
import arcade
from pyglet.event import EVENT_HANDLE_STATE
from pyglet.graphics import Batch
import arcade.gui as agui
import arcade.gui.widgets.layout
from typing import Optional, Literal, Tuple, Union
import time
import re
import os
import random
import json
import uuid
from .gui import UISliderVertical, Managers, UISliderSavesUpdater
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

            self.in_game_manager = Managers.InGameManager(FONT_NAME, self.window)
            self.in_game_manager.settings_button.on_click = self.settings_manager.turn_visibl
            self.in_game_manager.return_button.on_click = self.LoreLogger.return_back
            self.in_game_manager.enable()

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
                        if time.time() - self.last_text_skip < 0.01:
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
            
            super().on_update(delta_time)

        def on_key_press(self, key, modifiers) -> None:
            if (key == arcade.key.SPACE or key == arcade.key.ENTER) and not self.settings_manager.waiting_settings:
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
                self.why.alpha = 255
                self.is_loading  = True

        def show_main_windows(self) -> None:

            def create_menu_buttons():

                def start_game(event=None):
                    self.window.set_fullscreen(False)
                    self.window.size = (1920, 1080)
                    self.window.set_fullscreen(True)
                    self.manager.disable()
                    game = Views.GameView()
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
                    width=self.window.width,
                    y=self.window.height * 0.7,
                    font_size=70
                )
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
                ui_anchor_layout.add(child=self.v_box, anchor_x="center_x", anchor_y="center_y")

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
                FPS_check_box.on_click = lambda event=None: sm.Volume.set_other("show_fps", not sm.Volume.get_other("show_fps"))
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



def init_file() -> None:
    """
    Инициализирует основные классы
    """
    global sm, am, da, wwl, scene, fm

    timee = time.time()
    print("files_manager...")
    fm = FilesManager()
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
