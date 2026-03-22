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
from .gui import UISliderVertical, InGameSettings, UISliderSavesUpdater
from .scene import Scene
from .lore_viewer import Wwl
from .waiter import Waiter
from .saves import Saves_manager
from .namespace import Namespace
from .actions import Actions
from .audio import AudioManager
from .presence import Discord_act
from .files_manager import FilesManager

arcade.load_font("game/fonts/Kurale-Regular.ttf")



text_anchor = "left"

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

dialog_text_text: list[str] = []
cname_text_text = ""

cname_text_colour = arcade.color.BLACK
dialog_text_colour = arcade.color.BLACK

class Views:

    class MainWindow(arcade.Window):
        def __init__(self, width, height, title, resizable):
            super().__init__(width=width, height=height, title=title, resizable=resizable)

        def on_close(self) -> None:
            print("closing...")
            da.stop_thread_flag = True
            arcade.close_window()

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
            self.dialog_text_batch = Batch()
            self.dialog_texts: list = []
            self.cname_text: Optional[arcade.Text] = None

            self.scene = scene

            self.menu_manager = agui.UIManager()
            self.menu_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

            self.splash_manager = agui.UIManager()

            self.waiting_dialogue = Waiter(True)

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

            load_saves(session_id)

            self.actions = Actions(self, sm)

            print(self.session_id)

            self.NAMESPACE = Namespace(self, lc, wwl, am, wait_trigger, sm)

            self.talk_manager(clicked=False)

            self.settings_ui = InGameSettings(
                self.session_id,
                Views,
                self.scene,
                self.window,
                am, wwl, sm, self.NAMESPACE,
                FONT_NAME, STYLE_DEFAULT_BUTTON,
                self.actions
            )


        def chanel(self):
            am.stop_voice()
            am.stop_sound()
            am.stop_music()
            self.window.set_fullscreen(False)
            self.window.size = (1024, 786)
            game = Views.GameMenu(False)
            self.window.show_view(game)

        def talk_manager(self, pos_offset: Optional[int] = None, clicked: bool = True) -> None:
            """
            Получает инструкции сценария и запускает функцию talk(), обрабатывая её результаты
            """

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
                    return None

        def talk(self, now) -> str:
            """
            Запускает основные действия сценария
            :param now:
            :return:
            """
            global dialog_text_text, cname_text_text
            global cname_text_colour, dialog_text_colour
            global text_anchor
            global wait_trigger

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
                self.update_main_windows()
                self.dialog_text_batch.draw()
                self.menu_manager.draw()
                self.settings_ui.draw()
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

            self.settings_ui.update()
            
            super().on_update(delta_time)

        def on_key_press(self, key, modifiers) -> None:
            if (key == arcade.key.SPACE or key == arcade.key.ENTER or key == arcade.key.ENTER) and not self.settings_ui.waiting_settings:
                self.talk_manager()
            if key == arcade.key.S:
                self.settings_ui.turn_visibl()
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
            if (int(button) == 1) and not self.settings_ui.waiting_settings:
                self.talk_manager()

        def update_main_windows(self) -> None:

            def create_dialog_text():

                def split_by_length(text, max_length):
                    if len(text) <= max_length:
                        return [text]

                    parts = []
                    words = text.split(" ")
                    current_line = []

                    for word in words:
                        if len(word) > max_length:
                            if current_line:
                                parts.append(" ".join(current_line))
                                current_line = []

                            for i in range(0, len(word), max_length):
                                parts.append(word[i:i + max_length])
                        else:
                            test_line = " ".join(current_line + [word])
                            if len(test_line) <= max_length:
                                current_line.append(word)
                            else:
                                if current_line:
                                    parts.append(" ".join(current_line))
                                current_line = [word]

                    if current_line:
                        parts.append(" ".join(current_line))

                    return parts

                line_counter = 0

                self.dialog_text_batch = Batch()

                text_objects = []

                for i, line in enumerate(dialog_text_text):
                    split_lines = split_by_length(line, 60)

                    for sline in split_lines:
                        y_pos = (self.height * 0.2) - line_counter * 40

                        if text_anchor == "left":
                            x_pos = self.width * 0.18
                        elif text_anchor == "center":
                            x_pos = self.width // 2
                        elif text_anchor == "right":
                            x_pos = self.width * 0.82
                        elif type(text_anchor) is float:
                            x_pos = self.width * text_anchor
                        elif type(text_anchor) is int:
                            x_pos = int

                        t = arcade.Text(
                            text=sline,
                            x=x_pos,
                            y=y_pos,
                            font_size=30,
                            color=dialog_text_colour,
                            font_name=FONT_NAME,
                            anchor_x=text_anchor
                        )

                        text_objects.append(t)
                        line_counter += 1

                for text_obj in text_objects:
                    text_obj.draw()

            def create_cname_text():
                self.cname_text = arcade.Text(
                    cname_text_text,
                    x=self.width * 0.19,
                    y=self.height * 0.255,
                    font_size=40,
                    multiline=True,
                    width=1150,
                    color=cname_text_colour,
                    font_name=FONT_NAME
                )
                self.cname_text.draw()

            create_dialog_text()
            create_cname_text()

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



