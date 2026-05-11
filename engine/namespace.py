import time, datetime
import re
from typing import Optional, Literal, Tuple, Union
import PIL
import arcade
from arcade import Sprite, Texture, load_image, get_window, load_animated_gif, TextureAnimationSprite

from .saves import Saves_manager
from .Exceptions import ActionNotFoundError, ChannelDoesNotExistError

from .globals import g

class Namespace:
    def __init__(self) -> None:
        """
        Отвечает за работу со всеми функциями, используемыми в сценариях.
        """

        self.Game_view = g.main
        self.ListCharacters = g.ListCharacters
        self.Wwl = g.wwl
        self.AudioManager = g.am
        self.SavesManager = g.sm

        self.NAMESPACE = {
            "Data" : self.Data(self),
            "Persistent": self.Persistent(),
            "Define": self.Define(),
            "Scene": self.Scene(),
            "Screen" : self.Screen(),
            "Audio": self.Audio(),
            "Lore": self.Lore(),
            "SpriteEffects": self.SpriteEffects(),
            "wait" : lambda duration: self.wait(duration),
            "talk" : self.talk,
            "end" : lambda: self.end()
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
        def __init__(self):
            """
            Отвечает за работу с переменными, которые сохраняются между сессиями
            """
            super().__setattr__('sm', g.sm)

        def __setattr__(self, name, value):
            if 'sm' not in self.__dict__:
                super().__setattr__(name, value)
            elif name == 'sm':
                super().__setattr__(name, value)
            else:
                self.sm.Persistent.set_persistent(name, value)
                super().__setattr__(name, value)

        def __getattribute__(self, item):
            if item.startswith('__') and item.endswith('__') or item == 'sm':
                return object.__getattribute__(self, item)

            return self.sm.Persistent.get_persistent(item)

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

        def get_all_variables(self):
            """Возвращает все пользовательские переменные"""
            return self.defines.copy()  # Возвращаем копию, чтобы избежать случайных изменений

    class Data:
        '''
        Предоставляет доступ к основным классам движка
        '''

        def __init__(self, namespace):
            self.session_id = g.main.session_id
            self.height = g.main.height
            self.width = g.main.width
            self.Window = g.main.window
            self.namespace = namespace
            self.Game_view = g.main
            self.ListCharacters = g.ListCharacters
            self.Wwl = g.wwl
            self.AudioManager = g.am
            self.PIL = PIL

            self.mix = {
                "Сладкие блинчики": (frozenset(["milk.png", "eggs.png", "puki.png", "pineapple.png"]), "cooking_bliny"),  # молоко+яйца+мука+ананас
                "Омлет" : (frozenset(["milk.png", "eggs.png"]), "cooking_omlet"), # Молоко и яица
                "Салат" : (frozenset(["tomatoes.png"]), "cooking_salad") # Помедорчеки
                #"Пирог" : (frozenset(["milk.png", "eggs.png", "puki.png"]), "blinyyy") # Яица, молоко  и муки
            }

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

        def trig_dialogue_window(self, state: Optional[bool]):
            if state:
                self.Game_view.show_dialogue_bg_trigger = state
            else:
                self.Game_view.show_dialogue_bg_trigger = not self.Game_view.show_dialogue_bg_trigger

        def get_food_root(self) -> list[tuple]:
            chosen = [i for i in self.namespace["Define"].collected_items.keys()]
            available = []
            for name, fset in self.mix.items():
                if set(fset[0]).issubset(set(chosen)):
                    available.append((name, fset[1]))
            return available

    class Scene:
        def __init__(self) -> None:
            """
            Отвечает за работу с игровой сценой
            """


        @property
        def character_slice(self):
            return g.scene.character_slice

        @character_slice.setter
        def character_slice(self, value):
            g.scene.set_characters_slice(value)

        def _get_norm(self,
                      at: Optional[Union[Literal["left", "right", "center"], tuple[int, int], tuple[float, float]]],
                      sprite_name: str):

            window = get_window()

            x_norm, y_norm = 0, 0.4

            if sprite_name in g.scene["sprites"]:
                sprite = g.scene["sprites"][sprite_name]
            else:
                sprite = Sprite(center_x=window.width * x_norm, center_y=window.height * y_norm)

            match at:
                case "center":
                    x_norm = 0.5
                case "left":
                    x_norm = 0.2
                case "right":
                    x_norm = 0.8
                case _ if isinstance(at, tuple) and len(at) == 2:

                    if at[0] == -1:
                        x_norm = sprite.position[0] / window.width
                    elif isinstance(at[0], int):
                        x_norm = at[0] / window.width

                    elif isinstance(at[0], float):
                        if 0 <= at[0] <= 1:
                            x_norm = at[0]
                        else:
                            x_norm = at[0] / window.width


                    if at[1] == -1:
                        y_norm = sprite.position[1] / window.height

                    elif isinstance(at[1], int):
                            y_norm = at[1] / window.height

                    elif isinstance(at[1], float):
                        if 0 <= at[1] <= 1:
                            y_norm = at[1]
                        else:
                            y_norm = at[1] / window.height

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


        def add_sprite(self, filename_or_sprite: [str, Sprite, TextureAnimationSprite],
                       at: Optional[Union[Literal["left", "right", "center"], tuple[int, int], tuple[float, float]]] = None,
                       size: Optional[Union[tuple[int, int], int]] = None,
                       angle: int = 0.0,
                       effect = None,
                       stream: Literal["consistently", "consistently_async", "together"] = "consistently",
                       layer: str = "sprites") -> None:
            """
            Добавляет спрайт на сцену
            :param filename_or_sprite: Название спрайта или сам спрайт
            :param at: Позиция
            :param size: Размер спрайта
            :param angle: поворот спрайта
            :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Сonsistently: Обновляет только первый генератор в списке, пока он не завершится
            """
            window = get_window()

            if isinstance(filename_or_sprite, (Sprite, TextureAnimationSprite)):
                filename = filename_or_sprite.texture.file_path.name
                sprite = filename_or_sprite
            else:
                filename = filename_or_sprite
                sprite = g.scene.get_sprite(filename_or_sprite)
                if sprite is None:
                    raise FileNotFoundError(f"File {filename_or_sprite} not found!")

            sprite.size = self._get_size(size, sprite.size)

            if angle is not None:
                sprite.angle = angle

            if at is not None:

                x_norm, y_norm = self._get_norm(at, filename)

                sprite.center_x = window.width * x_norm
                sprite.center_y = window.height * y_norm

            else:
                sprite.center_x = window.width // 2
                sprite.center_y = window.height * 0.2

            if effect is not None:
                sprite.alpha = 0
            else:
                sprite.alpha = 255

            def target():
                g.scene.add_sprite(layer, filename, sprite)
                yield

            g.main.actions.active_generators.add_generator(stream, target(), "show_sprite")
            if effect is not None:
                g.main.actions.active_generators.add_generator(
                    stream,
                    effect.effect(sprite),
                    "show_sprite_effect"
                )

        def hide_sprite(self, filename: str,
                        effect = None,
                        stream: Literal["consistently", "consistently_async", "together"] = "consistently") -> None:
            """
            Удаляет спрайт со сцены
            :param filename: Название файла
            :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится
            """

            def target():
                g.scene.delete_sprite("sprites", filename)
                yield

            if effect is not None:
                sprite = g.scene.get_scene_sprite(filename, "sprites")
                g.main.actions.active_generators.add_generator(
                    stream,
                    effect.effect(sprite, 0),
                    "hide_sprite_effect"
                )
            g.main.actions.active_generators.add_generator(stream, target(), "hide_sprite")


        def show_character(self, character: str,
                        at: Optional[Union[Literal["left", "right", "center"], tuple[int, int], tuple[float, float]]] = None,
                        size: Optional[Union[int, float, Tuple[int], Tuple[float]]] = None,
                        effect = None,
                        stream: Literal["consistently", "consistently_async", "together"] = "consistently") -> None:
            """
            Добавляет спрайт персонажа на сцену
            :param character: Айди персонажа
            :param at: Положение персонажа
            :param size: Размер спрайта
            :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Сonsistently: Обновляет только первый генератор в списке, пока он не завершится
            """

            window = get_window()

            char_id = character.split(" ")[0]
            sprite = g.ListCharacters[char_id].show(character)

            sprite.size = self._get_size(size, sprite.size)

            if at is not None:

                x_norm, y_norm = self._get_norm(at, char_id)

                sprite.center_x = window.width * x_norm
                sprite.center_y = window.height * y_norm

            else:
                if char_id in g.scene["sprites"]:
                    sprite.position = g.scene["sprites"][char_id].position
                    sprite.scale = g.scene["sprites"][char_id].scale
                else:
                    sprite.center_x = window.width // 2
                    sprite.center_y = window.height * 0.2

            if effect is not None:
                sprite.alpha = 0
            else:
                sprite.alpha = 255

            def target():
                g.scene.add_sprite("sprites", character.split(" ")[0], sprite)
                yield

            g.main.actions.active_generators.add_generator(stream, target(), "show_sprite")
            if effect is not None:
                g.main.actions.active_generators.add_generator(
                    stream,
                    effect.effect(sprite),
                    "show_sprite_effect"
                )

        def hide_character(self, character: str,
                        effect = None,
                        stream: Literal["consistently", "consistently_async", "together"] = "consistently") -> None:
            """
            Удаляет спрайт персонажа со сцены
            :param character: Айди персонажа
            :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится
            """
            print("hide", id(g.scene.data), g.scene.data)
            def target(scene):
                print("hide", id(scene.data), scene.data)
                scene.delete_sprite("sprites", character)
                yield

            if effect is not None:
                sprite = g.scene.get_scene_sprite(character, "sprites")
                effect = effect.effect(sprite, 0)
                g.main.actions.active_generators.add_generator(
                    stream,
                    effect,
                    "hide_sprite_effect"
                )
            g.main.actions.active_generators.add_generator(stream, target(g.scene), "hide_sprite")

        def set_scene(self,
                      file_name: Optional[Union[str, Sprite]],
                      size: Optional[Union[tuple[int, int], int]] = None,
                      layer: int = 0,
                      effect = None,
                      stream: Literal["consistently", "consistently_async", "together"] = "consistently") -> None:
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

            window = get_window()
            scene = g.scene

            if layer < 0:
                raise ValueError("Layer must be greater than zero.")

            bg_id = int(layer)

            if effect is not None:
                bg_id = -1

            if file_name is None:
                def del_layer():
                    scene.clear_layer("sprites")
                    scene.clear_layer("bg_parallax")
                    scene.clear_layer("animated_sprites")
                    scene.clear_layer("bg")
                    yield

                if effect is not None:
                    sprite = scene.get_scene_sprite(file_name, "sprites")
                    g.main.actions.active_generators.add_generator(stream, effect.effect(sprite),"set_scene_effect")

                g.main.actions.active_generators.add_generator(stream, del_layer(), "set_scene")

                return None


            if isinstance(file_name, str):

                sprite = scene.get_sprite(file_name)
                if sprite is None:
                    raise FileNotFoundError(f"File {file_name} not found!")

            elif isinstance(file_name, Sprite):
                sprite = file_name

            sprite.center_x, sprite.center_y, sprite.size = window.width * 0.5, window.height * 0.5, self._get_size(size, sprite.size)

            if effect is not None:
                sprite.alpha = 0

            def target(bg_id, hide_scene: bool):
                scene.clear_layer("sprites")
                scene.clear_layer("bg_parallax")
                scene.clear_layer("animated_sprites")
                if hide_scene:
                    scene.clear_layer("bg")
                scene.add_sprite(f"bg", bg_id, sprite)
                g.main.set_bg_by_scene_bg()
                g.scene.on_resize(*get_window().get_size())
                yield


            def edit_layer_name_and_del_old(bg_id, layer):
                old_bg = scene["bg"][bg_id]
                scene.clear_layer("animated_sprites")
                scene.clear_layer("bg")
                scene["bg"][layer] = old_bg
                yield

            g.main.actions.active_generators.add_generator(stream, target(bg_id, effect is None), "set_scene")
            if effect is not None:
                g.main.actions.active_generators.add_generator(stream, effect.effect(sprite), "set_scene_effect")
                g.main.actions.active_generators.add_generator(stream, edit_layer_name_and_del_old(bg_id, layer), "edit_layer_name_and_del_old")

        def set_scene_parallax(self,
                      files: [tuple[str, float]],
                      stream: Literal["consistently", "consistently_async", "together"] = "together") -> None:

            window = get_window()

            g.scene.clear_layer("bg_parallax")

            def target(file_name, speed):
                g.scene.clear_layer("sprites")
                g.scene.clear_layer("bg")
                g.scene.add_parallax_bg(file_name, speed, window.center_x, window.center_y)
                g.main.set_bg_by_scene_bg()
                yield

            for data in files:
                g.main.actions.active_generators.add_generator(stream, target(data[0], data[1]), "set_scene")

        def move(self, sprite: str,
                 position: tuple[Tuple[int, float]],
                 speed: float,
                 stream: Literal["consistently", "consistently_async", "together"] = "consistently") -> None:
            """
            Перемещает персонажа из текущего положения в определённую координату
            :param sprite: Название спрайта
            :param position: Положение
            :param speed: Скорость передвижения
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится
            """
            now = {"character": sprite, "pos": position, "speed": speed}
            g.main.actions.start_action("move_sprite", now, stream=stream)

        def fade(self, type: Literal["fadein", "fadeout"],
                 duration: float,
                 stream: Literal["consistently", "consistently_async", "together"] = "consistently") -> None:
            """
            Создаёт эффект фейдинга на экране
            :param type: Тип фейда "fadein" или "fadeout"
            :param duration: Продолжительность анимации
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится
            :raises ActionNotFoundError: Если type не существует
            """
            match type:
                case "fadein":
                    g.main.actions.start_action("fadein", {"time": duration}, stream=stream)
                case "fadeout":
                    g.main.actions.start_action("fadeout", {"time": duration}, stream=stream)
                case _:
                    raise ActionNotFoundError(f"Action \"{type}\" now found!")

        def start_cutscene(self, path):
            print(path)
            cutscene: TextureAnimationSprite = g.scene.get_sprite(path)
            while cutscene is None:
                cutscene = g.scene.get_sprite(path)

            print(cutscene)
            cutscene.size = get_window().size
            g.scene.clear_layer("bg")
            g.scene.clear_layer("animated_sprites")
            self.add_sprite(cutscene, layer="animated_sprites", at=(0.5, 0.5))

    class Lore:
        def __init__(self) -> None:
            """
            Обеспечивает работу с перемещением по сюжету сценария
            """

        def jump(self, label: str, position: int = 0) -> None:
            """
            Меняет текущий лейбл
            :param label: Название лейбла
            :param position: На какой строке сценария
            """
            g.wwl.pose = position
            g.wwl.label = label

    class Screen:

        def call_view(self, view_name: str):
            def call():
                g.main.waiting_autoskip.off()
                view = getattr(g.All_views, view_name)()
                get_window().show_view(view)
                yield
            g.main.actions.active_generators.add_generator("consistently", call(), "call_screen")

    class Audio:
        def __init__(self) -> None:
            """
            Отвечает за работу с аудио
            """

        def play(self, channel: Literal["music", "sound"],
                 file_name: str,
                 volume: float = 1.0,
                 loop: Optional[bool] = None,
                 effect: Optional[Literal["fade"]] = None,
                 stream: Literal["consistently", "consistently_async", "together"] = "consistently_async") -> None:
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
                    target = g.am.play_music_gen(file_name, loop, volume, effect)
                    g.main.actions.active_generators.add_generator(stream, target, "play_music")
                case "sound":
                    loop = False if loop is None else loop
                    target = g.am.play_sound_gen(file_name, loop, volume, effect)
                    g.main.actions.active_generators.add_generator(stream, target, "play_sound")
                case _:
                    raise ChannelDoesNotExistError(f"Channel {channel} does not exist")

        def stop(self, channel: Literal["music", "sound"],
                 effect: Optional[Literal["fade"]] = None,
                 stream: Literal["consistently", "consistently_async", "together"] = "consistently_async") -> None:
            """
            Останавливает проигрывание канала
            :param channel: Канал ("music" / "sound")
            :param effect: Название эффекта
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится
            :raises ChannelDoesNotExistError: Если channel не существует
            """
            match channel:
                case "music":
                    g.main.actions.active_generators.add_generator(stream, g.am.stop_music_gen(effect), "stop_music")
                case "sound":
                    g.main.actions.active_generators.add_generator(stream, g.am.stop_sound_gen(effect), "stop_sound")
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

            def effect(self, sprite: Sprite, target_alpha: int = 255):

                duration = max(self.duration + g.sm.Volume.get_other("fade_speed"), 0.001)

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
        g.main.actions.start_action("wait", {"time": duration}, "consistently")

    def end(self):
        g.wwl.label = "main"
        g.wwl.pose = 0
        g.main.chanel()

    def talk(self, character: str, text: str):
        def format_text(text: str) -> str:
            pattern = r'((?<!\\)\[[^\]]*(?:(?<!\\)\][^\[]*)*?(?<!\\)\])'
            text = re.split(pattern, str(text))
            for e, i in enumerate(text):
                if i.startswith("[") and i.endswith("]"):
                    text[e] = str(self.get(i.strip("[]"), "NONE"))
            text = "".join(text).replace("\\\\", "\\").replace("\[", "[").replace("\]", "]")
            return text
        gen = g.ListCharacters[character].talk(format_text(text))

        g.main.actions.active_generators.add_generator("consistently", gen, "talk")
        self.returning = "END_text"