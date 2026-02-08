import arcade
import pyglet
from pyglet.event import EVENT_HANDLE_STATE
from pyglet.graphics import Batch
import arcade.gui as agui
import arcade.gui.widgets.layout
from typing import Optional, List, Tuple
from gui import SpriteButton, UISliderVertical
import threading
import time
import re
import os
import json
import random
import json
import uuid

from lore_viewer import Wwl

with open("./other/splashes.json", "r", encoding="UTF-8") as splashes:
    splashes = json.load(splashes)
splash = str(random.choice(splashes))
if splash.startswith(">"):
    splash = splash.format(username=str(os.getenv("USERNAME") or os.getenv("USER")))[1:]

wwl = Wwl()



class Persistent:
    def __setattr__(self, name, value):
        sm.persistent.set_persistent(name, value)
        super().__setattr__(name, value)

    def __getattribute__(self, item):
        super().__setattr__(item, sm.persistent.get_persistent(item))
        return sm.persistent.get_persistent(item)


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

WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080

arcade.load_font("fonts/Kurale-Regular.ttf")
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


wait_trigger: bool = False

WINDOW_TITLE = f"Game name"
GAME_NAME = "Game name"
last_talk = threading.Event()

dialog_text_text: list[str] = []
cname_text_text = ""

cname_text_colour = arcade.color.BLACK
dialog_text_colour = arcade.color.BLACK