class Character:

    def __init__(self, name: str,
                 char_id: Optional[str] = None,
                 colour: str = "",
                 name_colour: str = "",
                 c_scale: float = 1.0,
                 text_anch: Tuple[int, float, Literal["left", "right", "center"]] = "left",
                 lps: int = 60) -> None:

        """
        Создаёт персонажа.
        :param name: Имя персонажа
        :param char_id: Айди персонажа (должно совпадать с его папкой, и названиями спрайтов)
        :param colour: Цвет текста речи (в HEX формате)
        :param name_colour: Цвет текста имени (в HEX формате)
        :param c_scale: Размер спрайта
        :param text_anch: Положение текста на экране (left, right, center)/ int - координата X / float - координата (width * text_anch)
        :param lps: Letters per frame: Скорость появления букв в секунду.
        """

        def hex_to_rgb(hex_color: str):
            if hex_color:
                hex_color = hex_color.lstrip("#")
                if len(hex_color) not in (6, 8):
                    raise ValueError("Hex должен быть в формате RRGGBB")

                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                if len(hex_color) == 8:
                    a = int(hex_color[6:8], 16)
                    return (r, g, b, a)
                return (r, g, b)
            else:
                return arcade.color.WHITE

        def find_sounds():
            sounds = []
            if self.char_id is not None:
                for f in os.listdir(f"./game/sounds/voice/{self.char_id}"):
                    if os.path.isfile(os.path.join(f"./game/sounds/voice/{self.char_id}", f)):
                        sounds.append(arcade.load_sound(f"./game/sounds/voice/{self.char_id}/{f}"))
            self.talk_sounds = sounds
            return sounds

        self.c_name = name
        self.colour = hex_to_rgb(colour)
        self.name_colour = hex_to_rgb(name_colour)
        self.c_scale = c_scale
        self.lps = lps
        self.action = None
        self.last_text = " "

        self.char_id = char_id

        self.talk_sounds = []

        threading.Thread(target=find_sounds).start()

        self.text_anch = text_anch

    def talk(self, text: str):
        """
        Форматирует текст и создаёт генератор, который проигрывает речь персонажа.
        :param text: Речь персонажа
        :return: Генератор
        """
        global dialog_text_colour, cname_text_colour
        global dialog_text_text, cname_text_text
        global text_anchor

        def replace_char_by_index(text, index, new_char):
            if index < 0 or index >= len(text):
                return text
            return text[:index] + new_char + text[index + 1:]

        now_lps = self.lps * (self.lps / sm.Volume.get_other("lps"))

        dialog_text_text_alt = [" "]
        string_index_alt = 0
        _text_alt = []
        for char in re.findall(r'\\n |\{[^}]*\}|\S|\s', repr(text).strip(r"'")):

            char = str(char)

            if char == r"\n ":
                string_index_alt += 1
                _text_alt = []
                continue

            if not char.startswith("{") and not str(char).endswith("}"):
                if char != r"\n ":
                    if char != " ":
                        _text_alt.append(" ")
                    else:
                        _text_alt.append(" ")
                    if len(dialog_text_text_alt)-1 != string_index_alt:
                        dialog_text_text_alt.insert(string_index_alt, "".join(_text_alt))
                    else:
                        dialog_text_text_alt[string_index_alt] = "".join(_text_alt)


        text_anchor = self.text_anch

        am.stop_voice()

        dialog_text_colour = self.colour
        cname_text_colour = self.name_colour

        self.action = None

        dialog_text_text = dialog_text_text_alt.copy()
        cname_text_text = ""

        def _talk(now_lps):
            global dialog_text_text, cname_text_text
            string_index = 0
            fast = False

            self.action = "talk"

            while True:
                i = -1
                if not wait_trigger:
                    self.last_text = text

                    _text = []
                    index = 0
                    for char in re.findall(r'\\n |\{[^}]*\}|\S|\s', repr(text).strip(r"'")):
                        i += 1
                        char = str(char)

                        if char == r"\n ":
                            string_index += 1
                            i = -1
                            _text = []
                            continue

                        cname_text_text = self.c_name

                        if not char.startswith("{") and not str(char).endswith("}"):
                            if char != r"\n ":
                                _text.append(char)
                                dialog_text_text[string_index] = replace_char_by_index(dialog_text_text[string_index], i, char)

                        index += 1

                        if ((index % 4 == 0 and char not in (",", ".", "!", "&", "?")) or index == 1) and self.char_id is not None:
                            if os.path.isdir(f"./game/sounds/voice/{self.char_id}"):
                                am.play_voice(random.choice(self.talk_sounds))

                        if char == ".":
                            if not fast:
                                remaining_time = 0.1
                                while remaining_time > 0:
                                    dt = yield

                                    if dt is None or dt <= 0:
                                        continue

                                    remaining_time -= dt

                        elif char == ",":
                            if not fast:
                                remaining_time = 0.05
                                while remaining_time > 0:
                                    dt = yield
                                    if dt is None or dt <= 0:
                                        continue
                                    remaining_time -= dt

                        elif char.startswith("{") and str(char).endswith("}"):
                            char = char[1:][:-1]

                            if char.startswith("w"):
                                i -= 1

                                remaining_time = float(char.split("=")[-1])
                                while remaining_time > 0:
                                    dt = yield
                                    if dt is None or dt <= 0:
                                        continue
                                    remaining_time -= dt

                            dt = yield
                            if char.startswith("f"):
                                i -= 1
                                fast = True

                        if not fast:
                            remaining_time = 1 / now_lps
                            while remaining_time > 0:
                                dt = yield
                                if dt is None or dt <= 0:
                                    continue
                                remaining_time -= dt

                    self.action = None
                    return None
                else:
                    if not fast:
                        remaining_time = 1 / now_lps
                        while remaining_time > 0:
                            dt = yield
                            if dt is None or dt <= 0:
                                continue
                            remaining_time -= dt
                    dt = yield

        return _talk(now_lps)

    def show(self, sprite: str) -> arcade.Sprite:
        """
        Возвращает спрайт персонажа
        :param sprite: Название спрайта
        :raises FileNotFoundError: Если спрайт не был найден
        """
        textures = fm.get_character_textures(sprite)

        if sprite not in textures:
            raise FileNotFoundError(f"Character sprite \"{sprite}\" was not found in \"./game/images/characters/{self.char_id}/{sprite}\"")

        now_sprite = arcade.Sprite(textures[sprite])
        return now_sprite

