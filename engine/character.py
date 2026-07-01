from typing import Optional, Literal, Union
from arcade import color, Sprite, Texture
import os
import random
import re
import json5

from .globals import g


class Attributes:
    def __init__(self):
        self.character_name = ""
        self.character_text = [""]

        self.character_name_colour = color.BLACK
        self.character_text_colour = color.BLACK

        self.text_anchor = "left"

    def reset(self):
        self.character_name = ""
        self.character_text = [""]

        self.character_name_colour = color.BLACK
        self.character_text_colour = color.BLACK

        self.text_anchor = "left"


class Character:
    def __init__(
        self,
        name: str,
        char_id: Optional[str] = None,
        colour: str = "",
        name_colour: str = "",
        c_scale: float = 1.0,
        text_anchor: Union[int, float, Literal["left", "right", "center"]] = "left",
        lps: int = 60,
    ) -> None:
        """
        Создаёт персонажа.
        :param name: Имя персонажа
        :param char_id: Айди персонажа (должно совпадать с его папкой, и названиями спрайтов)
        :param colour: Цвет текста речи (в HEX формате)
        :param name_colour: Цвет текста имени (в HEX формате)
        :param c_scale: Размер спрайта
        :param text_anchor: Положение текста на экране (left, right, center)/ int - координата X / float - координата (width * text_anch)
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
                return color.WHITE

        self.attributes = g.attributes

        self.sm = g.sm
        self.am = g.am
        self.fm = g.fm

        self.c_name = name
        self.colour = hex_to_rgb(colour)
        self.name_colour = hex_to_rgb(name_colour)
        self.c_scale = c_scale
        self.lps = lps
        self.action = None
        self.last_text = " "

        self.talk_sounds = []
        # find_sounds()

        self.char_id = char_id

        self.pattern = re.compile(r"\\n |\{[^}]*\}|\S|\s")

        self.text_anchor = text_anchor

    def _process_text(self, text, pattern, placeholder):
        matches = re.findall(pattern, text)

        result = []
        current_parts = []
        line_index = 0

        for char in matches:
            if char == "\n":
                result.append("".join(current_parts))
                current_parts = []
                line_index += 1
                continue

            if char.startswith("{") and char.endswith("}"):
                current_parts.append(char)
                continue

            if char != " ":
                current_parts.append(placeholder)
            else:
                current_parts.append(" ")

        if current_parts:
            result.append("".join(current_parts))

        return result

    def talk(self, text: str):
        """
        Форматирует текст и создаёт генератор, который проигрывает речь персонажа.
        :param text: Речь персонажа
        :return: Генератор
        """

        def replace_char_by_index(text, index, new_char):
            return text if index < 0 else text[:index] + new_char + text[index + 1:]

        now_lps = self.lps * self.sm.Volume.lps

        dialog_text_text_alt = self._process_text(text, self.pattern, g.UNSEEN_TEXT_PLACEHOLDER)

        self.attributes.text_anchor = self.text_anchor

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

            self.attributes.character_text = dialog_text_text_alt.copy()
            self.attributes.text_anchor = self.text_anchor
            self.attributes.character_name = self.c_name

            g.main.characters_texts_manager.prepare(self.attributes.character_text)

            while True:

                i = -1
                self.last_text = text

                _text = []
                index = 0
                for char in re.findall(self.pattern, repr(text).strip(r"'")):
                    i += 1

                    if char == r"\n ":
                        string_index += 1
                        i = -1
                        _text = []
                        continue

                    if not char.startswith("{") and not char.endswith("}"):
                        if char != r"\n ":
                            _text.append(char)
                            self.attributes.character_text[string_index] = (
                                replace_char_by_index(
                                    self.attributes.character_text[string_index],
                                    i,
                                    char,
                                )
                            )

                    elif char.startswith("{") and char.endswith("}") and char not in ("{w}", "{f}"):
                        i += len(char)-1
                    index += 1

                    if (
                        (index % 4 == 0 and char not in (",", ".", "!", "&", "?"))
                        or index == 1
                    ) and self.char_id is not None:
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

                    elif char in ("{w}", "{f}"):
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

        return _talk(now_lps)

    def show(self, sprite: str) -> Sprite:
        """
        Возвращает спрайт персонажа
        :param sprite: Название спрайта
        :raises FileNotFoundError: Если спрайт не был найден
        """
        textures = self.fm.get_character_textures(sprite)

        if sprite not in textures:
            raise FileNotFoundError(
                f'Character sprite "{sprite}" was not found in "./game/images/characters/{self.char_id}/{sprite}"'
            )

        texture: Texture = textures[sprite]
        sprite = Sprite(texture)
        sprite.scale = self.c_scale

        return sprite


class ListCharacters:
    def __init__(self) -> None:
        """
        Хранит в себе всех персонажей
        """

        self.characters = {"narr": Character(" ", None, text_anchor="center")}
        self.characters.update(self._init_characters())

    def __getitem__(self, item) -> dict[str:Character]:
        return self.characters[item]

    def _init_characters(self):
        """
        Парсит файл characters.json5
        """

        if "characters.json5" not in os.listdir("./game/other/"):
            raise FileNotFoundError(
                "Файл персонажей game/other/characters.json5 не найден!"
            )

        with open("./game/other/characters.json5", "r", encoding="UTF-8") as file:
            characters: dict[str:dict] = json5.load(file)

        characters_data = {
            char_name: Character(
                data.get("name", " "),
                data.get("char_id", None),
                data.get("colour", None),
                data.get("name_colour", None),
                data.get("c_scale", 1.0),
                data.get("text_anchor", "left"),
                data.get("lps", 60),
            )
            for char_name, data in characters.items()
        }

        return characters_data