class GameView(arcade.View):

    def __init__(self, session_id: Optional[str] = None) -> None:
        super().__init__()
        global am, wwl
        am = AudioManager()
        wwl = Wwl()

        print(session_id)
        self.NAMESPACE = {
            "persistent": Persistent(),
            "define": Define()
        }

        self.scene = arcade.Scene()
        self.settings_scene = arcade.Scene()

        self.settings_manager = agui.UIManager()
        self.settings_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=10)
        self.settings_v_box.visible = False

        self.delta_time = 0.0

        self.cursor_texture = arcade.Sprite("images/gui/cursor.png", 0.2)

        self.background_color = arcade.color.WHITE

        self.dialog_window: Optional[arcade.Sprite] = None
        self.dialog_text_batch = Batch()
        self.dialog_texts: list = []
        self.cname_text: Optional[arcade.Text] = None

        self.characters_sprites: dict[str : arcade.Sprite] = {}

        self.scene.add_sprite_list("bg")
        self.scene.add_sprite_list("characters")
        self.scene.add_sprite_list("fade")
        self.scene.add_sprite_list("gui")

        self.menu_manager = agui.UIManager()
        self.menu_manager.disable()
        self.menu_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

        self.waiting_dialogue = True
        self.waiting_settings = False

        self.last_text = " "

        def create_widgets():
            # dialog window
            texture = arcade.load_texture("images/gui/dialog_window.png")

            self.dialog_window = arcade.Sprite(
                texture,
                scale=6 * min(self.width / WINDOW_WIDTH, self.height / WINDOW_HEIGHT),
                center_x=self.width * 0.5,
                center_y=self.height * 0.13
            )

            #blackscreen
            texture = arcade.load_texture("images/gui/blackscreen.png")

            sprite = arcade.Sprite(
                texture,
                scale=50,
                center_x=self.width * 0.5,
                center_y=self.height * 0.5
            )
            sprite.alpha = 0
            self.scene.add_sprite("fade", sprite)

            #settings bg
            def create_settings():
                texture = arcade.load_texture("images/gui/in_game_settings.png")

                sprite = arcade.Sprite(
                    texture,
                    center_x=self.width * 0.5,
                    center_y=self.height * 0.5
                )
                self.settings_scene.add_sprite("in_game_settings", sprite)
                self.settings_scene["in_game_settings"].alpha = 0

                def create_settings_buttons():
                    with open("data.JSON", "r", encoding="UTF-8") as data:
                        data = json.load(data)
                    volumes = data['options']['volume']

                    def return_to_main_menu(event=None):
                        am.stop_sound()
                        am.stop_music()
                        am.stop_voice()
                        self.window.set_fullscreen(False)
                        self.window.size = (1024, 786)
                        game = GameMenu()
                        self.window.show_view(game)

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
                                "size": o.size,
                                "pos": o.position
                            }
                            for i, o in self.characters_sprites.items()
                        ]

                        bg = {
                            "path" : str(self.scene["bg"][-1].texture.file_path),
                            "size" : self.scene["bg"][-1].size,
                            "pos" : self.scene["bg"][-1].position
                        }

                        scene = {
                            "bg" : bg,
                            "characters" : characters,
                            "music" : music_file

                        }
                        sm.save.create_save(self.session_id,
                                            defines=self.NAMESPACE["define"].defines,
                                            position=wwl.pose,
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
                        value=volumes["music"] * 100,  # начальное значение
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
                        value=volumes["sound"] * 100,  # начальное значение
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
                        value=volumes["voice"] * 100,  # начальное значение
                        min_value=0,
                        max_value=200,
                        width=300,
                        height=20
                    )
                    self.settings_v_box.add(voice_volume_slider)

                    ui_anchor_layout = arcade.gui.widgets.layout.UIAnchorLayout()
                    ui_anchor_layout.add(child=self.settings_v_box, anchor_x="left", align_x=300)

                    self.settings_manager.add(ui_anchor_layout)

                create_settings_buttons()

            create_settings()
        create_widgets()

        self.start_trigger: bool = True

        def load_saves():
            if session_id is None:
                self.session_id = str(uuid.uuid4())
            else:
                self.session_id = session_id
                save = sm.save.get_save(self.session_id)
                wwl.label = save["label"]
                wwl.pose = save["position"]
                for i, o in save["defines"].items():
                    self.NAMESPACE["define"].defines[i] = o

                scene = save["scene"]

                bg_sprite = arcade.Sprite(scene["bg"]["path"])
                bg_sprite.size = tuple(scene["bg"]["size"])
                bg_sprite.position = tuple(scene["bg"]["pos"])
                self.scene["bg"].append(bg_sprite)

                for i in scene["characters"]:
                    character_sprite = arcade.Sprite(i["path"])
                    character_sprite.size = tuple(i["size"])
                    character_sprite.position = tuple(i["pos"])
                    self.characters_sprites[i["id"]] = character_sprite
                    self.scene["characters"].append(character_sprite)

                if scene["music"] is not None:
                    am.play_music(scene["music"])

        load_saves()

    def format_text(self, text: str):
        pattern = r'((?<!\\)\[[^\]]*(?:(?<!\\)\][^\[]*)*?(?<!\\)\])'
        text = re.split(pattern, str(text))
        for e, i in enumerate(text):
            if i.startswith("[") and i.endswith("]"):
                text[e] = self.NAMESPACE.get(i.strip("[]"), "NONE")
        text = "".join(text).replace("\\\\", "\\")
        return text

    def talk_manager(self):
        print(wwl.pose, wwl.label)
        now = wwl.get_thing()
        print(now)
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
                game = GameMenu(False)
                self.window.show_view(game)


    def talk(self, now):
        global dialog_text_text, cname_text_text
        global wait_trigger

        while True:

            if now is None:
                return None

            match now['action']:

                case "SAY":
                    self.dialog_texts = []

                    self.start_trigger = False
                    pon = lc.get_character(now["character"]).talk(self.format_text(now["args"]))

                    return "END_text"

                case "PLAY":
                    match now["play_what"]:
                        case "MUSIC":
                            am.play_music(f"music/{now['path']}", now["loop"], float(now["volume"]), effect=now["effect"])

                        case "SOUND":
                            am.play_sound(f"sounds/{now['path']}", bool(now["loop"]), float(now["volume"]), effect=now["effect"])
                    return "NEXT"

                case "STOP":
                    match now["what"]:
                        case "MUSIC":
                            if now["effect"] is not None:
                                am.stop_music(now["effect"])
                            else:
                                am.stop_music()
                        case "SOUND":
                            if now["effect"] is not None:
                                am.stop_sound(now["effect"])
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
                        if now["character"] in self.characters_sprites:
                            sprite.position = self.characters_sprites[now["character"]].position

                    if now["character"] in self.characters_sprites:
                        self.characters_sprites[now["character"]].remove_from_sprite_lists()
                    self.characters_sprites[now["character"]] = sprite
                    self.scene.add_sprite("characters", self.characters_sprites[now["character"]])
                    return "NEXT"

                case "HIDE":
                    self.characters_sprites[now["character"]].remove_from_sprite_lists()
                    del self.characters_sprites[now["character"]]
                    return "NEXT"

                case "MOVE":
                    self.Move.move_towards(self.characters_sprites[now["character"]], now["pos"][0], now["pos"][1], now["speed"])
                    return "NEXT"

                case "SCENE":
                    self.scene["bg"].clear()

                    for i in self.characters_sprites.values():
                        i.remove_from_sprite_lists()
                    self.characters_sprites.clear()
                    texture = arcade.load_texture(f"images/scenes/{now['filename']}")
                    sprite = arcade.Sprite(
                        texture,
                        scale=float(now['scale']),
                        center_x=self.width * 0.5,
                        center_y=self.height * 0.5
                    )
                    self.scene.add_sprite("bg", sprite)
                    return "NEXT"

                case "FADE":
                    match now["type"]:
                        case "FADEIN":
                            def editing_alpha():
                                global wait_trigger
                                wait_trigger = True
                                start_time = time.time()
                                duration = now["time"]

                                while True:

                                    elapsed = time.time() - start_time

                                    if elapsed >= duration:
                                        self.scene["fade"][0].alpha = 255
                                        break

                                    progress = elapsed / duration
                                    alpha = int(progress * 255)

                                    if not wait_trigger:
                                        wait_trigger = True

                                    self.scene["fade"][0].alpha = alpha

                                    time.sleep(0.01)

                                wait_trigger = False
                            threading.Thread(target=editing_alpha).start()
                        case "FADEOUT":
                            def editing_alpha():
                                global wait_trigger
                                wait_trigger = True
                                start_time = time.time()
                                duration = now["time"]

                                while True:

                                    elapsed = time.time() - start_time
                                    if elapsed >= duration:
                                        alpha = 0
                                        wait_trigger = False
                                        return None

                                    progress = elapsed / duration
                                    alpha = 255 - int(progress * 255)

                                    self.scene["fade"][0].alpha = alpha

                                    time.sleep(0.01)
                            threading.Thread(target=editing_alpha).start()
                    return "NEXT"

                case "JUMP":

                    wwl.pose = 0
                    wwl.label = now["label"]

                    return "NEXT"

                case "MENU":
                    global dialog_text_text, cname_text_text

                    dialog_text_text = [" "]
                    cname_text_text = ""

                    self.show_menu(now['data'])
                    wait_trigger = True

                    return "END"

                case "WAIT":

                    def _waiter():
                        global wait_trigger

                        wait_trigger = True
                        time.sleep(now["time"])
                        wait_trigger = False

                    threading.Thread(target=_waiter).start()
                    return "NEXT"

                case "END":

                    wwl.label = main
                    wwl.pose = 0

                    dialog_text_text = [" "]
                    cname_text_text = ""
                    return "CHANEL"


                case "EXECUTE":
                    exec(now["data"], self.NAMESPACE)
                    return "NEXT"

                case _:
                    return None

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
            arcade.draw_sprite(self.cursor_texture)

    def show_menu(self, data):

        def jump(label: str):
            global wait_trigger
            wwl.pose = 0
            wwl.label = label
            self.menu_manager.clear()
            self.menu_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)
            wait_trigger = False
            self.talk_manager()

        for k, v in data.items():
            button = agui.UIFlatButton(
                text=k,
                width=200,
                font_name=FONT_NAME,
                style=STYLE_DEFAULT_BUTTON
            )
            button.on_click = lambda event, label=v: jump(label)
            self.menu_v_box.add(button)

        ui_anchor_layout = arcade.gui.widgets.layout.UIAnchorLayout()
        ui_anchor_layout.add(child=self.menu_v_box, anchor_x="center_x", anchor_y="center_y")

        self.menu_manager.add(ui_anchor_layout)

    def show_settings(self, state: Optional[bool] = None):
        settings = self.settings_scene["in_game_settings"]

        if state is True:
            self.waiting_settings = True
            self.settings_v_box.visible = True
            settings.alpha = 255
        elif state is False:
            self.waiting_settings = False
            self.settings_v_box.visible = False
            settings.alpha = 0
        else:
            if settings.alpha > 0:
                self.waiting_settings = False
                self.settings_v_box.visible = False
                settings.alpha = 0
            else:
                self.waiting_settings = True
                self.settings_v_box.visible = True
                settings.alpha = 255

    def on_update(self, delta_time):
        """
        All the logic to move, and the game logic goes here.
        Normally, you'll call update() on the sprite lists that
        need it.
        """
        if self.waiting_dialogue:
            if not wait_trigger:
                self.talk_manager()
                self.waiting_dialogue = False

        self.delta_time = delta_time
        self.scene.update(delta_time)
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

        self.cursor_texture.position = (self.window._mouse_x, self.window._mouse_y)


    def on_key_press(self, key, modifiers):
        if (key == arcade.key.SPACE or key == arcade.key.ENTER or key == arcade.key.ENTER) and not self.waiting_settings:
            self.waiting_dialogue = True
        if key == arcade.key.S:
            self.show_settings()

    def on_mouse_release(self, x, y, button, modifiers):
        if (int(button) == 1) and not self.waiting_settings:
            self.waiting_dialogue = True

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

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> EVENT_HANDLE_STATE:
        self.window.set_mouse_visible(False)

    class Move():
        @staticmethod
        def move_towards(sprite, target_x, target_y, speed):

            def move():
                while True:
                    dx = target_x - sprite.center_x
                    dy = target_y - sprite.center_y
                    distance = (dx ** 2 + dy ** 2) ** 0.5
                    if distance > speed:
                        sprite.center_x += dx / distance * speed
                        sprite.center_y += dy / distance * speed
                    else:
                        sprite.center_x = target_x
                        sprite.center_y = target_y
                    time.sleep(0.01)
                    if distance <= 0:
                        break

            threading.Thread(target=move).start()

