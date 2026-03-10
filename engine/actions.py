import time
from typing import Optional, Literal, Tuple

import arcade

from .list_generator import ListActiveGenerators
from .saves import Saves_manager as sm
from .Exceptions import ActionNotFoundError

class Actions:
    def __init__(self, main) -> None:
        """
        Хранит в себе некоторые функции-генераторы.
        Отвечает за обновление всех генераторов
        :param main:
        """
        self.main = main
        self.active_generators = ListActiveGenerators()
        self.dt_accumulator = 0.0

    def _fadein(self, now: dict):

        duration = max(now["time"] + sm.volume.get_other("fade_speed"), 0.001)
        progress = 0.0
        last_alpha = self.main.scene["fade"]["fade"].alpha
        min_step = 1

        while True:
            dt = yield

            if dt is None or dt <= 0:
                continue

            progress = min(progress + dt / duration, 1.0)
            new_alpha = int(progress * 255)

            if abs(new_alpha - last_alpha) >= min_step or progress >= 1.0:
                self.main.scene["fade"]["fade"].alpha = new_alpha
                last_alpha = new_alpha

            if progress >= 1.0:
                return

    def _fadeout(self, now: dict):

        duration = max(now["time"] + sm.volume.get_other("fade_speed"), 0.001)
        progress = 0.0
        last_alpha = self.main.scene["fade"]["fade"].alpha
        min_step = 1

        while True:
            dt = yield

            if dt is None or dt <= 0:
                continue

            progress = min(progress + dt / duration, 1.0)
            new_alpha = 255 - int(progress * 255)

            if abs(new_alpha - last_alpha) >= min_step or progress >= 1.0:
                self.main.scene["fade"]["fade"].alpha = new_alpha
                last_alpha = new_alpha

            if progress >= 1.0:
                self.main.scene["fade"]["fade"].alpha = 0
                return

    def _move(self, now: dict):
        sprite = self.main.scene["characters"][now["character"]]
        now["speed"] = now["speed"] * 1000

        if now["pos"][0] == -1:
            x_norm = sprite.center_x / self.main.width
        elif isinstance(now["pos"][0], int):
            x_norm = now["pos"][0] / self.main.width
        elif isinstance(now["pos"][0], float):
            x_norm = now["pos"][0]
        else:
            x_norm = 0.5

        if now["pos"][1] == -1:
            y_norm = sprite.center_y / self.main.height
        elif isinstance(now["pos"][1], int):
            y_norm = now["pos"][1] / self.main.height
        elif isinstance(now["pos"][1], float):
            y_norm = now["pos"][1]
        else:
            y_norm = 0.5

        target_x = self.main.width * x_norm
        target_y = self.main.height * y_norm

        speed = abs(now["speed"]) if now["speed"] != 0 else 0.001

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

            distance = (dx ** 2 + dy ** 2) ** 0.5
            step = speed * dt

            if distance <= step:
                sprite.center_x = target_x
                sprite.center_y = target_y
                break
            else:
                sprite.center_x += (dx / distance) * step
                sprite.center_y += (dy / distance) * step

    def _wait(self, now):
        start_time = time.time()

        while time.time() - start_time < now["time"]:
            yield

    def _show_splash(self, now):

        self.main.splash_manager.children[0][0].text = now["name"]
        self.main.splash_manager.children[0][1].text = now["description"]

        duration = max(now["duration"] + sm.volume.get_other("fade_speed"), 0.001)
        progress = 0.0
        last_alpha = self.main.scene["fade"]["splash"].alpha
        min_step = 1

        while True:
            dt = yield

            if dt is None or dt <= 0:
                continue


            progress = min(progress + dt / duration, 1.0)
            new_alpha = int(progress * 255)

            if abs(new_alpha - last_alpha) >= min_step or progress >= 1.0:
                self.main.splash_manager.children[0][0].update_font(font_color=(255, 255, 255, new_alpha))
                self.main.splash_manager.children[0][1].update_font(font_color=(255, 255, 255, new_alpha))

                self.main.scene["fade"]["splash"].alpha = new_alpha
                last_alpha = new_alpha

            if progress >= 1.0:
                break

        remaining_time = now["duration"]
        while remaining_time > 0:
            dt = yield
            if dt is None or dt <= 0:
                continue
            remaining_time -= dt

        duration = max(now["duration"] / 2 + sm.volume.get_other("fade_speed"), 0.001)
        progress = 0.0
        last_alpha = self.main.scene["fade"]["splash"].alpha
        min_step = 1

        while True:
            dt = yield

            if dt is None or dt <= 0:
                continue

            progress = min(progress + dt / duration, 1.0)
            new_alpha = 255 - int(progress * 255)

            if abs(new_alpha - last_alpha) >= min_step or progress >= 1.0:
                self.main.splash_manager.children[0][0].update_font(font_color=(255, 255, 255, new_alpha))
                self.main.splash_manager.children[0][1].update_font(font_color=(255, 255, 255, new_alpha))

                self.main.scene["fade"]["splash"].alpha = new_alpha
                last_alpha = new_alpha

            if progress >= 1.0:
                self.main.scene["fade"]["splash"].alpha = 0
                return


    def update(self, delta_time: float) -> None:
        self.active_generators.update(delta_time)

    def start_action(self, name: Literal["fadein", "fadeout", "move_sprite", "wait", "show_splash"],
                     now: dict,
                     stream: Literal["consistently", "together"]) -> None:
        """
        Запускает нужный генератор
        :param name: Название генератора
        :param now: Параметры для этого генератора (которых создаёт lore_viewer)
        :param stream: Метод обновления. Together: Обновление всех генераторов разом, Сonsistently: Обновляет только первый генератор в списке, пока он не завершится
        :raises ActionNotFoundError: Если name не существует
        """

        method_map = {
            "fadein": self._fadein,
            "fadeout": self._fadeout,
            "move_sprite": self._move,
            "wait": self._wait,
            "show_splash" : self._show_splash
        }

        if name not in method_map:
            raise ActionNotFoundError(f"Action \"{name}\" now found!")

        self.active_generators.add_generator(stream, method_map[name](now), name)