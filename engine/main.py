import arcade
import pyglet
from pyglet.event import EVENT_HANDLE_STATE
from pyglet.graphics import Batch
import arcade.gui as agui
import arcade.gui.widgets.layout
from typing import Optional, Literal
import time
import re
import os
import random
import json
import uuid
import sys
sys.path.append(os.path.dirname(__file__))
from gui import UISliderVertical
from scene import Scene
from lore_viewer import Wwl
from waiter import Waiter
from saves import Saves_manager

arcade.load_font("game/fonts/Kurale-Regular.ttf")


class Persistent:
    def __setattr__(self, name, value):
        Saves_manager().persistent.set_persistent(name, value)
        super().__setattr__(name, value)

    def __getattribute__(self, item):
        super().__setattr__(item, Saves_manager().persistent.get_persistent(item))
        return Saves_manager().persistent.get_persistent(item)

class Define:
    def __init__(self):
        object.__setattr__(self, 'defines', {})

    def __setattr__(self, name, value):
        defines = object.__getattribute__(self, 'defines')
        defines[name] = value
        object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        if name == 'defines':
            return object.__getattribute__(self, 'defines')
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            defines = object.__getattribute__(self, 'defines')
            return defines.get(name, {})


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
    def init(self):
        return self.GameMenu, self.SettingsMenu, self.SaveMenu, self.GameView


    class Main_template(arcade.View):
        def __init__(self):
            super().__init__()
            self.cursor_texture = arcade.Sprite("game/images/gui/cursor.png", 0.2)
            self.window.background_color = arcade.color.WHITE
            self.background_color = arcade.color.WHITE
            self.fps = {
                'window': [],
                'last_print_time': time.time(),
                'avg_fps': 0.0,
                'min_fps': 0.0,
                'max_fps': 0.0,
                'label': arcade.Text(
                    "FPS: Avg=0, Min=0, Max=0",
                    x=10,
                    y=self.window.height - 10,
                    color=arcade.color.ARCADE_GREEN,
                    font_size=14,
                    anchor_x="left",
                    anchor_y="top",
                )
            }
        def on_update(self, delta_time: float) -> bool | None:
            self.cursor_texture.position = (self.window._mouse_x, self.window._mouse_y)
            self.window.set_mouse_visible(False)

            if sm.volume.get_other("show_fps"):
                current_fps = 1.0 / delta_time if delta_time > 0 else 0

                self.fps['window'].append(current_fps)
                if len(self.fps['window']) > 60:
                    self.fps['window'].pop(0)

                if time.time() - self.fps['last_print_time'] >= 1.0:
                    self.fps['avg_fps'] = sum(self.fps['window']) / len(self.fps['window'])
                    self.fps['min_fps'] = min(self.fps['window'])
                    self.fps['max_fps'] = max(self.fps['window'])

                    self.fps['label'].text = f"FPS: Avg={int(self.fps['avg_fps'])}, Min={int(self.fps['min_fps'])}, Max={int(self.fps['max_fps'])}"

                    self.fps['last_print_time'] = time.time()


        def on_draw(self) -> bool | None:
            arcade.draw_sprite(self.cursor_texture)
            if sm.volume.get_other("show_fps"):
                arcade.draw_lrbt_rectangle_filled(
                    left=5,
                    right=250,
                    bottom=self.window.height - 35,
                    top=self.window.height - 10,
                    color=(0, 0, 0, 200)
                )
                self.fps['label'].draw()

    class GameView(Main_template):

        def __init__(self, session_id: Optional[str] = None) -> None:
            super().__init__()

            self.NAMESPACE = {
                "persistent": Persistent(),
                "define": Define()
            }
            self.settings_scene = arcade.Scene()

            self.settings_manager = agui.UIManager()
            self.settings_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=10)
            self.settings_v_box_1 = arcade.gui.widgets.layout.UIBoxLayout(space_between=10)
            self.settings_v_box_1 = arcade.gui.widgets.layout.UIBoxLayout(space_between=10)
            self.settings_h_box = arcade.gui.widgets.layout.UIBoxLayout(vertical=False, space_between=20)
            self.settings_h_box.visible = False

            self.delta_time = 0.0

            self.dialog_window: Optional[arcade.Sprite] = None
            self.dialog_text_batch = Batch()
            self.dialog_texts: list = []
            self.cname_text: Optional[arcade.Text] = None

            self.scene = Scene()

            self.menu_manager = agui.UIManager()
            self.menu_manager.disable()
            self.menu_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

            self.waiting_dialogue = Waiter(True)
            self.waiting_settings = Waiter()

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
                self.scene.add_sprite("fade", "", sprite)

                #settings bg
                def create_settings():
                    texture = arcade.load_texture("game/images/gui/in_game_settings.png")

                    sprite = arcade.Sprite(
                        texture,
                        center_x=self.width * 0.5,
                        center_y=self.height * 0.5,
                        scale=1.0
                    )
                    self.settings_scene.add_sprite("in_game_settings", sprite)
                    self.settings_scene["in_game_settings"].alpha = 0

                    def create_settings_buttons():
                        with open("game/data.JSON", "r", encoding="UTF-8") as data:
                            data = json.load(data)
                        volumes = data['options']

                        def return_to_main_menu(event=None):
                            self.actions.active_generators.clear()

                            am.stop_sound()
                            am.stop_music()
                            am.stop_voice()
                            self.window.set_fullscreen(False)
                            self.window.size = (1024, 786)
                            game = Views.GameMenu()
                            self.window.show_view(game)
                            init_file()

                        def create_save(event=None):
                            try:
                                music_file = am.music.sound.file_name
                            except FileNotFoundError:
                                music_file = None
                            except AttributeError:
                                music_file = None

                            characters = [
                                {
                                    "id": str(i),
                                    "path": str(o.texture.file_path),
                                    "size": round(i.size),
                                    "pos": o.position
                                }
                                for i, o in self.scene["characters"].items()
                            ]

                            bg = [
                                {
                                    "layer" :  0,
                                    "path" : str(i.texture.file_path),
                                    "size" : round(i.size),
                                    "pos" : i.position
                                }
                                for i in self.scene["bg"].values()
                            ]

                            scene = {
                                "bg" : bg,
                                "characters" : characters,
                                "music" : music_file

                            }
                            Saves_manager().save.create_save(self.session_id,
                                                defines=self.NAMESPACE["define"].defines,
                                                position=wwl.pose-1,
                                                label=wwl.label,
                                                scene=scene)


                        return_button = agui.UIFlatButton(
                            text="Главное меню",
                            width=300,
                            height=50,
                            style=STYLE_DEFAULT_BUTTON
                        )
                        return_button.on_click = return_to_main_menu
                        self.settings_v_box.add(return_button)

                        save_button = agui.UIFlatButton(
                            text="Сохранить",
                            width=200,
                            style=STYLE_DEFAULT_BUTTON
                        )
                        save_button.on_click = create_save
                        self.settings_v_box.add(save_button)

                        self.settings_v_box.add(arcade.gui.UISpace(height=20))

                        music_volume_label = agui.UILabel(
                            "Музыка",
                            text_color=arcade.color.WHITE,
                            font_size=20,
                            font_name=FONT_NAME
                        )
                        self.settings_v_box.add(music_volume_label)

                        music_volume_slider = agui.UISlider(
                            value=volumes['volume']["music"] * 100,  # начальное значение
                            min_value=0,
                            max_value=200,
                            width=300,
                            height=20
                        )
                        self.settings_v_box.add(music_volume_slider)
                        self.settings_v_box.add(arcade.gui.UISpace(height=10))

                        sound_volume_label = agui.UILabel(
                            "Звуки",
                            text_color=arcade.color.WHITE,
                            font_size=20,
                            font_name=FONT_NAME
                        )
                        self.settings_v_box.add(sound_volume_label)

                        sound_volume_slider = agui.UISlider(
                            value=volumes['volume']["sound"] * 100,  # начальное значение
                            min_value=0,
                            max_value=200,
                            width=300,
                            height=20
                        )
                        self.settings_v_box.add(sound_volume_slider)
                        self.settings_v_box.add(arcade.gui.UISpace(height=10))

                        voice_volume_label = agui.UILabel(
                            "Голос",
                            text_color=arcade.color.WHITE,
                            font_size=20,
                            font_name=FONT_NAME
                        )
                        self.settings_v_box.add(voice_volume_label)

                        voice_volume_slider = agui.UISlider(
                            value=volumes['volume']["voice"] * 100,  # начальное значение
                            min_value=0,
                            max_value=200,
                            width=300,
                            height=20
                        )
                        self.settings_v_box.add(voice_volume_slider)



                        lps_label = agui.UILabel(
                            "Скорость появления букв",
                            text_color=arcade.color.WHITE,
                            font_size=20,
                            font_name=FONT_NAME
                        )
                        self.settings_v_box_1.add(lps_label)
                        self.lps_slider = agui.UISlider(
                            value=volumes["lps"],  # начальное значение
                            min_value=20,
                            max_value=110,
                            width=300,
                            height=20
                        )
                        self.settings_v_box_1.add(self.lps_slider)
                        self.settings_v_box_1.add(arcade.gui.UISpace(height=20))

                        fade_speed_label = agui.UILabel(
                            "Скорость переходов",
                            text_color=arcade.color.WHITE,
                            font_size=20,
                            font_name=FONT_NAME
                        )
                        self.settings_v_box_1.add(fade_speed_label)
                        self.fade_speed_slider = agui.UISlider(
                            value=volumes["fade_speed"],  # начальное значение
                            min_value=-10,
                            max_value=10,
                            width=300,
                            height=20
                        )
                        self.settings_v_box_1.add(self.fade_speed_slider)

                        self.settings_h_box.add(self.settings_v_box_1)
                        self.settings_h_box.add(self.settings_v_box)

                        ui_anchor_layout = arcade.gui.widgets.layout.UIAnchorLayout()
                        ui_anchor_layout.add(child=self.settings_h_box, anchor_x="left", align_x=80)

                        self.settings_manager.add(ui_anchor_layout)

                    create_settings_buttons()

                create_settings()
            create_widgets()

            self.start_trigger: bool = True

            def load_saves(session_id):
                if session_id is None:
                    self.session_id = str(uuid.uuid4())
                else:
                    self.session_id = session_id
                    save = Saves_manager().save.get_save(self.session_id)
                    wwl.label = save["label"]
                    wwl.pose = save["position"]
                    for i, o in save["defines"].items():
                        self.NAMESPACE["define"].defines[i] = o

                    scene = save["scene"]

                    for i in scene["bg"]:
                        bg_sprite = arcade.Sprite(i["path"])
                        bg_sprite.size = tuple(i["size"])
                        bg_sprite.position = tuple(i["pos"])
                        self.scene.add_sprite("bg", f"bg_{i["layer"]}", bg_sprite)

                    for i in scene["characters"]:
                        character_sprite = arcade.Sprite(i["path"])
                        character_sprite.size = tuple(i["size"])
                        character_sprite.position = tuple(i["pos"])
                        self.scene.add_sprite("characters", i["id"], character_sprite)

                    if scene["music"] is not None:
                        am.play_music(scene["music"])

            load_saves(session_id)

            self.actions = self.Actions(self)

            print(self.session_id)

        def format_text(self, text: str):
            pattern = r'((?<!\\)\[[^\]]*(?:(?<!\\)\][^\[]*)*?(?<!\\)\])'
            text = re.split(pattern, str(text))
            for e, i in enumerate(text):
                if i.startswith("[") and i.endswith("]"):
                    text[e] = self.NAMESPACE.get(i.strip("[]"), "NONE")
            text = "".join(text).replace("\\\\", "\\")
            return text

        def talk_manager(self):
            now = wwl.get_thing()
            res = self.talk(now)

            match res:
                case "NEXT":
                    self.talk_manager()
                case "REPEAT":
                    # self.talk(now)
                    return None
                case "END":
                    return None
                case "END_text":
                    return None
                case "CHANEL":
                    self.window.set_fullscreen(False)
                    self.window.size = (1024, 786)
                    game = Views.GameMenu(False)
                    self.window.show_view(game)
                    init_file()

        def talk(self, now):
            global dialog_text_text, cname_text_text
            global cname_text_colour, dialog_text_colour
            global text_anchor
            global wait_trigger

            while True:

                if now is None:
                    return None

                match now['action']:

                    case "SAY":
                        def format_dialogue(text: str):
                            text = re.sub(r'\{[^}]*\}', '', text)
                            text = text.replace(r'\n ', '\n')
                            return text.split('\n')

                        self.dialog_texts = []

                        self.start_trigger = False
                        pon = lc.get_character(now["character"]).talk(self.format_text(now["args"]))

                        if self.actions.talk_generator is not None:
                            self.actions.talk_generator = None
                            i = -2
                            while True:
                                nowe = wwl.get_thing(pos_offset = i, edit_main=False)
                                if nowe['action'] == 'SAY':
                                    wwl.pose += (i + 2)
                                    break
                                else:
                                    i -= 1
                            dialog_text_text = format_dialogue(nowe['args'])
                            cname_text_text = lc.get_character(nowe['character']).c_name
                            cname_text_colour = lc.get_character(nowe['character']).name_colour
                            dialog_text_colour = lc.get_character(nowe['character']).colour
                            text_anchor = lc.get_character(nowe['character']).text_anch
                        else:
                            self.actions.talk_generator = pon

                        return "END_text"

                    case "PLAY":
                        match now["play_what"]:
                            case "MUSIC":
                                target = am.play_music(f"game/music/{now['path']}", now["loop"], float(now["volume"]), effect=now["effect"])
                                self.actions.active_generators.append(target)

                            case "SOUND":
                                target = am.play_sound(f"game/sounds/{now['path']}", bool(now["loop"]), float(now["volume"]), effect=now["effect"])
                                self.actions.active_generators.append(target)
                        return "NEXT"

                    case "STOP":
                        match now["what"]:
                            case "MUSIC":
                                if now["effect"] is not None:
                                    target = am.stop_music(now["effect"])
                                    self.actions.active_generators.append(target)
                                else:
                                    am.stop_music()
                            case "SOUND":
                                if now["effect"] is not None:
                                    target = am.stop_sound(now["effect"])
                                    self.actions.active_generators.append(target)
                                else:
                                    am.stop_sound()
                        return "NEXT"

                    case "SHOW":
                        sprite = lc.get_character(now["character"]).show(str(now["sprite"]))
                        if 'at' in now:
                            sprite.center_y = sprite.height / 2
                            match now['at']:
                                case "center":
                                    sprite.center_x = self.width // 2
                                case "left":
                                    sprite.center_x = (self.width // 2) * 0.4
                                case "right":
                                    sprite.center_x = (self.width // 2) * 1.6
                        else:
                            if now["character"] in self.scene["characters"]:
                                sprite.position = self.scene["characters"][now["character"]].position
                                sprite.scale = self.scene["characters"][now["character"]].scale
                        self.scene.add_sprite("characters", now["sprite"].split(" ")[0], sprite)
                        return "NEXT"

                    case "HIDE":
                        self.scene.delete_sprite("characters", now["character"])
                        return "NEXT"

                    case "MOVE":
                        self.actions.start_action("move_sprite", now)
                        return "NEXT"

                    case "SCENE":
                        self.scene.clear_layer("characters")
                        self.scene.clear_layer("bg")
                        texture = arcade.load_texture(f"game/images/scenes/{now['filename']}")
                        sprite = arcade.Sprite(
                            texture,
                            scale=float(now['scale']),
                            center_x=self.width * 0.5,
                            center_y=self.height * 0.5
                        )
                        self.scene.add_sprite("bg", "bg_0", sprite)
                        return "NEXT"

                    case "FADE":
                        wait_trigger.on()
                        match now["type"]:
                            case "FADEIN":
                                self.actions.start_action("fadein", now)
                            case "FADEOUT":
                                self.actions.start_action("fadeout", now)
                            case _:
                                wait_trigger.off()
                        return "NEXT"

                    case "JUMP":

                        wwl.pose = 0
                        wwl.label = now["label"]

                        return "NEXT"

                    case "MENU":
                        wait_trigger.on()

                        dialog_text_text = [" "]
                        cname_text_text = ""

                        self.show_menu(now['data'])

                        return "END"

                    case "WAIT":
                        self.actions.start_action("wait", now)
                        return "NEXT"

                    case "END":

                        wwl.label = "main"
                        wwl.pose = 0

                        dialog_text_text = [" "]
                        cname_text_text = ""
                        return "CHANEL"


                    case "EXECUTE":
                        exec(now["data"], self.NAMESPACE)
                        return "NEXT"

                    case _:
                        print(f"Неопознанная команда: {now}")

        def on_draw(self):
            """
            Render the screen.
            """

            if not self.start_trigger:
                self.clear()
                self.scene.draw()
                arcade.draw_sprite(self.dialog_window)
                self.update_main_windows()
                self.dialog_text_batch.draw()
                self.menu_manager.draw()
                self.settings_scene.draw()
                self.settings_manager.draw()
            super().on_draw()

        def show_menu(self, data):
            global wait_trigger

            def jump(label: str):
                global wait_trigger
                wwl.pose = 0
                wwl.label = label
                self.menu_manager.clear()
                self.menu_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)
                #wait_trigger.off()
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

        def show_settings(self, state: Optional[bool] = None):
            settings = self.settings_scene["in_game_settings"]

            if state is not None:
                turn_on = state
            else:
                turn_on = settings.alpha <= 0

            (self.waiting_settings.on if turn_on else self.waiting_settings.off)()
            self.settings_h_box.visible = turn_on
            settings.alpha = 255 if turn_on else 0

        def on_update(self, delta_time):
            """
            All the logic to move, and the game logic goes here.
            Normally, you'll call update() on the sprite lists that
            need it.
            """

            self.delta_time = delta_time

            self.scene.update()

            self.actions.update(delta_time)

            if self.waiting_dialogue:
                if not wait_trigger:
                    self.talk_manager()
                    self.waiting_dialogue.off()

            self.settings_scene.update(delta_time)
            self.menu_manager.enable()

            if self.waiting_settings:
                self.settings_manager.enable()
            else:
                self.settings_manager.disable()

            if self.waiting_settings:
                am.music.set_volume(round(self.settings_v_box.children[4].value / 100, 2))
                am.sound.set_volume(round(self.settings_v_box.children[7].value / 100, 2))
                am.voice.set_volume(round(self.settings_v_box.children[10].value / 100, 2))
                sm.volume.set_other("lps", round(self.settings_v_box_1.children[1].value, 2))
                sm.volume.set_other("fade_speed", round(self.settings_v_box_1.children[4].value, 2))
            
            super().on_update(delta_time)

        def on_key_press(self, key, modifiers):
            if (key == arcade.key.SPACE or key == arcade.key.ENTER or key == arcade.key.ENTER) and not self.waiting_settings:
                self.waiting_dialogue.on()
            if key == arcade.key.S:
                self.show_settings()

        def on_mouse_release(self, x, y, button, modifiers):
            if (int(button) == 1) and not self.waiting_settings:
                self.waiting_dialogue.on()

        def update_main_windows(self):

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


                for i, line in enumerate(dialog_text_text):
                    for e, sline in enumerate(split_by_length(line, 60)):
                        if text_anchor == "left":
                            t = arcade.Text(
                                text=sline,
                                x=self.width * 0.18,
                                y=(self.height * 0.2) - (i+e) * (30 + 10),
                                font_size=30,
                                color=dialog_text_colour,
                                batch=self.dialog_text_batch,
                                font_name=FONT_NAME,
                                anchor_x=text_anchor
                            )
                        elif text_anchor == "center":
                            t = arcade.Text(
                                text=sline,
                                x=self.width // 2,
                                y=(self.height * 0.2) - (i + e) * (30 + 10),
                                font_size=30,
                                color=dialog_text_colour,
                                batch=self.dialog_text_batch,
                                font_name=FONT_NAME,
                                anchor_x=text_anchor
                            )
                        elif text_anchor == "right":
                            t = arcade.Text(
                                text=sline,
                                x=self.width * 0.82,
                                y=(self.height * 0.2) - (i + e) * (30 + 10),
                                font_size=30,
                                color=dialog_text_colour,
                                batch=self.dialog_text_batch,
                                font_name=FONT_NAME,
                                anchor_x=text_anchor
                            )

                        self.dialog_text_batch.draw()

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

        class Actions:
            def __init__(self, main):
                self.main: Views.GameView = main
                self.active_generators = []
                self.talk_generator = None

            def _fadein(self, now: dict):
                global wait_trigger
                wait_trigger.on()
                start_time = time.time()
                duration = now["time"] + sm.volume.get_other("fade_speed") if now["time"] + sm.volume.get_other(
                    "fade_speed") > 0 else 0

                while True:

                    elapsed = time.time() - start_time

                    if elapsed >= duration:
                        self.main.scene["fade"].alpha = 255
                        wait_trigger.off()
                        return None

                    progress = elapsed / duration
                    alpha = int(progress * 255)

                    self.main.scene["fade"].alpha = alpha

                    yield

            def _fadeout(self, now: dict):
                global wait_trigger
                wait_trigger.on()
                start_time = time.time()
                duration = now["time"] + sm.volume.get_other("fade_speed") if now["time"] + sm.volume.get_other("fade_speed") > 0 else 0

                while True:

                    elapsed = time.time() - start_time
                    if elapsed >= duration:
                        alpha = 0
                        wait_trigger.off()
                        return None

                    progress = elapsed / duration
                    alpha = 255 - int(progress * 255)

                    self.main.scene["fade"].alpha = alpha

                    yield

            def _move(self, now: dict):
                # Хз работает ли это или нет, но вроде должно
                sprite = self.main.scene["characters"][now["character"]]
                while True:
                    dx = now["pos"][0] - sprite.center_x
                    dy = now["pos"][1] - sprite.center_y
                    distance = (dx ** 2 + dy ** 2) ** 0.5
                    if distance > now["speed"]:
                        sprite.center_x += dx / distance * now["speed"]
                        sprite.center_y += dy / distance * now["speed"]
                    else:
                        sprite.center_x = now["pos"][0]
                        sprite.center_y = now["pos"][1]
                    time.sleep(0.01)
                    if distance <= 0:
                        break
                    yield

            def _wait(self, now):
                global wait_trigger
                start_time = time.time()

                wait_trigger.on()

                while time.time() - start_time < now["time"]:
                    yield

                wait_trigger.off()

            def update(self, delta_time: float):
                if self.talk_generator:
                    try:
                        next(self.talk_generator)
                    except StopIteration:
                        self.talk_generator = None

                for gen in self.active_generators[:]:
                    try:
                        next(gen)
                    except StopIteration:
                        self.active_generators.remove(gen)
                    except TypeError:
                        self.active_generators.remove(gen)

            def start_action(self, name: Literal["fadein", "fadeout", "move_sprite", "wait"], now: dict):
                if name == "fadein":
                    self.active_generators.append(self._fadein(now))
                elif name == "fadeout":
                    self.active_generators.append(self._fadeout(now))
                elif name == "move_sprite":
                    self.active_generators.append(self._move(now))
                elif name == "wait":
                    self.active_generators.append(self._wait(now))

    class GameMenu(Main_template):
        def __init__(self, show_lc: bool = True):
            super().__init__()

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

            am.stop_music()
            am.stop_voice()
            am.stop_sound()

            if show_lc:
                self.show_ls()


        def show_ls(self):
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

        def on_draw(self):
            """
            Render the screen.
            """

            self.clear()
            self.manager.draw()
            arcade.draw_sprite(self.loading_screen)
            arcade.draw_sprite(self.loading_screen_fade)
            arcade.draw_sprite(self.why)
            super().on_draw()

        def on_update(self, delta_time):
            """
            All the logic to move, and the game logic goes here.
            Normally, you'll call update() on the sprite lists that
            need it.
            """
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

        def on_key_press(self, key: int, modifiers: int) -> bool | None:
            if (key == arcade.key.L and modifiers & arcade.key.MOD_SHIFT) and not self.is_loading:
                self.why.alpha = 255
                self.is_loading  = True

        def show_main_windows(self):

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
                exit_button.on_click = lambda event: arcade.exit()
                self.v_box.add(exit_button)

                ui_anchor_layout = arcade.gui.widgets.layout.UIAnchorLayout()
                ui_anchor_layout.add(child=self.v_box, anchor_x="center_x", anchor_y="center_y")

                self.manager.add(ui_anchor_layout)

            create_menu_buttons()

    class SaveMenu(Main_template):
        def __init__(self):
            super().__init__()

            saves = sm.save.get_all_saves()
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

        def generate_buttons(self):

            def return_to_main_menu(event=None):
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
        def __init__(self):
            super().__init__()

            self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=0)
            self.v_box_1 = arcade.gui.widgets.layout.UIBoxLayout(space_between=0)
            self.main_h_box = arcade.gui.widgets.layout.UIBoxLayout(vertical=False, space_between=20)

            self.manager = agui.UIManager()
            self.manager.enable()
            self.other_buttons = []

            self.manager.add(self.main_h_box)

            self.music_volume_slider: Optional[agui.UISlider] = None
            self.sound_volume_slider: Optional[agui.UISlider] = None
            self.voice_volume_slider: Optional[agui.UISlider] = None
            self.lps_slider: Optional[agui.UISlider] = None
            self.fade_speed_slider: Optional[agui.UISlider] = None

            self.show_main_windows()

        def on_draw(self):
            self.clear()
            self.manager.draw()
            super().on_draw()

        def on_update(self, delta_time: float) -> bool | None:
            if self.window.visible:
                am.music.set_volume(round(self.music_volume_slider.value / 100, 2))
                am.sound.set_volume(round(self.sound_volume_slider.value / 100, 2))
                am.voice.set_volume(round(self.voice_volume_slider.value / 100, 2))
                sm.volume.set_other("lps", round(self.lps_slider.value, 2))
                sm.volume.set_other("fade_speed", round(self.fade_speed_slider.value, 2))
            super().on_update(delta_time)

        def show_main_windows(self):

            def create_menu_buttons():
                with open("game/data.JSON", "r", encoding="UTF-8") as data:
                    data = json.load(data)
                volumes = data['options']

                def return_to_main_menu(event=None):
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
                FPS_check_box.on_click = lambda event=None: sm.volume.set_other("show_fps", not sm.volume.get_other("show_fps"))
                FPS_check_box.center_x = self.window.center_x
                FPS_check_box.center_y = self.window.height * 0.7
                self.manager.add(FPS_check_box)

                music_volume_label = agui.UILabel(
                    "Музыка",
                    text_color=arcade.color.BLACK,
                    font_name=FONT_NAME
                )
                self.v_box.add(music_volume_label)

                self.music_volume_slider = agui.UISlider(
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

                self.sound_volume_slider = agui.UISlider(
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

                self.voice_volume_slider = agui.UISlider(
                    value=volumes['volume']["voice"]*100,  # начальное значение
                    min_value=0,
                    max_value=200,
                    width=300,
                    height=20
                )
                self.v_box.add(self.voice_volume_slider)
                self.v_box.add(arcade.gui.UISpace(height=20))



                self.lps_slider = agui.UISlider(
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

                self.fade_speed_slider = agui.UISlider(
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



class Character():

    def __init__(self, name: str, char_id: Optional[str] = None, colour: str = "", name_colour: str = "", c_scale: float = 1.0, text_anch: str = "left", lps: int = 60):
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

        def find_files(extension: list):
            results = {}
            start_path = f"./game/images/characters/{char_id}"

            for i in extension:
                for root, dirs, files in os.walk(start_path):
                    for file in files:
                        if file.lower().endswith(i.lower()):
                            full_path = os.path.join(root, file)
                            results[file.split(".")[0]] = arcade.Sprite(full_path.replace("\\", "/"))

            return results

        self.c_name = name
        self.colour = hex_to_rgb(colour)
        self.name_colour = hex_to_rgb(name_colour)
        self.c_scale = c_scale
        self.def_lps = lps
        if self.def_lps == 60:
            self.lps = sm.volume.get_other("lps")
        else:
            self.lps = lps

        self.action = None
        self.last_text = " "

        self.char_id = char_id

        self.sprites = find_files([".png", ".jpg", ".jpeg", ".PNG", ".JPEG"])

        self.text_anch = text_anch


    def talk(self, text: str):
        global dialog_text_colour, cname_text_colour
        global dialog_text_text, cname_text_text
        global text_anchor

        def replace_char_by_index(text, index, new_char):
            if index < 0 or index >= len(text):
                return text
            return text[:index] + new_char + text[index + 1:]

        if self.def_lps == 60:
            self.lps = sm.volume.get_other("lps")

        dialog_text_text_alt = [" "]
        string_index_alt = 0
        _text_alt = []
        for char in re.findall(r'\\n |\{[^}]*\}|\S|\s', text):

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

        def _talk():
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
                    for char in re.findall(r'\\n |\{[^}]*\}|\S|\s', text):
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

                        def talk_sound():
                            def _get_random_sound_path():
                                files = [f"./game/sounds/character_voice/{self.char_id}/{f}" for f in
                                         os.listdir(f"./game/sounds/character_voice/{self.char_id}") if
                                         os.path.isfile(os.path.join(f"./game/sounds/character_voice/{self.char_id}", f))]
                                return random.choice(files)

                            am.play_voice(_get_random_sound_path())

                        if ((index % 4 == 0 and char not in (",", ".", "!", "&", "?")) or index == 1) and self.char_id is not None:
                            if os.path.isdir(f"./game/sounds/character_voice/{self.char_id}"):
                                talk_sound()

                        if char == ".":
                            if not fast:
                                old_time = time.time()
                                while time.time() < old_time + 0.1:
                                    yield

                        elif char == ",":
                            if not fast:
                                old_time = time.time()
                                while time.time() < old_time + 0.05:
                                    yield
                        elif char.startswith("{") and str(char).endswith("}"):
                            char = char[1:][:-1]

                            if char.startswith("w"):
                                i -= 1
                                old_time = time.time()
                                while time.time() < old_time + float(char.split("=")[-1]):
                                    yield
                            if char.startswith("f"):
                                i -= 1
                                fast = True

                        if not fast:
                            old_time = time.time()
                            while time.time() < old_time + 1 / self.lps:
                                yield
                    self.action = None
                    return None
                else:
                    if not fast:
                        old_time = time.time()
                        while time.time() < old_time + 1 / self.lps:
                            yield
                    yield

        return _talk()

    def show(self, sprite: str, scale: Optional[int] = None) -> arcade.Sprite:
        if scale is None:
            scale = self.c_scale
        now_sprite = self.sprites[sprite]
        now_sprite.scale = scale
        return now_sprite

class ListCharacters:
    def __init__(self):
        self.characters = {
            "j" : Character("Джопа", "j", name_colour="#D2691E", colour="#CD853F"),
            "aj": Character("АнтиДжек", "aj", name_colour="#3f87cd", c_scale=0.5, colour="#2167C4"),
            "sj": Character("ГлупоДжек", "sj", name_colour="#D1D0CF", c_scale=0.5, colour="#D4D4D4"),
            "narr" : Character(" ", None, text_anch="center")
        }
    def get_character(self, char_id: str) -> Character:
        return self.characters[char_id]



class AudioChannel:
    def __init__(self, default_volume: float=1.0, modifier: float = 1.0, volume_type: Optional[str] = None):
        '''
        :param default_volume: Громкость по умолчанию
        :param volume_type: Тип звука ("music"/"sound"/"voice")
        '''
        self.player: Optional[pyglet.media.player.Player] = None
        self.default_volume: float = default_volume # Громкость по умолчанию
        self.volume_type: Optional[str] = volume_type # Тип канала
        self.modifier = modifier # Модификатор громкости. Предназначен для управления громкости с ползунков из настроек
        self._fade_modifier: float = 1.0 # Модификатор громкости. Предназначен для управления громкости во время плавных переходов (FADEIN/FADEOUT)
        self._local_modifier: float = 1.0 # Модификатор громкости. Предназначен для управления громкости текущего трека. Сбрасывается при запуске нового трека

    @property
    def fade_modifier(self):
        return self._fade_modifier

    @fade_modifier.setter
    def fade_modifier(self, value):
        self._fade_modifier = value
        if self.player:
            self.player.volume = self.default_volume * self.modifier * self._fade_modifier * self._local_modifier
            # Обновляем громкость проигрывателя, если параметр self._fade_modifier был изменён

    def play(self, path, loop=False, speed=1.0, local_volume: Optional[float]=None):
        """
        Включает звук
        :param path: Путь к файлу
        :param loop: Если True, звук будет зацикливаться
        :param speed: Скорость проигрывания
        :return:
        """
        self.stop()

        if local_volume:
            self._local_modifier = local_volume

        sound = arcade.load_sound(path)
        volume = self.default_volume * self.modifier * self._fade_modifier * self._local_modifier

        self.player = sound.play(volume=volume, loop=loop, speed=speed)

    def stop(self):
        if self.player:
            self.player.delete()
        self._local_modifier = 1.0

    def pause(self):
        if self.player:
            self.player.pause()

    def resume(self):
        if self.player:
            self.player.play()

    def set_volume(self, vol, is_global: bool = True):
        """
        Изменяет громкость
        :param vol: Громкость
        :param is_global: Если True, применяет глобально, к этом и последующим звукам, а также, сохраняет значение. Если False, применяет громкость только к текущему звуку
        """

        if is_global:
            self.modifier = vol
            if self.player:
                self.player.volume = self.default_volume * self.modifier * self._fade_modifier * self._local_modifier

            # Сохраняем значения
            if self.volume_type == "music":
                sm.volume.set_music(self.modifier)
            elif self.volume_type == "sound":
                sm.volume.set_sound(self.modifier)
            elif self.volume_type == "voice":
                sm.volume.set_voice(self.modifier)
        else:
            self._local_modifier = vol
            if self.player:
                self.player.volume = self.default_volume * self.modifier * self._fade_modifier * self._local_modifier


    def is_playing(self):
        if self.player:
            return self.player.playing
        else:
            return False

class AudioManager:
    def __init__(self):

        self.music = AudioChannel(modifier=sm.volume.get_music(), volume_type="music")
        self.sound = AudioChannel(modifier=sm.volume.get_sound(), volume_type="sound")
        self.voice = AudioChannel(modifier=sm.volume.get_voice(), volume_type="voice", default_volume=2.0)

    def play_music(self, path: str, loop: Optional[bool] = False, volume: float = 1.0, effect: Optional[str] = None):

        match effect:
            case "FADE":
                def fadeout_music():
                    while self.music.fade_modifier < 1.0:
                        self.music.fade_modifier += 0.005
                        yield
                    self.music.fade_modifier = 1.0

                self.music.fade_modifier = 0.0
                self.music.play(path, loop=loop, local_volume=volume)
                return fadeout_music()

            case _:
                self.music.play(path, loop=loop, local_volume=volume)

    def play_sound(self, path, loop: Optional[bool] = False, volume: float = 1.0, effect: Optional[str] = None):

        match effect:
            case "FADE":
                def fadeout_sound():
                    while self.sound.fade_modifier < 1.0:
                        self.sound.fade_modifier += 0.005
                        yield
                    self.sound.fade_modifier = 1.0

                self.sound.fade_modifier = 0.0
                self.sound.play(path, loop=loop, local_volume=volume)
                return fadeout_sound()

            case _:
                self.sound.play(path, loop=loop, local_volume=volume)


    def play_voice(self, path, loop=False):
        self.voice.play(path, loop=loop, speed=random.randint(99, 101) / 100)

    def stop_music(self, effect: Optional[str] = None):
        match effect:
            case "FADE":
                def fadeout_music():
                    while 0.0 < self.music.fade_modifier:
                        self.music.fade_modifier -= 0.005
                        yield
                    self.music.fade_modifier = 0.0
                    self.music.stop()
                    self.music.fade_modifier = 1.0
                return fadeout_music()
            case _:
                self.music.stop()

    def stop_sound(self, effect: Optional[str] = None):
        match effect:
            case "FADE":
                def fadeout_sound():
                    while 0.0 < self.sound.fade_modifier:
                        self.sound.fade_modifier -= 0.005
                        yield
                    self.sound.fade_modifier = 0.0
                    self.sound.stop()
                    self.sound.fade_modifier = 1.0

                return fadeout_sound()

            case _:
                self.sound.stop()

    def stop_voice(self):
        self.voice.stop()


def init_file():
    """
    Инициализирует основные классы
    """
    global sm, am, lc, wwl
    sm = Saves_manager()
    am = AudioManager()
    lc = ListCharacters()
    wwl = Wwl()