class ListCharacters:
    def __init__(self) -> None:
        """
        Хранит в себе список всех персонажей
        """
        self.characters = {
            "j" : Character("Джопа", "j", name_colour="#D2691E", colour="#CD853F"),
            "aj": Character("АнтиДжек", "aj", name_colour="#3f87cd", c_scale=0.5, colour="#2167C4"),
            "sj": Character("ГлупоДжек", "sj", name_colour="#D1D0CF", c_scale=0.5, colour="#D4D4D4"),
            "narr" : Character(" ", None, text_anch="center"),

            "masorubka" : Character("Мясорубка/", char_id="masorubka", name_colour="#FFB6C1", colour="#FFB6C1", c_scale=0.8),
            "edwin" : Character("Эдвин/", char_id="edwin", name_colour="#FFDEAD", colour="#FFDEAD", c_scale=0.8),
            "rony" : Character("Рони/", char_id="rony", name_colour="#c9976c", colour="#c9976c", c_scale=0.8),
            "bromand" : Character("Броманд/", char_id="bromand", name_colour="#7FFF00", colour="#7FFF00", c_scale=0.8),
            "uni" : Character("Юни/", char_id="uni", name_colour="#00FF7F", colour="#00FF7F", c_scale=0.8)
        }

    def __getitem__(self, item) -> dict[str : Character]:
        return self.characters[item]


def init_file() -> None:
    """
    Инициализирует основные классы
    """
    global sm, am, da, lc, wwl, scene, fm

    timee = time.time()
    print("files_manager...")
    fm = FilesManager()
    print("Saves...")
    sm = Saves_manager()
    print("Audio manager...")
    am = AudioManager(sm, fm)
    print("Lore...")
    wwl = Wwl(fm)
    print("Scene...")
    scene = Scene(fm)
    print("characters...")
    lc = ListCharacters()
    print("Discord...")
    da = Discord_act()
    print(f"Init done for {round(time.time() - timee, 2)}s")
