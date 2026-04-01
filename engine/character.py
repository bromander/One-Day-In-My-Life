from typing import Optional, Literal, Union
from arcade import color, load_sound, Sprite
from .saves import Saves_manager
from .audio import AudioManager
from .waiter import Waiter
from .files_manager import FilesManager
from arcade import color
import os
import random
import re

class Attributes:
    def __init__(self):
        self.character_name = ""
        self.character_text = [""]

        self.character_name_colour = color.BLACK
        self.character_text_colour = color.BLACK

        self.text_anchor = "left"

class Character:

    def __init__(self,
                 sm : Saves_manager,
                 am : AudioManager,
                 fm : FilesManager,
                 attributes: Attributes,
                 wait_trigger : Waiter,
                 text_anchor,
                 name: str,
                 char_id: Optional[str] = None,
                 colour: str = "",
                 name_colour: str = "",
                 c_scale: float = 1.0,
                 text_anch: Union[int, float, Literal["left", "right", "center"]] = "left",
                 lps: int = 60
                 ) -> None:

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

        def find_sounds():
            sounds = []
            if char_id is not None:
                if os.path.isfile((f"./game/sounds/voice/{char_id}")):
                    for f in os.listdir(f"./game/sounds/voice/{char_id}"):
                        if os.path.isfile(os.path.join(f"./game/sounds/voice/{char_id}", f)):
                            sounds.append(load_sound(f"./game/sounds/voice/{char_id}/{f}"))
            self.talk_sounds = sounds
            return sounds

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
                return color.WHITE

        self.attributes = attributes

        self.text_anchor = text_anchor

        self.sm = sm
        self.am = am
        self.fm = fm

        self.wait_trigger = wait_trigger

        self.c_name = name
        self.colour = hex_to_rgb(colour)
        self.name_colour = hex_to_rgb(name_colour)
        self.c_scale = c_scale
        self.lps = lps
        self.action = None
        self.last_text = " "

        self.talk_sounds = []
        find_sounds()

        self.char_id = char_id

        self.text_anch = text_anch

    def talk(self, text: str):
        """
        Форматирует текст и создаёт генератор, который проигрывает речь персонажа.
        :param text: Речь персонажа
        :return: Генератор
        """

        def replace_char_by_index(text, index, new_char):
            if index < 0 or index >= len(text):
                return text
            return text[:index] + new_char + text[index + 1:]

        now_lps = self.lps * (self.lps / self.sm.Volume.get_other("lps"))

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


        self.attributes.text_anchor = self.text_anch

        self.am.stop_voice()

        self.attributes.character_text_colour = self.colour
        self.attributes.character_name_colour = self.name_colour

        self.action = None

        self.attributes.character_text = dialog_text_text_alt.copy()
        self.attributes.character_name = ""

        def _talk(now_lps):
            string_index = 0
            fast = False

            self.action = "talk"

            while True:
                self.attributes.text_anchor = self.text_anchor
                self.attributes.character_name = self.c_name

                i = -1
                if not self.wait_trigger:
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

                        self.attributes.character_name = self.c_name

                        if not char.startswith("{") and not str(char).endswith("}"):
                            if char != r"\n ":
                                _text.append(char)
                                self.attributes.character_text[string_index] = replace_char_by_index(self.attributes.character_text[string_index], i, char)

                        index += 1

                        if ((index % 4 == 0 and char not in (",", ".", "!", "&", "?")) or index == 1) and self.char_id is not None:
                            if os.path.isfile(f"./game/sounds/voice/{self.char_id}"):
                                self.am.play_voice(random.choice(self.talk_sounds))

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

    def show(self, sprite: str) -> Sprite:
        """
        Возвращает спрайт персонажа
        :param sprite: Название спрайта
        :raises FileNotFoundError: Если спрайт не был найден
        """
        textures = self.fm.get_character_textures(sprite)

        if sprite not in textures:
            raise FileNotFoundError(f"Character sprite \"{sprite}\" was not found in \"./game/images/characters/{self.char_id}/{sprite}\"")

        now_sprite = Sprite(textures[sprite])
        return now_sprite

class ListCharacters:
    def __init__(self,
                 sm : Saves_manager,
                 am : AudioManager,
                 fm : FilesManager,
                 wait_trigger: Waiter) -> None:
        """
        Хранит в себе список всех персонажей
        """

        self.attributes = Attributes()

        _Character = lambda name, char_id = None, colour = "", name_colour = "", c_scale = 1.0, text_anch= "left", lps = 60: Character(
            sm, am, fm, self.attributes, wait_trigger,
            name=name, char_id=char_id, colour=colour, name_colour=name_colour, c_scale=c_scale, text_anchor=text_anch, lps=lps
        )

        self.characters = {
            "narr" : _Character(" ", None, text_anch="center"),
            "unk1" : _Character("???", None, text_anch="center", colour="#f0c4c0"),
            "unk2" : _Character("???", None, text_anch="center", colour="#d5dbf0"),
            "shak" : _Character("Жаклин", "shak", "#f5a889", "#f0855b"),
            "masorubka" : _Character("Кассир", "masorubka", "#E0FFFF", "#7FFFD4"),
            "ed" : _Character("Сосед", "ed", "#FFDEAD", "#FFDEAD"),
            "oz": _Character("Ф. ОЗИНАД", "oz", "#12d3da"),
        }

    def __getitem__(self, item) -> dict[str : Character]:
        return self.characters[item]