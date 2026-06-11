import time
from typing import Optional, Literal
from arcade import Sprite, get_window

from .Ease import Ease


class SpriteEffects:
    def __init__(self, g):
        self.Dissolve = lambda duration=1.0, additional_effect="ease_in_out_cubic": (
            self.Dissolve_effect(g, duration, additional_effect)
        )
        self.Slide = lambda duration=1.0, ease_dissolve_effect="ease_in_out_cubic", ease_slide_effect="ease_in_out_cubic", offset=None, side_from="auto_horizontal": (
            self.Slide_effect(g, duration, ease_dissolve_effect, ease_slide_effect, offset, side_from)
        )

    class Dissolve_effect:
        def __init__(
            self,
            g,
            duration: float = 1.0,
            ease_effect: Optional[str] = "ease_in_out_cubic",
        ) -> None:
            """
            Отвечает эа эффект растворения
            :param duration: Продолжительность эффекта
            """
            self.name = "DISSOLVE"
            self.duration = duration
            self.ease_effect = ease_effect

            self.g = g

        def _effect(self, t):
            if self.ease_effect:
                return Ease.prepare_effect(self.ease_effect, t)
            else:
                return t

        def effect(self, sprite: Sprite, target_alpha: int = 255):

            duration = max(self.duration * self.g.sm.Volume.fade_speed, 0.001)

            start_alpha = sprite.alpha
            progress = 0.0

            while progress < 1.0:
                dt = yield

                if dt is None or dt <= 0:
                    continue

                progress = min(progress + dt / duration, 1.0)
                progress_ease = self._effect(progress)

                new_alpha = round(
                    start_alpha + (target_alpha - start_alpha) * progress_ease
                )
                sprite.alpha = new_alpha

        def effect_show_sprite(self, new_sprite: Sprite, old_sprite_name: str):

            use_old_sprite = False
            if old_sprite_name in self.g.scene["sprites"]:
                old_sprite = self.g.scene.get_scene_sprite(old_sprite_name, "sprites")
                use_old_sprite = True

            start_new = new_sprite.alpha
            if use_old_sprite:
                start_old = old_sprite.alpha

            duration_new = max(self.duration * self.g.sm.Volume.fade_speed, 0.001)
            duration_old = duration_new * 2  # в два раза медленнее

            total_duration = duration_old

            elapsed = 0.0
            progress = 0.0

            while progress < 1.0:
                dt = yield

                if dt is None or dt <= 0:
                    continue

                elapsed += dt

                if use_old_sprite:
                    progress = min(elapsed / total_duration, 1.0)
                    progress_new = min(progress * 2, 1.0)
                else:
                    progress = min(elapsed / duration_new, 1.0)
                    progress_new = min(progress, 1.0)

                progress_ease_new = self._effect(progress_new)
                progress_ease_old = self._effect(progress)

                new_sprite.alpha = round(
                    start_new + (255 - start_new) * progress_ease_new
                )
                if use_old_sprite:
                    old_sprite.alpha = round(
                        start_old + (0 - start_old) * progress_ease_old
                    )

    class Slide_effect:
        def __init__(
            self,
            g,
            duration: float = 1.0,
            ease_dissolve_effect: Optional[str] = "ease_in_out_cubic",
            ease_slide_effect: Optional[str] = "ease_in_out_cubic",
            offset: Optional[int] = None,
            side_from: Literal[
                "left", "top", "right", "bottom", "auto_horizontal", "auto_vertical"
            ] = "auto_horizontal",
        ) -> None:
            """
            Отвечает эа эффект растворения
            :param duration: Продолжительность эффекта
            :param ease_dissolve_effect: Ease эффект появления спрайта
            :param ease_slide_effect: Ease эффект движения спрайта
            :param offset: Сколько пикселей спрайт будет двигаться. None, чтобы спрайт двигался треть своей ширины
            :param side_from: С какой стороны будет выезжать спрайт
            """
            self.name = "SLIDE"
            self.duration = duration
            self.ease_dissolve_effect = ease_dissolve_effect
            self.ease_slide_effect = ease_slide_effect
            self.side_from = side_from
            self.offset = offset

            self.g = g

        def _effect(self, t, effect: Optional[str]):
            if effect:
                return Ease.prepare_effect(effect, t)
            else:
                return t

        def _get_slide_offset(self, start_pos: tuple, sprite: Sprite):

            window = get_window()

            if self.offset is None:
                offset = (sprite.width / 3, sprite.height / 3)
            else:
                offset = (self.offset, self.offset)

            match self.side_from:
                case "left":
                    slide_offset = (start_pos[0] - offset[0], start_pos[1])
                case "right":
                    slide_offset = (start_pos[0] + offset[0], start_pos[1])
                case "top":
                    slide_offset = (start_pos[0], start_pos[1] + offset[1])
                case "bottom":
                    slide_offset = (start_pos[0], start_pos[1] - offset[1])
                case "auto_horizontal":
                    if sprite.center_x < window.center_x:
                        slide_offset = (start_pos[0] - offset[0], start_pos[1])
                    else:
                        slide_offset = (start_pos[0] + offset[0], start_pos[1])
                case "auto_vertical":
                    if sprite.center_y < window.center_y:
                        slide_offset = (start_pos[0], start_pos[1] - offset[1])
                    else:
                        slide_offset = (start_pos[0], start_pos[1] + offset[1])
                case _:
                    raise ValueError(
                        f"Значение параметра side_from у Slide_effect спарйта {sprite.texture.file_path.name} не существует!"
                    )

            return slide_offset

        def effect(self, sprite: Sprite, target_alpha: int = 255):

            duration = max(self.duration * self.g.sm.Volume.fade_speed, 0.001)

            start_pos = (sprite.center_x, sprite.center_y)

            slide_offset = self._get_slide_offset(start_pos, sprite)

            sprite.center_x, sprite.center_y = slide_offset

            start_alpha = sprite.alpha
            progress = 0.0

            while progress < 1.0:
                dt = yield

                if dt is None or dt <= 0:
                    continue

                progress = min(progress + dt / duration, 1.0)
                progress_dissolve_ease = self._effect(
                    progress, self.ease_dissolve_effect
                )
                progress_slide_ease = self._effect(progress, self.ease_slide_effect)

                new_alpha = round(
                    start_alpha + (target_alpha - start_alpha) * progress_dissolve_ease
                )
                new_x = (
                    slide_offset[0]
                    + (start_pos[0] - slide_offset[0]) * progress_slide_ease
                )
                new_y = (
                    slide_offset[1]
                    + (start_pos[1] - slide_offset[1]) * progress_slide_ease
                )
                sprite.center_x = round(new_x)
                sprite.center_y = round(new_y)

                sprite.alpha = new_alpha

        def effect_show_sprite(self, new_sprite: Sprite, old_sprite_name: str):

            use_old_sprite = False
            if old_sprite_name in self.g.scene["sprites"]:
                old_sprite = self.g.scene.get_scene_sprite(old_sprite_name, "sprites")
                use_old_sprite = True

            start_new = new_sprite.alpha
            if use_old_sprite:
                start_old = old_sprite.alpha

            duration_new = max(self.duration * self.g.sm.Volume.fade_speed, 0.001)
            duration_old = duration_new * 2  # в два раза медленнее

            total_duration = duration_old

            start_pos = (new_sprite.center_x, new_sprite.center_y)

            slide_offset = self._get_slide_offset(start_pos, new_sprite)

            new_sprite.center_x, new_sprite.center_y = slide_offset

            elapsed = 0.0
            progress = 0.0

            while progress < 1.0:
                dt = yield

                if dt is None or dt <= 0:
                    continue

                elapsed += dt

                if use_old_sprite:
                    progress = min(elapsed / total_duration, 1.0)
                    progress_new = min(progress * 2, 1.0)
                else:
                    progress = min(elapsed / duration_new, 1.0)
                    progress_new = min(progress, 1.0)

                progress_ease_new = self._effect(
                    progress_new, self.ease_dissolve_effect
                )
                progress_ease_old = self._effect(progress, self.ease_dissolve_effect)

                new_sprite.alpha = round(
                    start_new + (255 - start_new) * progress_ease_new
                )
                if use_old_sprite:
                    old_sprite.alpha = round(
                        start_old + (0 - start_old) * progress_ease_old
                    )

                progress_slide_ease = self._effect(progress_new, self.ease_slide_effect)

                new_x = (
                    slide_offset[0]
                    + (start_pos[0] - slide_offset[0]) * progress_slide_ease
                )
                new_y = (
                    slide_offset[1]
                    + (start_pos[1] - slide_offset[1]) * progress_slide_ease
                )
                new_sprite.center_x = round(new_x)
                new_sprite.center_y = round(new_y)