class Map(arcade.View):
    def __init__(self):
        super().__init__()

        self.scene = arcade.Scene()
        self.background_color = arcade.color.WHITE
        self.cursor_texture = arcade.Sprite("images/gui/cursor.png", 0.2)

    def on_draw(self):
        self.clear()
        self.scene.draw()
        arcade.draw_sprite(self.cursor_texture)



    def on_update(self, delta_time: float) -> bool | None:
        self.scene.update(delta_time)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> EVENT_HANDLE_STATE:
        self.cursor_texture.position = (x, y)
        self.window.set_mouse_visible(False)

    def on_close(self):
        self.window.set_fullscreen(False)
        self.window.size = (1024, 786)
        game = GameMenu()
        self.window.show_view(game)

class GameMenu(arcade.View):
    def __init__(self, show_lc: bool = True):
        super().__init__()

        global am, wwl
        am = AudioManager()
        wwl = Wwl()

        self.loading_screen = arcade.Sprite("images/gui/JE3000_logo-export.png", 1)
        self.loading_screen.position = (int(self.center_x), int(self.center_y))
        self.loading_screen_fade = arcade.Sprite("images/gui/blackscreen.png")
        self.loading_screen_fade.position = (int(self.center_x), int(self.center_y))
        self.loading_screen_fade.alpha = 0
        self.loading_screen_fade.size = (2500, 2500)
        self.loading_screen.alpha = 0

        self.cursor_texture = arcade.Sprite("images/gui/cursor.png", 0.2)
        self.window.set_mouse_visible(False)
        self.cursor_texture.position = (self.window._mouse_x, self.window._mouse_y)

        self.manager = agui.UIManager()
        self.manager.disable()

        self.background_color = arcade.color.WHITE

        self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

        self.why = arcade.Sprite("images/gui/what_are_you_so_afraid_of.png", center_x=self.window.width/2, center_y=self.window.height/2)
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
        self.loading_screen.alpha = 255
        self.is_loading = True
        def show():
            self.loading_screen_fade.alpha = 255
            time.sleep(0.4)
            for i in range(0, 255):
                if self.is_mouse_pressed:
                    self.loading_screen_fade.alpha = 0
                    break
                self.loading_screen_fade.alpha = 255-i
                time.sleep(0.01)
            time.sleep(1.9)
            self.loading_screen_fade.alpha = 255
            self.loading_screen.alpha = 0
            time.sleep(0.1)
            self.loading_screen_fade.alpha = 0
            self.is_loading = False

        threading.Thread(target=show).start()

    def on_draw(self):
        """
        Render the screen.
        """

        self.clear()
        self.manager.draw()
        arcade.draw_sprite(self.cursor_texture)
        arcade.draw_sprite(self.loading_screen)
        arcade.draw_sprite(self.loading_screen_fade)
        arcade.draw_sprite(self.why)

    def on_update(self, delta_time):
        """
        All the logic to move, and the game logic goes here.
        Normally, you'll call update() on the sprite lists that
        need it.
        """
        if not self.is_loading:
            self.manager.enable()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> EVENT_HANDLE_STATE:
        self.cursor_texture.position = (x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> EVENT_HANDLE_STATE:
        self.is_mouse_pressed = True

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> EVENT_HANDLE_STATE:
        self.is_mouse_pressed = False

    def on_key_press(self, key: int, modifiers: int) -> bool | None:
        if (key == arcade.key.L and modifiers & arcade.key.MOD_SHIFT) and not self.is_loading:
            self.why.alpha = 255
            def wHy():
                time.sleep(10)
                arcade.exit()
            threading.Thread(target=wHy).start()

    def on_hide_view(self):
        self.manager.disable()

    def show_main_windows(self):

        def create_menu_buttons():

            def start_game(event=None):
                self.window.set_fullscreen(False)
                self.window.size = (1920, 1080)
                self.window.set_fullscreen(True)
                self.manager.disable()
                game = GameView()
                self.window.show_view(game)

            def open_saves(event=None):
                settings = SaveMenu()
                self.window.show_view(settings)

            def open_settings(event=None):
                settings = SettingsMenu()
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

class SaveMenu(arcade.View):
    def __init__(self):
        super().__init__()
        self.cursor_texture = arcade.Sprite("images/gui/cursor.png", 0.2)
        self.window.set_mouse_visible(False)
        self.cursor_texture.position = (self.window._mouse_x, self.window._mouse_y)

        saves = sm.save.get_all_saves()
        self.saves = saves + [[None]]*(20 - len(saves))
        self.saves_len = 20

        self.slider: Optional[UISliderVertical]  = None

        self.manager = agui.UIManager()
        self.manager.enable()

        self.background_color = arcade.color.WHITE

        self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)
        self.v_box.center_x = self.window.width/2-300
        self.manager.add(self.v_box)

        self.choise = 0

        self.generate_buttons()

    def generate_buttons(self):

        def return_to_main_menu(event=None):
            game = GameMenu(False)
            self.window.show_view(game)

        def open_save(session_id: str, event=None):
            self.window.set_fullscreen(False)
            self.window.size = (1920, 1080)
            self.window.set_fullscreen(True)
            self.manager.disable()
            game = GameView(session_id)
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
        arcade.draw_sprite(self.cursor_texture)

    def on_update(self, delta_time: float) -> bool | None:
        self.v_box.center_y = self.center_y - ((self.saves_len - self.slider.value) * 220 + 100) + (220 * 10)
        self.choise = int(self.slider.value-1)

        for i in range(self.saves_len):
            self.v_box.children[i].disabled = True if i != self.choise else False

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.cursor_texture.position = (x, y)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> bool | None:
        if (self.saves_len - self.slider.value) + scroll_y >= 0 and (self.saves_len - self.slider.value) + scroll_y < self.saves_len:
            self.slider.value += -scroll_y

