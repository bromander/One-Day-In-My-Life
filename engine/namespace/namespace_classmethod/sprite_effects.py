from typing import Optional
from arcade import Sprite

from .Ease import Ease


class SpriteEffects:
    def __init__(self, g):
        self.Dissolve = lambda duration=1.0, additional_effect="ease_in_out_cubic": (
            self.Dissolve_effect(g, duration, additional_effect)
        )

    class Dissolve_effect:
        def __init__(
            self,
            g,
            duration: float = 1.0,
            additional_effect: Optional[str] = "ease_in_out_cubic",
        ) -> None:
            """
            Отвечает эа эффект растворения
            :param duration: Продолжительность эффекта
            """
            self.name = "DISSOLVE"
            self.duration = duration
            self.additional_effect = additional_effect

            self.g = g

        def _effect(self, t):
            if self.additional_effect:
                return Ease.prepare_effect(self.additional_effect, t)
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

            no_old = False

            if old_sprite_name in self.g.scene["sprites"]:
                old_sprite = self.g.scene.get_scene_sprite(old_sprite_name, "sprites")
            else:
                no_old = True

            duration = max(self.duration * self.g.sm.Volume.fade_speed, 0.001)
            start_new_alpha = new_sprite.alpha

            if not no_old:
                start_old_alpha = old_sprite.alpha

            progress = 0.0

            while progress < 1.0:
                dt = yield

                if dt is None or dt <= 0:
                    continue

                progress = min(progress + dt / duration, 1.0)
                progress_ease = self._effect(progress)

                new_alpha = round(
                    start_new_alpha + (255 - start_new_alpha) * progress_ease
                )
                new_sprite.alpha = new_alpha

                if not no_old:
                    old_alpha = round(
                        start_old_alpha + (0 - start_old_alpha) * progress_ease
                    )
                    old_sprite.alpha = old_alpha
