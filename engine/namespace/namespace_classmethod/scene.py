from typing import Optional, Literal, Union, Tuple
from arcade import get_window, Sprite, TextureAnimationSprite

from .exceptions import ActionNotFoundError
from .Ease import Ease


class Scene:
    def __init__(self, g) -> None:
        """
        Отвечает за работу с игровой сценой
        """
        self.g = g
        self.actions = g.actions
        self.lc = g.ListCharacters
        self.set_bg_by_scene_bg = g.main.set_bg_by_scene_bg

    @property
    def character_slice(self):
        return self.g.scene.character_slice

    @character_slice.setter
    def character_slice(self, value):
        self.g.scene.set_characters_slice(value)

    def _get_norm(
        self,
        at: Optional[
            Union[
                Literal["left", "right", "center"],
                tuple[int, int],
                tuple[float, float],
            ]
        ],
        sprite_name: Optional[str] = None,
    ):

        window = get_window()

        x_norm, y_norm = 0, 0.4

        if sprite_name:
            if sprite_name in self.g.scene["sprites"]:
                sprite = self.g.scene["sprites"][sprite_name]
            else:
                sprite = Sprite(
                    center_x=window.width * x_norm, center_y=window.height * y_norm
                )

        match at:
            case "center":
                x_norm = 0.5
            case "left":
                x_norm = 0.2
            case "right":
                x_norm = 0.8
            case _ if isinstance(at, tuple) and len(at) == 2:
                if at[0] == -1:
                    if sprite_name:
                        x_norm = sprite.position[0] / window.width
                    else:
                        x_norm = window.center_x
                elif isinstance(at[0], int):
                    x_norm = at[0] / window.width

                elif isinstance(at[0], float):
                    if 0 <= at[0] <= 1:
                        x_norm = at[0]
                    else:
                        x_norm = at[0] / window.width

                if at[1] == -1:
                    if sprite_name:
                        y_norm = sprite.position[1] / window.height
                    else:
                        y_norm = window.center_y
                elif isinstance(at[1], int):
                    y_norm = at[1] / window.height

                elif isinstance(at[1], float):
                    if 0 <= at[1] <= 1:
                        y_norm = at[1]
                    else:
                        y_norm = at[1] / window.height

        return x_norm, y_norm

    def _get_size(
        self,
        size,
        sprite_size: tuple,
    ) -> tuple:
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

    def add_sprite(
        self,
        filename_or_sprite: [str, Sprite, TextureAnimationSprite],
        at=None,
        size=None,
        angle: int = 0.0,
        flip_x: bool = False,
        flip_y: bool = False,
        effect = None,
        stream: Literal[
            "consistently", "consistently_async", "together"
        ] = "consistently",
        layer: str = "sprites",
    ) -> None:
        """
        Добавляет спрайт на сцену
        :param filename_or_sprite: Название спрайта или сам спрайт
        :param at: Позиция
        :param size: Размер спрайта
        :param flip_x: Отражает персонажа по горизонтали
        :param flip_y: Отражает персонажа по вертикали
        :param angle: поворот спрайта
        :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
        :param stream: Метод обновления. Together: Обновление всех генераторов разом, Сonsistently: Обновляет только первый генератор в списке, пока он не завершится, consistently_async: Обновляет только первый генератор в списке, но игра не ждёт его окончания
        """
        window = get_window()

        if isinstance(filename_or_sprite, (Sprite, TextureAnimationSprite)):
            filename = filename_or_sprite.texture.file_path.name
            sprite = filename_or_sprite
        else:
            filename = filename_or_sprite
            sprite = self.g.scene.get_sprite(filename_or_sprite)
            if sprite is None:
                raise FileNotFoundError(f"File {filename_or_sprite} not found!")

        if flip_x:
            sprite.texture = sprite.texture.flip_horizontally()

        if flip_y:
            sprite.texture = sprite.texture.flip_horizontally()

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
            self.g.scene.add_sprite(layer, filename, sprite)
            yield

        self.actions.active_generators.add_generator(stream, target(), "show_sprite")
        if effect is not None:
            self.actions.active_generators.add_generator(
                stream, effect.effect(sprite), "show_sprite_effect"
            )

    def hide_sprite(
        self,
        filename: str,
        effect=None,
        stream: Literal[
            "consistently", "consistently_async", "together"
        ] = "consistently",
    ) -> None:
        """
        Удаляет спрайт со сцены
        :param filename: Название файла
        :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
        :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится, consistently_async: Обновляет только первый генератор в списке, но игра не ждёт его окончания
        """

        def target():
            self.g.scene.delete_sprite("sprites", filename)
            yield

        if effect is not None:
            sprite = self.g.scene.get_scene_sprite(filename, "sprites")
            self.actions.active_generators.add_generator(
                stream, effect.effect(sprite, 0), "hide_sprite_effect"
            )
        self.actions.active_generators.add_generator(stream, target(), "hide_sprite")

    def show_character(
        self,
        character: str,
        at=None,
        size=None,
        angle: Optional[int] = None,
        flip_x: Optional[bool] = None,
        flip_y: Optional[bool] = None,
        effect=None,
        stream: Literal[
            "consistently", "consistently_async", "together"
        ] = "consistently",
    ) -> None:
        """
        Добавляет спрайт персонажа на сцену
        :param character: Айди персонажа
        :param at: Положение персонажа
        :param size: Размер спрайта
        :param angle: поворот спрайта
        :param flip_x: Отражает персонажа по горизонтали
        :param flip_y: Отражает персонажа по вертикали
        :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
        :param stream: Метод обновления. Together: Обновление всех генераторов разом, Сonsistently: Обновляет только первый генератор в списке, пока он не завершится, consistently_async: Обновляет только первый генератор в списке, но игра не ждёт его окончания
        """

        window = get_window()

        char_id = character.split(" ")[0]
        sprite: Sprite = self.lc[char_id].show(character)

        if flip_x:
            sprite.texture = sprite.texture.flip_horizontally()

        if flip_y:
            sprite.texture = sprite.texture.flip_vertically()

        if angle:
            sprite.angle = angle
        elif angle is None:
            if char_id in self.g.scene["sprites"]:
                sprite.angle = self.g.scene["sprites"][char_id].angle

        if size is not None:
            sprite.size = self._get_size(size, sprite.size)
        else:
            if char_id in self.g.scene["sprites"]:
                sprite.size = self.g.scene["sprites"][char_id].size

        if at is not None:
            x_norm, y_norm = self._get_norm(at, char_id)

            sprite.center_x = window.width * x_norm
            sprite.center_y = window.height * y_norm

        else:
            if char_id in self.g.scene["sprites"]:
                sprite.position = self.g.scene["sprites"][char_id].position
            else:
                sprite.center_x = window.width // 2
                sprite.center_y = window.height * 0.2

        if effect is not None:
            sprite.alpha = 0
        else:
            sprite.alpha = 255

        new_char_name_sprite = f"{character.split(' ')[0]}_new"

        def target():
            if effect is not None:
                self.g.scene.add_sprite("sprites", new_char_name_sprite, sprite)
            else:
                self.g.scene.add_sprite("sprites", character.split(" ")[0], sprite)
            yield

        def rename():
            sprite = self.g.scene["sprites"][new_char_name_sprite]
            del self.g.scene["sprites"][new_char_name_sprite]
            self.g.scene["sprites"][character.split(" ")[0]] = sprite
            yield

        self.actions.active_generators.add_generator(stream, target(), "show_sprite")
        if effect is not None:
            self.actions.active_generators.add_generator(
                stream,
                effect.effect_show_sprite(sprite, character.split(" ")[0]),
                "show_sprite_effect",
            )
            self.actions.active_generators.add_generator(
                stream, rename(), "rename_sprite_effect"
            )

        # effect_show_sprite(self, new_sprite: Sprite, old_sprite: Sprite)

    def hide_character(
        self,
        character: str,
        effect=None,
        stream: Literal[
            "consistently", "consistently_async", "together"
        ] = "consistently",
    ) -> None:
        """
        Удаляет спрайт персонажа со сцены
        :param character: Айди персонажа
        :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
        :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится, consistently_async: Обновляет только первый генератор в списке, но игра не ждёт его окончания
        """

        def target(scene):
            scene.delete_sprite("sprites", character)
            yield

        if effect is not None:
            sprite = self.g.scene.get_scene_sprite(character, "sprites")
            effect = effect.effect(sprite, 0)
            self.actions.active_generators.add_generator(
                stream, effect, "hide_sprite_effect"
            )
        self.actions.active_generators.add_generator(
            stream, target(self.g.scene), "hide_sprite"
        )

    def set_scene(
        self,
        file_name: Optional[Union[str, Sprite]],
        size=None,
        at=None,
        layer: int = 0,
        effect=None,
        stream: Literal[
            "consistently", "consistently_async", "together"
        ] = "consistently",
    ) -> None:
        """
        Изменяет бекграунд
        :param file_name: Название файла
        :param size: Размер
        :param at: Положение бекграунда
        :param layer: Слой
        :param effect: Вложенный класс класса SpriteEffects. Обозначает эффект, который будет примениться к спрайту при появлении
        :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится, consistently_async: Обновляет только первый генератор в списке, но игра не ждёт его окончания
        :raises ValueError: Если layer < 0
        :raises FileNotFoundError: Если файл сцены не был найден
        """

        # self.character_slice = -1

        window = get_window()
        scene = self.g.scene

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
                self.actions.active_generators.add_generator(
                    stream, effect.effect(sprite), "set_scene_effect"
                )

            self.actions.active_generators.add_generator(
                stream, del_layer(), "set_scene"
            )

            return None

        elif isinstance(file_name, str):
            sprite = scene.get_sprite(file_name)
            if sprite is None:
                raise FileNotFoundError(f"File {file_name} not found!")

        elif isinstance(file_name, Sprite):
            sprite = file_name

        sprite.size = self._get_size(size, sprite.size)

        if effect is not None:
            sprite.alpha = 0

        if at is not None:
            x_norm, y_norm = self._get_norm(at)

            sprite.center_x = window.width * x_norm
            sprite.center_y = window.height * y_norm

        else:
            sprite.center_x = window.width // 2
            sprite.center_y = window.height * 0.2


        def target(bg_id, hide_scene: bool):
            scene.clear_layer("sprites")
            scene.clear_layer("bg_parallax")
            scene.clear_layer("animated_sprites")
            if hide_scene:
                scene.clear_layer("bg")
            scene.add_sprite("bg", bg_id, sprite)
            self.set_bg_by_scene_bg()
            self.g.scene.on_resize(*get_window().get_size())
            yield

        def edit_layer_name_and_del_old(bg_id, layer):
            old_bg = scene["bg"][bg_id]
            scene.clear_layer("animated_sprites")
            scene.clear_layer("bg")
            scene["bg"][layer] = old_bg
            yield

        self.actions.active_generators.add_generator(
            stream, target(bg_id, effect is None), "set_scene"
        )
        if effect is not None:
            self.actions.active_generators.add_generator(
                stream, effect.effect(sprite), "set_scene_effect"
            )
            self.actions.active_generators.add_generator(
                stream,
                edit_layer_name_and_del_old(bg_id, layer),
                "edit_layer_name_and_del_old",
            )

    def set_scene_parallax(
        self,
        files: [tuple[str, float]],
        stream: Literal["consistently", "consistently_async", "together"] = "together",
    ) -> None:

        window = get_window()

        self.g.scene.clear_layer("bg_parallax")

        def target(file_name, speed):
            self.g.scene.clear_layer("sprites")
            self.g.scene.clear_layer("bg")
            self.g.scene.add_parallax_bg(
                file_name, speed, window.center_x, window.center_y
            )
            self.set_bg_by_scene_bg()
            yield

        for data in files:
            self.actions.active_generators.add_generator(
                stream, target(data[0], data[1]), "set_scene"
            )

    def move(
        self,
        sprite: str,
        move_to,
        speed: float,
        stream: Literal[
            "consistently", "consistently_async", "together"
        ] = "consistently",
    ) -> None:
        """
        Перемещает персонажа из текущего положения в определённую координату
        :param sprite: Название спрайта
        :param move_to: Положение
        :param speed: Скорость передвижения
        :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится, consistently_async: Обновляет только первый генератор в списке, но игра не ждёт его окончания
        """
        self.actions.active_generators.add_generator(
            stream, self._move_gen(sprite, speed, move_to), "move_sprite"
        )

    def fade(
        self,
        type: Literal["fadein", "fadeout"],
        duration: float,
        effect: Optional[str] = "ease_in_quad",
        stream: Literal[
            "consistently", "consistently_async", "together"
        ] = "consistently",
    ) -> None:
        """
        Создаёт эффект фейдинга на экране
        :param type: Тип фейда "fadein" или "fadeout"
        :param duration: Продолжительность анимации
        :param effect: Ease эффект появления фейда
        :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится, consistently_async: Обновляет только первый генератор в списке, но игра не ждёт его окончания
        :raises ActionNotFoundError: Если type не существует
        """
        match type:
            case "fadein":
                self.actions.active_generators.add_generator(
                    stream, self._fadein_gen(duration, effect), "fadein"
                )
            case "fadeout":
                self.actions.active_generators.add_generator(
                    stream, self._fadeout_gen(duration, effect), "fadeout"
                )
            case _:
                raise ActionNotFoundError(f'Action "{type}" now found!')

    def start_cutscene(self, path):
        cutscene: TextureAnimationSprite = self.g.scene.get_sprite(path)
        while cutscene is None:
            cutscene = self.g.scene.get_sprite(path)

        cutscene.size = get_window().size
        self.g.scene.clear_layer("bg")
        self.g.scene.clear_layer("animated_sprites")
        self.add_sprite(cutscene, layer="animated_sprites", at=(0.5, 0.5))

    # ===== ГЕНЕРАТОРЫ =====

    def _effect_progress(self, t, effect: Optional[str] = None):
        if effect:
            return Ease.prepare_effect(effect, t)
        else:
            return t

    def _fadein_gen(self, time: float, effect: Optional[str] = None):

        duration = max(time * self.g.sm.Volume.fade_speed, 0.001)
        progress = 0.0
        last_alpha = self.g.scene["fade"]["fade"].alpha
        fade_sprite = self.g.scene["fade"]["fade"]
        min_step = 1

        while True:
            dt = yield

            if dt is None or dt <= 0:
                continue

            progress = min(progress + dt / duration, 1.0)
            progress_ease = self._effect_progress(progress, effect)
            new_alpha = round(progress_ease * 255)

            if abs(new_alpha - last_alpha) >= min_step or progress >= 1.0:
                fade_sprite.alpha = new_alpha
                last_alpha = new_alpha

            if progress >= 1.0:
                return

    def _fadeout_gen(self, time: float, effect: Optional[str] = None):

        duration = max(time * self.g.sm.Volume.fade_speed, 0.001)
        progress = 0.0
        last_alpha = self.g.scene["fade"]["fade"].alpha
        fade_sprite = self.g.scene["fade"]["fade"]
        min_step = 1

        while True:
            dt = yield

            if dt is None or dt <= 0:
                continue

            progress = min(progress + dt / duration, 1.0)
            progress_ease = self._effect_progress(progress, effect)
            new_alpha = 255 - round(progress_ease * 255)

            if abs(new_alpha - last_alpha) >= min_step or progress >= 1.0:
                fade_sprite.alpha = new_alpha
                last_alpha = new_alpha

            if progress >= 1.0:
                fade_sprite.alpha = 0
                return

    def _move_gen(self, sprite_name: str, speed: float, move_to):
        main = self.g.main

        sprite = self.g.scene["sprites"][sprite_name]
        speed *= 1000

        x_norm, y_norm = self._get_norm(move_to, sprite_name)

        target_x = main.width * x_norm
        target_y = main.height * y_norm

        speed = abs(speed) if speed != 0 else 0.001

        start_x = sprite.center_x
        start_y = sprite.center_y
        full_distance = ((target_x - start_x) ** 2 + (target_y - start_y) ** 2) ** 0.5

        if full_distance < 1:
            return None

        while True:
            dt = yield

            if dt is None or dt <= 0:
                continue

            current_x = sprite.center_x
            current_y = sprite.center_y
            dx = target_x - current_x
            dy = target_y - current_y

            distance = (dx**2 + dy**2) ** 0.5
            step = speed * dt

            if distance <= step:
                sprite.center_x = target_x
                sprite.center_y = target_y
                break
            else:
                sprite.center_x += (dx / distance) * step
                sprite.center_y += (dy / distance) * step