class SettingsMenu(arcade.View):
    def __init__(self):
        super().__init__()

        self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=0)
        self.manager = agui.UIManager()
        self.manager.enable()
        self.other_buttons = []

        self.cursor_texture = arcade.Sprite("images/gui/cursor.png", 0.2)
        self.window.set_mouse_visible(False)
        self.cursor_texture.position = (self.window._mouse_x, self.window._mouse_y)

        self.music_volume_slider: Optional[agui.UISlider] = None
        self.sound_volume_slider: Optional[agui.UISlider] = None
        self.voice_volume_slider: Optional[agui.UISlider] = None

        self.background_color = arcade.color.WHITE

        self.show_main_windows()

    def on_draw(self):
        self.clear()
        self.manager.draw()
        arcade.draw_sprite(self.cursor_texture)

    def on_update(self, delta_time: float) -> bool | None:
        if self.window.visible:
            am.music.set_volume(round(self.music_volume_slider.value / 100, 2))
            am.sound.set_volume(round(self.sound_volume_slider.value / 100, 2))
            am.voice.set_volume(round(self.voice_volume_slider.value / 100, 2))

    def show_main_windows(self):

        def create_menu_buttons():
            with open("data.JSON", "r", encoding="UTF-8") as data:
                data = json.load(data)
            volumes = data['options']['volume']

            def return_to_main_menu(event=None):
                game = GameMenu(False)
                self.window.show_view(game)

            return_button = agui.UIFlatButton(
                text="Назад",
                width=300,
                height=50,
                style=STYLE_DEFAULT_BUTTON
            )
            return_button.on_click = return_to_main_menu
            self.v_box.add(return_button)
            self.v_box.add(arcade.gui.UISpace(height=40))

            self.music_volume_label = agui.UILabel(
                "Музыка",
                text_color=arcade.color.BLACK,
                font_name=FONT_NAME
            )
            self.v_box.add(self.music_volume_label)

            self.music_volume_slider = agui.UISlider(
                value=volumes["music"]*100,  # начальное значение
                min_value=0,
                max_value=200,
                width=300,
                height=20
            )
            self.v_box.add(self.music_volume_slider)
            self.v_box.add(arcade.gui.UISpace(height=20))

            self.sound_volume_label = agui.UILabel(
                "Звуки",
                text_color=arcade.color.BLACK,
                font_name=FONT_NAME
            )
            self.v_box.add(self.sound_volume_label)

            self.sound_volume_slider = agui.UISlider(
                value=volumes["sound"]*100,  # начальное значение
                min_value=0,
                max_value=200,
                width=300,
                height=20
            )
            self.v_box.add(self.sound_volume_slider)
            self.v_box.add(arcade.gui.UISpace(height=20))

            self.voice_volume_label = agui.UILabel(
                "Голос",
                text_color=arcade.color.BLACK,
                font_name=FONT_NAME
            )
            self.v_box.add(self.voice_volume_label)

            self.voice_volume_slider = agui.UISlider(
                value=volumes["voice"]*100,  # начальное значение
                min_value=0,
                max_value=200,
                width=300,
                height=20
            )
            self.v_box.add(self.voice_volume_slider)
            self.v_box.add(arcade.gui.UISpace(height=20))

            ui_anchor_layout = arcade.gui.widgets.layout.UIAnchorLayout()
            ui_anchor_layout.add(child=self.v_box, anchor_x="center_x", anchor_y="center_y")

            self.manager.add(ui_anchor_layout)

        create_menu_buttons()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> EVENT_HANDLE_STATE:
        self.cursor_texture.position = (x, y)
        self.window.set_mouse_visible(False)

