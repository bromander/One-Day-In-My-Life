import arcade
from pyglet.event import EVENT_HANDLE_STATE
from pyglet.graphics import Batch
from arcade import gui as agui
from typing import Optional, List, Tuple
import threading
import time
import re
import os
import json
import random

from lore_viewer import Wwl

with open("./other/splashes.json", "r", encoding="UTF-8") as splashes:
    splashes = json.load(splashes)
splash = str(random.choice(splashes))
if splash.startswith(">"):
    splash = splash.format(username=str(os.getenv("USERNAME") or os.getenv("USER")))[1:]

wwl = Wwl()

text_anchor = "left"

WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080

arcade.load_font("fonts/Kurale-Regular.ttf")

wait_trigger: bool = False

WINDOW_TITLE = f"Game name"
TEXT_SPEED = 40
last_talk = threading.Event()

dialog_text_text: list[str] = []
cname_text_text = ""

cname_text_colour = arcade.color.BLACK
dialog_text_colour = arcade.color.BLACK

class GameView(arcade.View):

    def __init__(self):
        super().__init__()
        self.scene = arcade.Scene()

        self.cursor_texture = arcade.Sprite("images/gui/cursor.png", 0.2)
        self.window.set_mouse_visible(False)

        self.background_color = arcade.color.WHITE

        self.dialog_window = None
        self.dialog_text_batch = Batch()
        self.dialog_texts: list = []
        self.cname_text: Optional[arcade.Text] = None

        self.characters_sprites: dict[str : arcade.Sprite] = {}

        self.scene.add_sprite_list("bg")
        self.scene.add_sprite_list("characters")
        self.scene.add_sprite_list("fade")
        self.scene.add_sprite_list("gui")

        self.is_mouse_pressed = False

        self.last_text = " "

        def create_dialog_window():
            texture = arcade.load_texture("images/gui/dialog_window.png")

            self.dialog_window = arcade.Sprite(
                texture,
                scale=6 * min(self.width / WINDOW_WIDTH, self.height / WINDOW_HEIGHT),
                center_x=self.width * 0.5,
                center_y=self.height * 0.13
            )
            self.scene.add_sprite("gui", self.dialog_window)

        def create_dialog_fade():
            texture = arcade.load_texture("images/gui/blackscreen.png")

            fade = arcade.Sprite(
                texture,
                scale=50,
                center_x=self.width * 0.5,
                center_y=self.height * 0.5
            )
            fade.alpha = 0
            self.scene.add_sprite("fade", fade)

        create_dialog_fade()
        create_dialog_window()

        time.sleep(2)

        self.start_trigger: bool = True

        self.talk_manager()


    def talk_manager(self):

        now = wwl.get_thing()
        res = self.talk(now)


        match res:
            case "NEXT":
                self.talk_manager()
            case "REPEAT":
                #self.talk(now)
                return None
            case "END":
                return None



    def talk(self, now):
        global dialog_text_text, cname_text_text

        while True:

            if now is None:
                return None


            match now['action']:

                case "SAY":
                    self.dialog_texts = []

                    self.start_trigger = False
                    pon = lc.get_character(now["character"]).talk(str(now["args"]))

                    return "END"

                case "PLAY":
                    match now["play_what"]:
                        case "MUSIC":
                            if len(now["args"]) < 2:
                                now["args"].append(1)
                            if len(now["args"]) < 3:
                                now["args"].append(True)

                            am.play_music(f"music/{now["args"][0]}", bool(now["args"][2]), float(now["args"][1]))

                        case "SOUND":
                            if len(now["args"]) < 2:
                                now["args"].append(1)
                            if len(now["args"]) < 3:
                                now["args"].append(False)

                            am.play_sound(f"sounds/{now["args"][0]}", bool(now["args"][2]), float(now["args"][1]))
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
                    texture = arcade.load_texture(f"images/scenes/{now['filename']}")
                    self.dialog_window = arcade.Sprite(
                        texture,
                        scale=float(now['scale']),
                        center_x=self.width * 0.5,
                        center_y=self.height * 0.5
                    )
                    self.scene.add_sprite("bg", self.dialog_window)
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
                                        if not wait_trigger:
                                            wait_trigger = True
                                        break

                                    progress = elapsed / duration
                                    alpha = 255 - int(progress * 255)

                                    if not wait_trigger:
                                        wait_trigger = True

                                    self.scene["fade"][0].alpha = alpha

                                    time.sleep(0.01)
                                wait_trigger = False

                            threading.Thread(target=editing_alpha).start()
                    return "NEXT"

                case "JUMP":

                    wwl.pose = 0
                    wwl.label = f"label {now["label"]}"

                    return "NEXT"

                case "WAIT":

                    def _waiter():
                        global wait_trigger

                        wait_trigger = True
                        time.sleep(now["time"])
                        wait_trigger = False

                    threading.Thread(target=_waiter).start()
                    return "NEXT"

                case "END":
                    self.window.close()

                    wwl.label = "label main"
                    wwl.pose = 0

                    dialog_text_text = [" "]
                    cname_text_text = ""

                    game = GameMenu(width=1024, height=786, title=f"{WINDOW_TITLE} | {splash}")
                    game.run()
                    return "END"


                case _:
                    return None

    def on_draw(self):
        """
        Render the screen.
        """

        if not self.start_trigger:
            self.clear()
            self.scene.draw()
            self.create_main_windows()
            self.dialog_text_batch.draw()
            arcade.draw_sprite(self.cursor_texture)


    def on_update(self, delta_time):
        """
        All the logic to move, and the game logic goes here.
        Normally, you'll call update() on the sprite lists that
        need it.
        """
        self.scene.update(delta_time)
        #self

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE or key == arcade.key.ENTER or key == arcade.key.ENTER:
            if not wait_trigger:
                self.talk_manager()

    def on_mouse_release(self, x, y, button, modifiers):
        self.is_mouse_pressed = False
        if int(button) == 1:
            if not wait_trigger:
                self.talk_manager()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:
        self.is_mouse_pressed = True

    def create_main_windows(self):

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
                            font_name="Kurale",
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
                            font_name="Kurale",
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
                            font_name="Kurale",
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
                font_name="Kurale"
            )
            self.cname_text.draw()

        create_dialog_text()
        create_cname_text()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> EVENT_HANDLE_STATE:
        self.cursor_texture.position = (x, y)

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


