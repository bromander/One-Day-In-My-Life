import sys
from io import StringIO
import re
from typing import Optional, Literal, Tuple
from .saves import Saves_manager
from .Exceptions import ActionNotFoundError, ChannelDoesNotExistError


class Namespace:
    def __init__(self, GameView, ListCharacters, Wwl, AudioManager, Wait_trigger) -> None:
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

        self.NAMESPACE = {
            "Persistent": self.Persistent(),
            "Define": self.Define(),
            "Scene": self.Scene(GameView, ListCharacters, Wwl, Wait_trigger),
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
        exec(command, self.NAMESPACE)
        old_ret = self.returning
        self.returning = None
        return old_ret

    def get(self, key: str, default: any = None) -> any:
        return self.NAMESPACE.get(key, default)

    class Persistent:
        def __init__(self):
            """
            Отвечает за работу с переменными, которые сохраняются межуд сессиями
            """
            pass

        def __setattr__(self, name, value):
            Saves_manager().persistent.set_persistent(name, value)
            super().__setattr__(name, value)

        def __getattribute__(self, item):
            super().__setattr__(item, Saves_manager().persistent.get_persistent(item))
            return Saves_manager().persistent.get_persistent(item)

        def __delattr__(self, item):
            super().__delattr__(item)
            return Saves_manager().persistent.del_persistent(item)

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

    class Scene:
        def __init__(self, Game_view, ListCharacters, Wwl, Wait_trigger) -> None:
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

        def show_character(self, character: str,
                        at: Optional[Tuple[Literal["left", "right", "center"], tuple[int, int], tuple[float, float]]] = None,
                        effect: Optional[classmethod] = None,
                        stream: Literal["consistently", "together"] = "consistently") -> None:
            """
            Добавляет спрайт на сцену
            :param character: Айди персонажа
            :param at: Положение персонажа
            :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Сonsistently: Обновляет только первый генератор в списке, пока он не завершится
            """

            char_id = character.split(" ")[0]
            sprite = self.ListCharacters[char_id].show(character)

            screen_width = self.Game_view.width
            screen_height = self.Game_view.height

            if at is not None:

                sprite.center_y = sprite.height / 2
                match at:
                    case "center":
                        sprite.center_x = screen_width // 2
                    case "left":
                        sprite.center_x = (screen_width // 2) * 0.4
                    case "right":
                        sprite.center_x = (screen_width // 2) * 1.6
                    case _ if isinstance(at, tuple) and len(at) == 2:

                        if at[0] == -1:
                            x_norm = self.Game_view.scene["sprites"][char_id].position[0] / screen_width
                        elif isinstance(at[0], int):
                            x_norm = at[0] / screen_width

                        elif isinstance(at[0], float):
                            if 0 <= at[0] <= 1:
                                x_norm = at[0]
                            else:
                                x_norm = at[0] / screen_width

                        else:
                            x_norm = 0


                        if at[1] == -1:
                            y_norm = self.Game_view.scene["sprites"][char_id].position[1] / screen_height

                        elif isinstance(at[1], int):
                                y_norm = at[1] / screen_height

                        elif isinstance(at[1], float):
                            if 0 <= at[1] <= 1:
                                y_norm = at[1]
                            else:
                                y_norm = at[1] / screen_height
                        else:
                            y_norm = 0

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
                    effect.effect(character.split(" ")[0], "sprites", self.Game_view),
                    "show_sprite_effect"
                )

        def hide_character(self, character: str,
                        effect: Optional[classmethod] = None,
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
                    effect.effect(character, "sprites", self.Game_view, 0),
                    "hide_sprite_effect"
                )
            self.Game_view.actions.active_generators.add_generator(stream, target(), "hide_sprite")

        def set_scene(self,
                      file_name: str,
                      scale: float,
                      layer: int = 0,
                      effect: Optional[classmethod] = None,
                      stream: Literal["consistently", "together"] = "consistently") -> None:
            """
            Изменяет бекграунд
            :param file_name: Название файла
            :param scale: Размер
            :param layer: Слой
            :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится
            :raises ValueError: Если layer < 0
            :raises FileNotFoundError: Если файл сцены не был найден
            """

            if layer < 0:
                raise ValueError("Layer must be greater than zero.")

            self.Game_view.scene.clear_layer("sprites")

            sprite = self.Game_view.scene.get_sprite(file_name)
            if sprite is None:
                raise FileNotFoundError(f"File {file_name} not found!")

            sprite.center_x, sprite.center_y, sprite.scale = self.Game_view.width * 0.5, self.Game_view.height * 0.5, scale

            bg_id = int(layer)
            if effect is not None:
                sprite.alpha = 0
                bg_id = -1
            else:
                self.Game_view.scene.clear_layer("bg")

            def target(bg_id):
                self.Game_view.scene.add_sprite(f"bg", bg_id, sprite)
                yield

            def edit_layer_name_and_del_old(bg_id, layer):
                old_bg = self.Game_view.scene["bg"][bg_id]
                self.Game_view.scene.clear_layer("bg")
                self.Game_view.scene["bg"][layer] = old_bg
                yield

            self.Game_view.actions.active_generators.add_generator(stream, target(bg_id), "set_scene")
            if effect is not None:
                self.Game_view.actions.active_generators.add_generator(stream, effect.effect(bg_id, "bg", self.Game_view), "set_scene_effect")
                self.Game_view.actions.active_generators.add_generator(stream, edit_layer_name_and_del_old(bg_id, layer), "edit_layer_name_and_del_old")

        def move(self, character: str,
                 position: tuple[Tuple[int, float]],
                 speed: float,
                 stream: Literal["consistently", "together"] = "consistently") -> None:
            """
            Перемещает персонажа из текущего положения в определённую координату
            :param character: Айди пользователя
            :param position: Положение
            :param speed: Скорость передвижения
            :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится
            """
            now = {"character": character, "pos": position, "speed": speed}
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
                    target = self.AudioManager.play_music_gen(f"game/music/{file_name}", loop, volume, effect)
                    self.Game_view.actions.active_generators.add_generator(stream, target, "play_music")
                case "sound":
                    loop = False if loop is None else loop
                    target = self.AudioManager.play_sound_gen(f"game/sounds/{file_name}", loop, volume, effect)
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

            def effect(self, sprite_name: str, layer: str, Game_view: classmethod, target_alpha: int = 255):

                if sprite_name not in Game_view.scene[layer]:
                    yield
                    return

                sprite = Game_view.scene[layer][sprite_name]
                duration = max(self.duration + Saves_manager().volume.get_other("fade_speed"), 0.001)

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
                    text[e] = self.get(i.strip("[]"), "NONE")
            text = "".join(text).replace("\\\\", "\\")
            return text
        gen = self.ListCharacters[character].talk(format_text(text))

        self.Game_view.actions.active_generators.add_generator("consistently", gen, "talk")
        self.returning = "End_text"