class Character():
    active_threads = []

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
            start_path = f"./images/characters/{char_id}"

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
        self.lps = lps

        self.action = None
        self.last_text = " "

        self.char_id = char_id

        if self.char_id is not None:
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

        for stop_event, thread in Character.active_threads:
            stop_event.set()
            thread.join()

        dialog_text_text = dialog_text_text_alt.copy()
        cname_text_text = ""


        stop_event = threading.Event()

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

                        if stop_event.is_set():
                            self.action = None
                            return False

                        if not char.startswith("{") and not str(char).endswith("}"):
                            if char != r"\n ":
                                _text.append(char)
                                dialog_text_text[string_index] = replace_char_by_index(dialog_text_text[string_index], i, char)

                        index += 1

                        def talk_sound():
                            def _get_random_sound_path():
                                files = [f"./sounds/character_voice/{self.char_id}/{f}" for f in
                                         os.listdir(f"./sounds/character_voice/{self.char_id}") if
                                         os.path.isfile(os.path.join(f"./sounds/character_voice/{self.char_id}", f))]
                                return random.choice(files)

                            am.play_voice(_get_random_sound_path())
                            return None

                        if ((index % 3 == 0 and char not in (",", ".", "!", "&", "?")) or index == 1) and self.char_id is not None:
                            if os.path.isdir(f"./sounds/character_voice/{self.char_id}"):
                                threading.Thread(target=talk_sound).start()

                        if char == ".":
                            if not fast:
                                time.sleep(0.1)
                        elif char == ",":
                            if not fast:
                                time.sleep(0.05)
                        elif char.startswith("{") and str(char).endswith("}"):
                            char = char[1:][:-1]

                            if char.startswith("w"):
                                i -= 1
                                time.sleep(float(char.split("=")[-1]))
                            if char.startswith("f"):
                                i -= 1
                                fast = True

                        if stop_event.is_set():
                            self.action = None
                            return False

                        if not fast:
                            time.sleep(1 / self.lps)
                    self.action = None
                    return False
                else:
                    if not fast:
                        time.sleep(1 / self.lps)
                    continue

        thread = threading.Thread(target=_talk)
        Character.active_threads = [(stop_event, thread)]
        thread.start()


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
    def get_character(self, char_id: str):
        return self.characters[char_id]