class GameMenu(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width=width, height=height, title=title, resizable=False)


        self.loading_screen = arcade.Sprite("images/gui/JE3000_logo-export.png", 1)
        self.loading_screen.position = (int(self.center_x), int(self.center_y))
        self.loading_screen_fade = arcade.Sprite("images/gui/blackscreen.png")
        self.loading_screen_fade.position = (int(self.center_x), int(self.center_y))
        self.loading_screen_fade.alpha = 0

        self.cursor_texture = arcade.Sprite("images/gui/cursor.png", 0.2)
        self.set_mouse_visible(False)

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        self.background_color = arcade.color.WHITE

        self.v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)

        self.show_main_windows()

        self.is_mouse_pressed = False

        am.stop_music()
        am.stop_voice()
        am.stop_sound()

        self.show_ls()


    def show_ls(self):

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

        threading.Thread(target=show).start()


    def on_draw(self):
        """
        Render the screen.
        """

        self.clear()
        self.manager.draw()
        arcade.draw_sprite(self.cursor_texture)
        arcade.draw_sprite(self.loading_screen)
        arcade.draw_sprite(self.loading_screen_fade, pixelated=True)



    def on_update(self, delta_time):
        """
        All the logic to move, and the game logic goes here.
        Normally, you'll call update() on the sprite lists that
        need it.
        """
        pass

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> EVENT_HANDLE_STATE:
        self.cursor_texture.position = (x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> EVENT_HANDLE_STATE:
        self.is_mouse_pressed = True

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> EVENT_HANDLE_STATE:
        self.is_mouse_pressed = False

    def on_hide_view(self):
        self.manager.disable()

    def show_main_windows(self):

        def create_menu_buttons():

            def start_game(event=None):
                self.close()
                window = arcade.Window(1920, 1080, f"{WINDOW_TITLE} | {splash}", resizable=False, fullscreen=True)
                game = GameView()
                window.show_view(game)
                arcade.run()

            start_button = arcade.gui.widgets.buttons.UIFlatButton(
                text="Начать игру",
                width=200
            )
            start_button.on_click = start_game
            self.v_box.add(start_button)

            settings_button = arcade.gui.widgets.buttons.UIFlatButton(
                text="Настройки",
                width=200
            )
            settings_button.on_click = lambda event: self.show_view(GameView())
            self.v_box.add(settings_button)

            exit_button = arcade.gui.widgets.buttons.UIFlatButton(
                text="Выход",
                width=200
            )
            exit_button.on_click = lambda event: arcade.exit()
            self.v_box.add(exit_button)

            ui_anchor_layout = arcade.gui.widgets.layout.UIAnchorLayout()
            ui_anchor_layout.add(child=self.v_box, anchor_x="center_x", anchor_y="center_y")

            self.manager.add(ui_anchor_layout)

        create_menu_buttons()

class SettingsMenu(arcade.Window):
    pass


class Work_with_jpy:
    def __init__(self):
        self.file_format = ".jpy"
        self.start_label = "main"

class Character():
    active_threads = []

    def __init__(self, name, char_id: Optional[str] = None, colour: str = "", name_colour: str = "", c_scale: float = 1.0, text_anch: str = "left"):
        super().__init__()

        def hex_to_rgb(hex_color: str):
            if hex_color:
                hex_color = hex_color.lstrip("#")
                if len(hex_color) not in (6, 8):
                    raise ValueError("Hex должен быть в формате RRGGBB или RRGGBBAA")

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
                            results[file.split(".")[0]] = full_path.replace("\\", "/")

            return results


        self.c_name = name
        self.colour = hex_to_rgb(colour)
        self.name_colour = hex_to_rgb(name_colour)
        self.c_scale = c_scale

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
                            return False

                        if not char.startswith("{") and not str(char).endswith("}"):
                            if char != r"\n ":
                                _text.append(char)
                                dialog_text_text[string_index] = replace_char_by_index(dialog_text_text[string_index], i, char)
                                print("\n")
                                print(i)
                                print(char)
                                print(dialog_text_text)
                                print(dialog_text_text_alt)

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
                            return False

                        if not fast:
                            time.sleep(1 / TEXT_SPEED)
                    self.action = None
                    return False
                else:
                    if not fast:
                        time.sleep(1 / TEXT_SPEED)
                    continue

        thread = threading.Thread(target=_talk)
        Character.active_threads = [(stop_event, thread)]
        thread.start()


    def show(self, sprite: str, scale: Optional[int] = None) -> arcade.Sprite:
        if scale is None:
            scale = self.c_scale
        now_sprite = arcade.Sprite(self.sprites[sprite], scale=scale)
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
    def __init__(self, default_volume=1.0):
        self.sound = None
        self.player = None
        self.default_volume = default_volume

    def play(self, path, loop=False, volume=None, speed=1.0):
        self.sound = arcade.load_sound(path)
        if volume is None:
            volume = self.default_volume

        self.player = self.sound.play(volume=volume, loop=loop, speed=speed)

    def stop(self):
        if self.player:
            self.player.pause()
            self.player.delete()
            self.player = None

    def pause(self):
        if self.player:
            self.player.pause()

    def resume(self):
        if self.player:
            self.player.play()

    def set_volume(self, vol):
        if self.player:
            self.player.volume = vol

    def is_playing(self):
        return bool(self.player and self.player.playing)

class AudioManager:
    def __init__(self):
        self.music = AudioChannel()
        self.sound = AudioChannel()
        self.voice = AudioChannel()

    # Удобные сокращения
    def play_music(self, path, loop=False, volume=1.0):
        self.music.play(path, loop=loop, volume=volume)

    def play_sound(self, path, loop=False, volume=1.0):
        self.sound.play(path, loop=loop, volume=volume)

    def play_voice(self, path, loop=False, volume=2.0):
        self.voice.play(path, loop=loop, volume=volume, speed=random.randint(99, 101) / 100)

    def stop_music(self, effect: Optional[str] = None):
        if effect is not None:
            match effect:
                case "FADE":
                    def fadeout_music():
                        while self.music.default_volume >= 0.0:
                            self.music.default_volume -= 0.002
                            self.music.set_volume(self.music.default_volume)
                            time.sleep(0.005)
                        self.music.stop()
                        return None
                    threading.Thread(target=fadeout_music).start()

                case _:
                    self.music.stop()
        else:
            self.music.stop()

    def stop_sound(self, effect: Optional[str] = None):
        if effect is not None:
            match effect:
                case "FADE":
                    for i in range(int(self.sound.default_volume*10), 0):
                        self.sound.set_volume(i)
                case N:
                    print(N)
        self.sound.stop()

    def stop_voice(self):
        self.voice.stop()


am = AudioManager()

def main():
    game = GameMenu(width=1024, height=786, title=f"{WINDOW_TITLE} | {splash}")

    game.run()



if __name__ == "__main__":
    lc = ListCharacters()
    main()