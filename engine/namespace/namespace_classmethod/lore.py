from typing import Literal, Optional
from .Ease import Ease


class Lore:
    def __init__(self, g) -> None:
        """
        Обеспечивает работу с перемещением по сюжету сценария
        """
        self.g = g

    def jump(self, label: str, position: int = 0) -> None:
        """
        Меняет текущий лейбл
        :param label: Название лейбла
        :param position: На какой строке сценария
        """
        self.g.lm.jump(label, position)

    def set_part(
        self,
        name: str,
        description: str,
        show_splash: bool = False,
        speed: float = 1.0,
        effect: Optional[str] = "ease_out_quad",
        stream: Literal["consistently", "consistently_async", "together"] = "together",
    ) -> None:
        """
        Позволяет указать то, в какой точке сюжета находится игрок.
        Ещё, позволяет запустить сплеш.
        По умолчанию, всегда вызывается в начале каждого лейбла
        :param name: Название текущей главы/части игры
        :param description: Описание
        :param show_splash: Если True, то при переключении на лейбл будет показан сплеш
        :param speed: Скорость появления сплеша и его пропадания (пропадает со скоростью в два раза меньше speed)
        :param effect: Ease эффект появления сплеша
        :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится, consistently_async: Обновляет только первый генератор в списке, но игра не ждёт его окончания
        """

        self.g.main.session_data["description"] = description
        self.g.main.session_data["name"] = name
        self.g.da.update(name, description)

        if show_splash:
            self.g.actions.active_generators.add_generator(
                stream,
                self._show_splash_gen(speed, name, description, effect),
                "show_splash",
            )

    def _effect(self, t, effect: Optional[str] = None):
        if effect:
            return Ease.prepare_effect(effect, t)
        else:
            return t

    def _show_splash_gen(
        self,
        duration: float = 2.0,
        name: str = "",
        description: str = "",
        effect: str = "ease_out_quad",
    ):

        splash_manager = self.g.main.splash_manager

        splash_manager.children[0][0].text = name
        splash_manager.children[0][1].text = description

        duration = max(duration * self.g.sm.Volume.fade_speed, 0.001)
        progress = 0.0
        last_alpha = self.g.scene["fade"]["splash"].alpha
        min_step = 1

        while True:
            dt = yield

            if dt is None or dt <= 0:
                continue

            progress = min(progress + dt / duration, 1.0)
            progress_ease = self._effect(progress, effect)
            new_alpha = round(progress_ease * 255)

            if abs(new_alpha - last_alpha) >= min_step or progress >= 1.0:
                splash_manager.children[0][0].update_font(
                    font_color=(255, 255, 255, new_alpha)
                )
                splash_manager.children[0][1].update_font(
                    font_color=(255, 255, 255, new_alpha)
                )

                self.g.scene["fade"]["splash"].alpha = new_alpha
                last_alpha = new_alpha

            if progress >= 1.0:
                break

        remaining_time = duration
        while remaining_time > 0:
            dt = yield
            if dt is None or dt <= 0:
                continue
            remaining_time -= dt

        duration = max(duration / 2 * self.g.sm.Volume.fade_speed, 0.001)
        progress = 0.0
        last_alpha = self.g.scene["fade"]["splash"].alpha
        min_step = 1

        while True:
            dt = yield

            if dt is None or dt <= 0:
                continue

            progress = min(progress + dt / duration, 1.0)
            progress_ease = self._effect(progress)
            new_alpha = 255 - round(progress_ease * 255)

            if abs(new_alpha - last_alpha) >= min_step or progress >= 1.0:
                splash_manager.children[0][0].update_font(
                    font_color=(255, 255, 255, new_alpha)
                )
                splash_manager.children[0][1].update_font(
                    font_color=(255, 255, 255, new_alpha)
                )

                self.g.scene["fade"]["splash"].alpha = new_alpha
                last_alpha = new_alpha

            if progress >= 1.0:
                self.g.scene["fade"]["splash"].alpha = 0
                splash_manager.children[0][0].update_font(font_color=(255, 255, 255, 0))
                return