class AudioChannel:
    def __init__(self, default_volume: float=1.0, volume_type: Optional[str] = None):
        self.sound: Optional[arcade.sound.Sound] = None
        self.player: Optional[pyglet.media.player.Player] = None
        self.default_volume: float = default_volume
        self.volume_type: Optional[str] = volume_type

    def play(self, path, loop=False, volume=None, speed=1.0):
        self.sound = arcade.load_sound(path)
        if volume is None:
            volume = self.default_volume

        self.player = self.sound.play(volume=volume, loop=loop, speed=speed)

    def stop(self):
        if self.player:
            self.sound.stop(self.player)
            self.sound = None
            self.player.delete()
            self.player = None

    def pause(self):
        if self.player:
            self.player.pause()

    def resume(self):
        if self.player:
            self.player.play()

    def set_volume(self, vol):
        if self.player is not None:
            self.player.volume = vol
            self.default_volume = vol

        if self.volume_type == "music":
            sm.volume.set_music(vol)
        elif self.volume_type == "sound":
            sm.volume.set_sound(vol)
        elif self.volume_type == "voice":
            sm.volume.set_voice(vol)

    def is_playing(self):
        return bool(self.player and self.player.playing)

class AudioManager:
    def __init__(self):

        self.music = AudioChannel(sm.volume.get_music(), "music")
        self.sound = AudioChannel(sm.volume.get_sound(), "sound")
        self.voice = AudioChannel(sm.volume.get_voice(), "voice")

    def play_music(self, path: str, loop: Optional[bool]=False, volume: float=1.0, effect: Optional[str] = None):

        old_volume = self.music.default_volume
        match effect:
            case "FADE":
                def fadeout_music():
                    self.music.default_volume = 0.0
                    self.music.set_volume(0.0)
                    while self.music.default_volume < old_volume:
                        self.music.default_volume += 0.002
                        self.music.set_volume(self.music.default_volume)
                        time.sleep(0.005)
                    self.music.set_volume(old_volume)
                    return None

                threading.Thread(target=fadeout_music).start()
        self.music.play(path, loop=loop, volume=self.music.default_volume * volume)

    def play_sound(self, path, loop=False, volume=1.0, effect: Optional[str] = None):

        old_volume = self.sound.default_volume
        match effect:
            case "FADE":
                def fadeout_music():
                    int_volume = int(round(self.music.default_volume, 2) * 100)
                    for i in range(int_volume):
                        self.music.default_volume = i/100
                        self.music.set_volume(self.music.default_volume)
                        time.sleep(0.001)
                    self.music.set_volume(old_volume)
                    return None

                threading.Thread(target=fadeout_music).start()
        self.sound.play(path, loop=loop, volume=self.sound.default_volume * volume)

    def play_voice(self, path, loop=False, volume=2.0):
        self.voice.play(path, loop=loop, volume=self.voice.default_volume * volume, speed=random.randint(99, 101) / 100)

    def stop_music(self, effect: Optional[str] = None):
        old_volume = self.music.default_volume
        match effect:
            case "FADE":
                def fadeout_music():
                    int_volume = int(round(self.music.default_volume, 2)*100)
                    for i in range(int_volume):
                        self.music.default_volume = round((int_volume - i)/100, 2)
                        self.music.set_volume(self.music.default_volume)
                        time.sleep(0.01)
                    self.music.stop()
                    self.music.set_volume(old_volume)
                    return None
                threading.Thread(target=fadeout_music).start()

            case _:
                self.music.stop()

    def stop_sound(self, effect: Optional[str] = None):
        old_volume = self.sound.default_volume
        match effect:
            case "FADE":
                def fadeout_music():
                    int_volume = int(round(self.sound.default_volume, 2) * 100)
                    for i in range(int_volume):
                        self.sound.default_volume = round((int_volume - i) / 100, 2)
                        self.sound.set_volume(self.sound.default_volume)
                        time.sleep(0.005)
                    self.sound.stop()
                    self.sound.set_volume(old_volume)
                    return None

                threading.Thread(target=fadeout_music).start()
            case _:
                self.sound.stop()

    def stop_voice(self):
        self.voice.stop()


