import sys
import time, datetime
from io import StringIO
import re
from sqlite3.dbapi2 import paramstyle
from typing import Optional, Literal, Tuple, Union
import PIL
from arcade import Sprite

from .saves import Saves_manager
from .Exceptions import ActionNotFoundError, ChannelDoesNotExistError

class Namespace:
    def __init__(self, GameView, Views, ListCharacters, Wwl, AudioManager, Wait_trigger, SavesManager) -> None:
        """
        Отвечает за работу со всеми функциями, используемыми в сценариях.
        :param GameView: Объект класса GameView
        :param ListCharacters: Объект класса ListCharacters
        :param Wwl: Объект класса Wwl
        :param AudioManager: Объект класса AudioManager
        :param Wait_trigger: Одноимённый объект класса Waiter
        """

        self.Game_view = GameView
        self.ListCharacters = ListCharacters
        self.Wwl = Wwl
        self.AudioManager = AudioManager
        self.Wait_trigger = Wait_trigger
        self.SavesManager = SavesManager

        self.NAMESPACE = {
            "Data" : self.Data(GameView, ListCharacters, Wwl, AudioManager),
            "Persistent": self.Persistent(SavesManager),
            "Define": self.Define(),
            "Scene": self.Scene(GameView, ListCharacters, Wwl, Wait_trigger, SavesManager),
            "Screen" : self.Screen(GameView, Views),
            "Audio": self.Audio(GameView, AudioManager),
            "Lore": self.Lore(GameView, Wwl),
            "SpriteEffects": self.SpriteEffects(),
            "wait" : lambda duration: self.wait(duration),
            "talk" : self.talk,
            "end" : lambda: self.end(self.Wwl, self.Game_view)
        }
        self.returning = None

    def __getitem__(self, item):
        return self.NAMESPACE[item]

    def execute(self, command: str) -> str:
        """
        Выполняет код в своём окружении
        :param command: Строка с кодом
        """
        try:
            exec(command, self.NAMESPACE)
        except SyntaxError as e:
            raise SyntaxError(
                f"{e}:\n{"\n    ".join([str(num) + " " + str(i) for num, i in enumerate(str(command).split("\n"))])}")


        old_ret = self.returning
        self.returning = None
        return old_ret

    def get(self, key: str, default: any = None) -> any:
        return self.NAMESPACE.get(key, default)

    class Persistent:
        def __init__(self, sm: Saves_manager):
            """
            Отвечает за работу с переменными, которые сохраняются между сессиями
            """
            object.__setattr__(self, 'sm', sm)

        def __setattr__(self, name, value):
            self.sm.Persistent.set_persistent(name, value)
            object.__setattr__(self, name, value)

        def __getattribute__(self, item):
            if item == 'sm':
                return object.__getattribute__(self, item)

            try:
                return self.sm.Persistent.get_persistent(item)
            except KeyError:
                raise AttributeError(f"'{type(self).__name__}' object has no attribute '{item}'")

        def __delattr__(self, item):
            self.sm.Persistent.del_persistent(item)
            object.__delattr__(self, item)

    class Define:
        def __init__(self):
            """
            Отвечает за работку с переменными, которые сохраняются со всеми сохранениями
            """
            super().__setattr__('defines', {})

        def __setattr__(self, name, value):
            if name == 'defines':
                super().__setattr__(name, value)
            else:
                defines = super().__getattribute__('defines')
                defines[name] = value

        def __getattribute__(self, name):
            if name == 'defines':
                return super().__getattribute__(name)
            try:
                return super().__getattribute__(name)
            except AttributeError:
                defines = super().__getattribute__('defines')
                if name in defines:
                    return defines[name]
                raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        def __delattr__(self, name):
            if name == 'defines':
                super().__delattr__(name)
            else:
                defines = super().__getattribute__('defines')
                if name in defines:
                    del defines[name]
                else:
                    try:
                        super().__delattr__(name)
                    except AttributeError:
                        pass

    class Data:
        '''
        Предоставляет доступ к основным классам движка
        '''

        def __init__(self, Game_view, ListCharacters, Wwl, AudioManager):
            self.session_id = Game_view.session_id
            self.height = Game_view.height
            self.width = Game_view.width
            self.Window = Game_view.window
            self.Game_view = Game_view
            self.ListCharacters = ListCharacters
            self.Wwl = Wwl
            self.AudioManager = AudioManager
            self.PIL = PIL

        def format_time_seconds(self):
            seconds = time.time()

            dt = datetime.datetime.fromtimestamp(seconds)

            days = {
                0: "понедельник",
                1: "вторник",
                2: "среда",
                3: "четверг",
                4: "пятница",
                5: "суббота",
                6: "воскресенье"
            }

            months = {
                1: "января",
                2: "февраля",
                3: "марта",
                4: "апреля",
                5: "мая",
                6: "июня",
                7: "июля",
                8: "августа",
                9: "сентября",
                10: "октября",
                11: "ноября",
                12: "декабря"
            }

            weekday = days[dt.weekday()]
            day = dt.day
            month = months[dt.month]

            return weekday, day, month

        def create_stamp(self):
            def stamp():
                yield
            self.Game_view.actions.active_generators.add_generator("continuous", stamp(), "stamp")

    class Scene:
        def __init__(self, Game_view, ListCharacters, Wwl, Wait_trigger, sm: Saves_manager) -> None:
            """
            Отвечает за работу с игровой сценой
            :param Game_view: Объект класса Game_view
            :param ListCharacters: Объект класса ListCharacters
            :param Wwl: Объект класса Wwl
            """
            self.Game_view = Game_view
            self.ListCharacters = ListCharacters
            self.Wwl = Wwl
            self.Wait_trigger = Wait_trigger
            self.sm = sm


        @property
        def character_slice(self):
            return self.Game_view.scene.character_slice

        @character_slice.setter
        def character_slice(self, value):
            self.Game_view.scene.set_characters_slice(value)

        def _get_norm(self,
                      at: Optional[Union[Literal["left", "right", "center"], tuple[int, int], tuple[float, float]]],
                      sprite_name: str):

            screen_width = self.Game_view.width
            screen_height = self.Game_view.height

            x_norm, y_norm = 0, 0.4

            if sprite_name in self.Game_view.scene["sprites"]:
                sprite = self.Game_view.scene["sprites"][sprite_name]
            else:
                sprite = Sprite(center_x=screen_width * x_norm, center_y=screen_height * y_norm)

            match at:
                case "center":
                    x_norm = 0.5
                case "left":
                    x_norm = 0.2
                case "right":
                    x_norm = 0.8
                case _ if isinstance(at, tuple) and len(at) == 2:

                    if at[0] == -1:
                        x_norm = sprite.position[0] / screen_width
                    elif isinstance(at[0], int):
                        x_norm = at[0] / screen_width

                    elif isinstance(at[0], float):
                        if 0 <= at[0] <= 1:
                            x_norm = at[0]
                        else:
                            x_norm = at[0] / screen_width


                    if at[1] == -1:
                        y_norm = sprite.position[1] / screen_height

                    elif isinstance(at[1], int):
                            y_norm = at[1] / screen_height

                    elif isinstance(at[1], float):
                        if 0 <= at[1] <= 1:
                            y_norm = at[1]
                        else:
                            y_norm = at[1] / screen_height

            return x_norm, y_norm

        def _get_size(self, size: Optional[Union[int, float, Tuple[int], Tuple[float]]], sprite_size: tuple) -> tuple:
            if size is None:
                return sprite_size

            if isinstance(size, (int, float)):
                if isinstance(size, float):
                    return (int(sprite_size[0] * size), int(sprite_size[1] * size))
                else:
                    return (size, size)

            if isinstance(size, tuple):
                width = None
                height = None

                if len(size) >= 1:
                    if isinstance(size[0], float):
                        width = int(sprite_size[0] * size[0])
                    else:
                        width = size[0]

                if len(size) >= 2:
                    if isinstance(size[1], float):
                        height = int(sprite_size[1] * size[1])
                    else:
                        height = size[1]

                if height is None and width is not None:
                    ratio = width / sprite_size[0]
                    height = int(sprite_size[1] * ratio)

                return (width, height)

            return sprite_size


        def add_sprite(self, filename: str,
                       at: Optional[Union[Literal["left", "right", "center"], tuple[int, int], tuple[float, float]]] = None,
                       size: Optional[Union[tuple[int, int], int]] = None,
                       angle: int = 0.0,
                       effect = None,
                       stream: Literal["consistently", "together"] = "consistently") -> None:
            """
            Добавляет спрайт на сцену
            :param filename: Название спрайта
            :param at: Позиция
            :param size: Размер спрайта
            :param angle: поворот спрайта
            :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Сonsistently: Обновляет только первый генератор в списке, пока он не завершится
            """

            sprite: Sprite = self.Game_view.scene.get_sprite(filename)
            if sprite is None:
                raise FileNotFoundError(f"File {filename} not found!")

            sprite.size = self._get_size(size, sprite.size)

            if angle is not None:
                sprite.angle = angle

            screen_width = self.Game_view.width
            screen_height = self.Game_view.height

            if at is not None:

                x_norm, y_norm = self._get_norm(at, filename)

                sprite.center_x = screen_width * x_norm
                sprite.center_y = screen_height * y_norm

            else:
                sprite.center_x = screen_width // 2
                sprite.center_y = screen_height * 0.2

            if effect is not None:
                sprite.alpha = 0
            else:
                sprite.alpha = 255

            def target():
                self.Game_view.scene.add_sprite("sprites", filename, sprite)
                yield

            self.Game_view.actions.active_generators.add_generator(stream, target(), "show_sprite")
            if effect is not None:
                self.Game_view.actions.active_generators.add_generator(
                    stream,
                    effect.effect(filename, "sprites", self.Game_view, self.sm),
                    "show_sprite_effect"
                )

        def hide_sprite(self, filename: str,
                        effect = None,
                        stream: Literal["consistently", "together"] = "consistently") -> None:
            """
            Удаляет спрайт со сцены
            :param filename: Название файла
            :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится
            """

            def target():
                self.Game_view.scene.delete_sprite("sprites", filename)
                yield

            if effect is not None:
                self.Game_view.actions.active_generators.add_generator(
                    stream,
                    effect.effect(filename, "sprites", self.Game_view, self.sm, 0),
                    "hide_sprite_effect"
                )
            self.Game_view.actions.active_generators.add_generator(stream, target(), "hide_sprite")


        def show_character(self, character: str,
                        at: Optional[Union[Literal["left", "right", "center"], tuple[int, int], tuple[float, float]]] = None,
                        size: Optional[Union[tuple[int, int], int]] = None,
                        effect = None,
                        stream: Literal["consistently", "together"] = "consistently") -> None:
            """
            Добавляет спрайт персонажа на сцену
            :param character: Айди персонажа
            :param at: Положение персонажа
            :param size: Размер спрайта
            :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Сonsistently: Обновляет только первый генератор в списке, пока он не завершится
            """

            char_id = character.split(" ")[0]
            sprite = self.ListCharacters[char_id].show(character)

            sprite.size = self._get_size(size, sprite.size)

            screen_width = self.Game_view.width
            screen_height = self.Game_view.height

            if at is not None:

                x_norm, y_norm = self._get_norm(at, char_id)

                sprite.center_x = screen_width * x_norm
                sprite.center_y = screen_height * y_norm

            else:
                if char_id in self.Game_view.scene["sprites"]:
                    sprite.position = self.Game_view.scene["sprites"][char_id].position
                    sprite.scale = self.Game_view.scene["sprites"][char_id].scale
                else:
                    sprite.center_x = screen_width // 2
                    sprite.center_y = screen_height * 0.2

            if effect is not None:
                sprite.alpha = 0
            else:
                sprite.alpha = 255

            def target():
                self.Game_view.scene.add_sprite("sprites", character.split(" ")[0], sprite)
                yield

            self.Game_view.actions.active_generators.add_generator(stream, target(), "show_sprite")
            if effect is not None:
                self.Game_view.actions.active_generators.add_generator(
                    stream,
                    effect.effect(character.split(" ")[0], "sprites", self.Game_view, self.sm),
                    "show_sprite_effect"
                )

        def hide_character(self, character: str,
                        effect = None,
                        stream: Literal["consistently", "together"] = "consistently") -> None:
            """
            Удаляет спрайт персонажа со сцены
            :param character: Айди персонажа
            :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится
            """

            def target():
                self.Game_view.scene.delete_sprite("sprites", character)
                yield

            if effect is not None:
                self.Game_view.actions.active_generators.add_generator(
                    stream,
                    effect.effect(character, "sprites", self.Game_view, self.sm, 0),
                    "hide_sprite_effect"
                )
            self.Game_view.actions.active_generators.add_generator(stream, target(), "hide_sprite")

        def set_scene(self,
                      file_name: str,
                      size: Optional[Union[tuple[int, int], int]] = None,
                      layer: int = 0,
                      effect = None,
                      stream: Literal["consistently", "together"] = "consistently") -> None:
            """
            Изменяет бекграунд
            :param file_name: Название файла
            :param size: Размер
            :param layer: Слой
            :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится
            :raises ValueError: Если layer < 0
            :raises FileNotFoundError: Если файл сцены не был найден
            """

            #self.character_slice = -1

            if layer < 0:
                raise ValueError("Layer must be greater than zero.")


            sprite = self.Game_view.scene.get_sprite(file_name)
            if sprite is None:
                raise FileNotFoundError(f"File {file_name} not found!")

            sprite.center_x, sprite.center_y, sprite.size = self.Game_view.width * 0.5, self.Game_view.height * 0.5, self._get_size(size, sprite.size)

            bg_id = int(layer)
            if effect is not None:
                sprite.alpha = 0
                bg_id = -1

            def target(bg_id, hide_scene: bool):
                self.Game_view.scene.clear_layer("sprites")
                if hide_scene:
                    self.Game_view.scene.clear_layer("bg")
                self.Game_view.scene.add_sprite(f"bg", bg_id, sprite)
                yield

            def edit_layer_name_and_del_old(bg_id, layer):
                old_bg = self.Game_view.scene["bg"][bg_id]
                self.Game_view.scene.clear_layer("bg")
                self.Game_view.scene["bg"][layer] = old_bg
                yield

            self.Game_view.actions.active_generators.add_generator(stream, target(bg_id, effect is None), "set_scene")
            if effect is not None:
                self.Game_view.actions.active_generators.add_generator(stream, effect.effect(bg_id, "bg", self.Game_view, self.sm), "set_scene_effect")
                self.Game_view.actions.active_generators.add_generator(stream, edit_layer_name_and_del_old(bg_id, layer), "edit_layer_name_and_del_old")

        def set_scene_parallax(self,
                      files: [tuple[str, float]],
                      stream: Literal["consistently", "together"] = "consistently") -> None:

            #self.character_slice = -1

            self.Game_view.scene.clear_layer("sprites")

            self.Game_view.scene.clear_layer("bg")

            def target(file_name, speed):
                self.Game_view.scene.add_parallax_bg(file_name, speed, self.Game_view.center_x, self.Game_view.center_y)
                yield

            for data in files:
                self.Game_view.actions.active_generators.add_generator(stream, target(data[0], data[1]), "set_scene")

        def move(self, sprite: str,
                 position: tuple[Tuple[int, float]],
                 speed: float,
                 stream: Literal["consistently", "together"] = "consistently") -> None:
            """
            Перемещает персонажа из текущего положения в определённую координату
            :param sprite: Название спрайта
            :param position: Положение
            :param speed: Скорость передвижения
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится
            """
            now = {"character": sprite, "pos": position, "speed": speed}
            self.Game_view.actions.start_action("move_sprite", now, stream=stream)

        def fade(self, type: Literal["fadein", "fadeout"],
                 duration: float,
                 stream: Literal["consistently", "together"] = "consistently") -> None:
            """
            Создаёт эффект фейдинга на экране
            :param type: Тип фейда "fadein" или "fadeout"
            :param duration: Продолжительность анимации
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится
            :raises ActionNotFoundError: Если type не существует
            """
            match type:
                case "fadein":
                    self.Game_view.actions.start_action("fadein", {"time": duration}, stream=stream)
                case "fadeout":
                    self.Game_view.actions.start_action("fadeout", {"time": duration}, stream=stream)
                case _:
                    raise ActionNotFoundError(f"Action \"{type}\" now found!")

        def show_menu(self, buttons: dict[str : str]) -> None:
            '''
            Показывает меню выбора для переключения между лейблами
            Пример параметра buttons:
            {
                "Кнопка1" : "Лейбл1",
                "Кнопка2" : "Лейбл3",
                "Сдохнуть" : "Лейбл_сдохнуть"
            }
            '''
            self.Wait_trigger.on()

            self.Game_view.show_menu(buttons)

    class Lore:
        def __init__(self, Game_view, Wwl) -> None:
            """
            Обеспечивает работу с перемещением по сюжету сценария
            :param Game_view: Объект класса Game_view
            """
            self.Game_view = Game_view
            self.Wwl = Wwl

        def jump(self, label: str, position: int = 0) -> None:
            """
            Меняет текущий лейбл
            :param label: Название лейбла
            :param position: На какой строке сценария
            """
            self.Wwl.pose = position
            self.Wwl.label = label

    class Screen:
        def __init__(self, Game_view, Views) -> None:
            self.Game_view = Game_view
            self.Views = Views

        def call_view(self, view_name: str, *args, **kwargs):
            def call():
                self.Game_view.waiting_autoskip.off()
                view = getattr(self.Views, view_name)(*args, **kwargs)
                self.Game_view.window.show_view(view)
                yield
            self.Game_view.actions.active_generators.add_generator("consistently", call(), "call_screen")

    class Audio:
        def __init__(self, Game_view, AudioManager) -> None:
            """
            Отвечает за работу с аудио
            :param Game_view: Объект класса Game_view
            :param AudioManager: Объект класса AudioManager
            """
            self.Game_view = Game_view
            self.AudioManager = AudioManager

        def play(self, channel: Literal["music", "sound"],
                 file_name: str,
                 volume: float = 1.0,
                 loop: Optional[bool] = None,
                 effect: Optional[Literal["fade"]] = None,
                 stream: Literal["consistently", "together"] = "together") -> None:
            """
            Запускает музыку
            :param channel: Канал ("music" / "sound")
            :param file_name: Название файла звука
            :param volume: Громкость
            :param loop: Если True, музыка будет играть циклично
            :param effect: Название эффекта
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится
            :raises ChannelDoesNotExistError: Если channel не существует
            """
            match channel:
                case "music":
                    loop = True if loop is None else loop
                    target = self.AudioManager.play_music_gen(file_name, loop, volume, effect)
                    self.Game_view.actions.active_generators.add_generator(stream, target, "play_music")
                case "sound":
                    loop = False if loop is None else loop
                    target = self.AudioManager.play_sound_gen(file_name, loop, volume, effect)
                    self.Game_view.actions.active_generators.add_generator(stream, target, "play_sound")
                case _:
                    raise ChannelDoesNotExistError(f"Channel {channel} does not exist")

        def stop(self, channel: Literal["music", "sound"],
                 effect: Optional[Literal["fade"]] = None,
                 stream: Literal["consistently", "together"] = "together") -> None:
            """
            Останавливает проигрывание канала
            :param channel: Канал ("music" / "sound")
            :param effect: Название эффекта
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится
            :raises ChannelDoesNotExistError: Если channel не существует
            """
            match channel:
                case "music":
                    self.Game_view.actions.active_generators.add_generator(stream, self.AudioManager.stop_music_gen(effect), "stop_music")
                case "sound":
                    self.Game_view.actions.active_generators.add_generator(stream, self.AudioManager.stop_sound_gen(effect), "stop_sound")
                case N:
                    raise ChannelDoesNotExistError(f"Channel {N} does not exist")

    class SpriteEffects:

        class Dissolve:
            def __init__(self, duration: float = 1.0) -> None:
                """
                Отвечает эа эффект растворения
                :param duration: Продолжительность эффекта
                """
                self.name = "DISSOLVE"
                self.duration = duration

            def effect(self, sprite_name: str, layer: str, Game_view, sm: Saves_manager, target_alpha: int = 255):

                if sprite_name not in Game_view.scene[layer]:
                    yield
                    return

                sprite = Game_view.scene[layer][sprite_name]
                duration = max(self.duration + sm.Volume.get_other("fade_speed"), 0.001)

                start_alpha = sprite.alpha
                progress = 0.0

                while progress < 1.0:
                    dt = yield

                    if dt is None or dt <= 0:
                        continue

                    progress = min(progress + dt / duration, 1.0)

                    new_alpha = int(start_alpha + (target_alpha - start_alpha) * progress)
                    sprite.alpha = new_alpha

    def wait(self, duration: float):
        """
        Заставляет игру... Ждать
        :param duration:
        """
        self.Game_view.actions.start_action("wait", {"time": duration}, "consistently")

    def end(self, Wwl, Game_view):
        Wwl.label = "main"
        Wwl.pose = 0
        Game_view.chanel()

    def talk(self, character: str, text: str):
        def format_text(text: str) -> str:
            pattern = r'((?<!\\)\[[^\]]*(?:(?<!\\)\][^\[]*)*?(?<!\\)\])'
            text = re.split(pattern, str(text))
            for e, i in enumerate(text):
                if i.startswith("[") and i.endswith("]"):
                    text[e] = str(self.get(i.strip("[]"), "NONE"))
            text = "".join(text).replace("\\\\", "\\").replace("\[", "[").replace("\]", "]")
            return text
        gen = self.ListCharacters[character].talk(format_text(text))

        self.Game_view.actions.active_generators.add_generator("consistently", gen, "talk")
        self.returning = "END_text"