class Saves_manager:
    def  __init__(self):

        if not os.path.exists("./data.JSON"):
            with open("./data.JSON",  "w", encoding="UTF-8") as file:
                data = {
                    "saves": {},
                    "persistent" : {},
                    "options": {
                        "volume": {
                            "music": 1.0,
                            "sound": 1.0,
                            "voice": 1.0
                        }
                    }
                }
                json.dump(data, file, indent=4, ensure_ascii=False)

        self.defines = {}

    class persistent:
        @staticmethod
        def get_persistent(name: str):
            with open("./data.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            return file["persistent"].get(name, None)

        @staticmethod
        def set_persistent(name: str, data: any):
            with open("./data.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["persistent"][name] = data
            with open("./data.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

    class volume:
        @staticmethod
        def set_music(value: float):
            with open("./data.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["options"]["volume"]["music"] = value
            with open("./data.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

        @staticmethod
        def set_sound(value: float):
            with open("./data.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["options"]["volume"]["sound"] = value
            with open("./data.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

        @staticmethod
        def set_voice(value: float):
            with open("./data.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["options"]["volume"]["voice"] = value
            with open("./data.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)


        @staticmethod
        def get_music():
            with open("./data.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            return file["options"]["volume"].get("music", None)

        @staticmethod
        def get_sound():
            with open("./data.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            return file["options"]["volume"].get("sound", None)

        @staticmethod
        def get_voice():
            with open("./data.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            return file["options"]["volume"].get("voice", None)

    class save:

        @staticmethod
        def create_save(session_id: str, defines: dict, position: int, label: str, scene: dict):
            with open("./data.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["saves"][session_id] = {
                "position" : position,
                "label" : label,
                "defines" : defines,
                "scene" : scene
            }
            with open("./data.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

        @staticmethod
        def get_save(session_id: str) -> dict:
            with open("./data.JSON", "r", encoding="UTF-8") as file:
                file_data = dict(json.load(file))
            return file_data["saves"][session_id]

        @staticmethod
        def get_all_saves() -> dict:
            with open("./data.JSON", "r", encoding="UTF-8") as file:
                file_data = dict(json.load(file))
            return [[i, o] for i, o in file_data["saves"].items()]

def main():
    window = arcade.Window(width=1024, height=786, title=f"{WINDOW_TITLE} | {splash}", resizable=False)
    game = GameMenu()
    window.show_view(game)
    arcade.run()

if __name__ == "__main__":
    sm = Saves_manager()
    am = AudioManager()
    lc = ListCharacters()
    main()