import arcade.gui
import warnings
from typing_extensions import override
from arcade.gui.widgets.slider import UISliderStyle, UIBaseSlider
import arcade
from typing import Optional, List, Tuple, Union
from arcade import uicolor
from arcade.gui.events import UIMousePressEvent, UIMouseReleaseEvent, UIMouseMovementEvent, UIMouseDragEvent, UIOnUpdateEvent
from arcade.gui import (
    Surface,
    UIEvent,
    UIMouseDragEvent
)
from arcade.gui.style import UIStyledWidget


class UISliderVertical(UIStyledWidget[UISliderStyle], UIBaseSlider):
    """A simple vertical slider.

    A slider consists of a vertical track and a thumb.
    The thumb can be moved along the track to set the value of the slider.

    Use the `on_change` event to get notified about value changes.

    There are four states of the UISlider i.e. normal, hovered, pressed and disabled.

    Args:
        value: Current value of the cursor of the slider.
        min_value: Minimum value of the slider.
        max_value: Maximum value of the slider.
        x: x coordinate of bottom left.
        y: y coordinate of bottom left.
        width: Width of the slider.
        height: Height of the slider.
        style: Used to style the slider for different states.
        step: Smallest change the slider value can move by.
    """

    UIStyle = UISliderStyle

    DEFAULT_STYLE = {
        "normal": UIStyle(),
        "hover": UIStyle(
            border=uicolor.BLUE_PETER_RIVER,
            border_width=2,
            filled_track=uicolor.BLUE_PETER_RIVER,
            filled_step=uicolor.DARK_BLUE_MIDNIGHT_BLUE,
        ),
        "press": UIStyle(
            bg=uicolor.BLUE_PETER_RIVER,
            border=uicolor.DARK_BLUE_WET_ASPHALT,
            border_width=3,
            filled_track=uicolor.BLUE_PETER_RIVER,
            filled_step=uicolor.DARK_BLUE_MIDNIGHT_BLUE,
        ),
        "disabled": UIStyle(
            bg=uicolor.WHITE_SILVER,
            border_width=1,
            filled_track=uicolor.GRAY_ASBESTOS,
            unfilled_track=uicolor.WHITE_SILVER,
        ),
    }

    NO_STEP_STYLE = {
        "normal": UIStyle(
            filled_step=None,
            unfilled_step=None,
        ),
        "hover": UIStyle(
            border=uicolor.BLUE_PETER_RIVER,
            border_width=2,
            filled_track=uicolor.BLUE_PETER_RIVER,
            filled_step=None,
            unfilled_step=None,
        ),
        "press": UIStyle(
            bg=uicolor.BLUE_PETER_RIVER,
            border=uicolor.DARK_BLUE_WET_ASPHALT,
            border_width=3,
            filled_track=uicolor.BLUE_PETER_RIVER,
            filled_step=None,
            unfilled_step=None,
        ),
        "disabled": UIStyle(
            bg=uicolor.WHITE_SILVER,
            border_width=1,
            filled_track=uicolor.GRAY_ASBESTOS,
            unfilled_track=uicolor.WHITE_SILVER,
            filled_step=None,
            unfilled_step=None,
        ),
    }
    """Removing the step colors from the style.
    So sliders with a step value do not show the steps visually."""

    def __init__(
            self,
            *,
            value: float = 0,
            min_value: float = 0,
            max_value: float = 100,
            x: float = 0,
            y: float = 0,
            width: float = 25,
            height: float = 300,
            size_hint=None,
            size_hint_min=None,
            size_hint_max=None,
            style: dict[str, UISliderStyle] | None = None,
            step: float | None = None,
            thumb_edge_padding_factor: float = 1.0,  # Новый параметр
            **kwargs,
    ):
        # Используем NO_STEP_STYLE если step не задан
        if step is None:
            style = style or UISliderVertical.NO_STEP_STYLE
        else:
            style = style or UISliderVertical.DEFAULT_STYLE

        super().__init__(
            value=value,
            min_value=min_value,
            max_value=max_value,
            x=x,
            y=y,
            width=width,
            height=height,
            size_hint=size_hint,
            size_hint_min=size_hint_min,
            size_hint_max=size_hint_max,
            style=style,
            step=step,
            **kwargs,
        )

        # Инициализируем состояния
        self.hovered = False
        self.pressed = False
        self.thumb_edge_padding_factor = thumb_edge_padding_factor

    @property
    def _cursor_height(self) -> int:
        """Высота курсора/ползунка."""
        return min(self.content_width, self.content_height // 10)

    @property
    def _thumb_y(self) -> float:
        """Текущая Y-координата ползунка."""
        return self._y_for_value(self.value)

    def _y_for_value(self, value: float) -> float:
        """Конвертирует значение в Y-координату."""
        normalized_value = (value - self.min_value) / (self.max_value - self.min_value)
        # Для вертикального слайдера: min_value внизу, max_value вверху
        # Инвертируем, так как в Arcade координаты растут снизу вверх
        return self.content_rect.bottom + (1 - normalized_value) * self.content_height

    def _value_for_y(self, y: float) -> float:
        """Конвертирует Y-координату в значение слайдера."""
        normalized_y = (y - self.content_rect.bottom) / self.content_height
        # Ограничиваем значения между 0 и 1
        normalized_y = max(0, min(1, normalized_y))
        # Для вертикального слайдера: y=bottom соответствует max_value, y=top соответствует min_value
        # Инвертируем, так как в Arcade координаты растут снизу вверх
        return self.min_value + (1 - normalized_y) * (self.max_value - self.min_value)

    @override
    def get_current_state(self) -> str:
        """Get the current state of the slider.

        Returns:
            "normal", "hover", "press" or "disabled".
        """
        if self.disabled:
            return "disabled"
        elif self.pressed:
            return "press"
        elif self.hovered:
            return "hover"
        else:
            return "normal"

    @override
    def _render_track(self, surface: Surface):
        style = self.get_current_style()
        if style is None:
            warnings.warn(f"No style found for state {self.get_current_state()}", UserWarning)
            return

        bg_slider_color = style.unfilled_track
        fg_slider_color = style.filled_track

        slider_width = self.content_width // 3
        slider_left = (self.content_width - slider_width) // 2
        slider_right = slider_left + slider_width
        slider_bottom = self.content_rect.bottom
        slider_top = self.content_rect.top

        cursor_radius = self._cursor_height // 2

        # Используем тот же коэффициент отступа
        padding = cursor_radius * self.thumb_edge_padding_factor

        # Текущая позиция ползунка
        thumb_y = self._thumb_y - self.content_rect.bottom

        # Ограничиваем позицию кружка для трека
        max_y = self.content_height - padding
        min_y = padding
        thumb_y = max(min_y, min(max_y, thumb_y))

        # Рисуем заполненную часть трека
        if thumb_y > slider_bottom:
            arcade.draw_lrbt_rectangle_filled(
                left=slider_left,
                right=slider_right,
                bottom=slider_bottom - self.content_rect.bottom,
                top=thumb_y - padding,  # Используем padding вместо cursor_radius
                color=fg_slider_color
            )

        # Рисуем незаполненную часть трека
        if slider_top > thumb_y:
            arcade.draw_lrbt_rectangle_filled(
                left=slider_left,
                right=slider_right,
                bottom=thumb_y + padding,  # Используем padding вместо cursor_radius
                top=slider_top - self.content_rect.bottom,
                color=bg_slider_color
            )

    @override
    def _render_steps(self, surface: Surface):
        if not self.step:
            return

        style = self.get_current_style()
        if style is None:
            warnings.warn(f"No style found for state {self.get_current_state()}", UserWarning)
            return

        unfilled_steps = style.unfilled_step
        filled_steps = style.filled_step

        def float_range(start, stop, step):
            current = start
            while current <= stop:
                yield current
                current += step

        steps = list(float_range(self.min_value, self.max_value, self.step))

        for v in steps:
            step_y = self._y_for_value(v) - self.content_rect.bottom
            step_color = filled_steps if v <= self.value else unfilled_steps

            if step_color:
                # bigger circle for first and last step
                circle_size = self._cursor_height // 4
                if v in (steps[0], steps[-1]):
                    circle_size = self._cursor_height // 3

                arcade.draw_circle_filled(
                    self.content_width // 2,
                    step_y,
                    circle_size,
                    step_color,
                    num_segments=8,
                )

    @override
    def _render_thumb(self, surface: Surface):
        style = self.get_current_style()
        if style is None:
            warnings.warn(f"No style found for state {self.get_current_state()}", UserWarning)
            return

        border_width = style.border_width
        cursor_color = style.bg
        cursor_outline_color = style.border

        cursor_radius = self._cursor_height // 2
        cursor_center_y = self._thumb_y - self.content_rect.bottom
        slider_center_x = self.content_width // 2

        # Используем коэффициент отступа
        padding = cursor_radius * self.thumb_edge_padding_factor

        # Ограничиваем позицию кружка
        max_y = self.content_height - padding
        min_y = padding

        # Применяем ограничения
        cursor_center_y = max(min_y, min(max_y, cursor_center_y))

        # Рисуем ползунок
        arcade.draw_circle_filled(
            slider_center_x,
            cursor_center_y,
            cursor_radius,
            cursor_color
        )

        # Рисуем внутренний круг
        arcade.draw_circle_filled(
            slider_center_x,
            cursor_center_y,
            cursor_radius // 2,
            cursor_outline_color
        )

        # Рисуем обводку
        arcade.draw_circle_outline(
            slider_center_x,
            cursor_center_y,
            cursor_radius,
            cursor_outline_color,
            border_width,
        )

    @override
    def on_event(self, event: UIEvent) -> bool:
        """Handle UI events for the slider."""
        if isinstance(event, (UIMouseMovementEvent, UIMouseDragEvent)):
            # Обновляем состояние наведения (только если не нажато)
            if not self.pressed:
                old_hovered = self.hovered

                # Ручная проверка попадания точки в прямоугольник
                if self.rect:
                    self.hovered = (
                            self.rect.left <= event.x <= self.rect.right and
                            self.rect.bottom <= event.y <= self.rect.top
                    )
                else:
                    self.hovered = False

                if old_hovered != self.hovered:
                    self.trigger_render()

            # Если слайдер нажат, обновляем значение независимо от позиции мыши
            if self.pressed:
                new_value = self._value_for_y(event.y)
                # Ограничиваем значение в пределах min_value и max_value
                new_value = max(self.min_value, min(self.max_value, new_value))

                if new_value != self.value:
                    self.value = new_value
                    self.trigger_full_render()
                    # Вызываем событие on_change если есть подписчики
                    if hasattr(self, 'on_change') and self.on_change:
                        self.on_change(self.value)
                return True

        elif isinstance(event, UIMousePressEvent):
            # Проверяем, находится ли мышь над слайдером при клике
            is_over = False
            if self.rect:
                is_over = (
                        self.rect.left <= event.x <= self.rect.right and
                        self.rect.bottom <= event.y <= self.rect.top
                )

            if is_over and not self.disabled:
                self.pressed = True
                new_value = self._value_for_y(event.y)
                # Ограничиваем значение в пределах min_value и max_value
                new_value = max(self.min_value, min(self.max_value, new_value))

                if new_value != self.value:
                    self.value = new_value
                    self.trigger_full_render()
                    # Вызываем событие on_change если есть подписчики
                    if hasattr(self, 'on_change') and self.on_change:
                        self.on_change(self.value)
                self.trigger_render()
                return True

        elif isinstance(event, UIMouseReleaseEvent):
            if self.pressed:
                self.pressed = False
                # Обновляем состояние наведения после отпускания
                if self.rect:
                    self.hovered = (
                            self.rect.left <= event.x <= self.rect.right and
                            self.rect.bottom <= event.y <= self.rect.top
                    )
                self.trigger_render()
                return True

        elif isinstance(event, UIOnUpdateEvent):
            # Обновляем состояние наведения (только если не нажато)
            if not self.pressed and hasattr(self, 'ui_manager') and self.ui_manager:
                mouse_x, mouse_y = self.ui_manager.mouse_x, self.ui_manager.mouse_y
                old_hovered = self.hovered

                if self.rect:
                    self.hovered = (
                            self.rect.left <= mouse_x <= self.rect.right and
                            self.rect.bottom <= mouse_y <= self.rect.top
                    )
                else:
                    self.hovered = False

                if old_hovered != self.hovered:
                    self.trigger_render()

            # Если слайдер нажат, продолжаем отслеживать движение мыши
            # даже если она за пределами слайдера
            if self.pressed and hasattr(self, 'ui_manager') and self.ui_manager:
                mouse_x, mouse_y = self.ui_manager.mouse_x, self.ui_manager.mouse_y
                # Обновляем значение независимо от позиции мыши
                new_value = self._value_for_y(mouse_y)
                # Ограничиваем значение в пределах min_value и max_value
                new_value = max(self.min_value, min(self.max_value, new_value))

                if new_value != self.value:
                    self.value = new_value
                    self.trigger_full_render()
                    # Вызываем событие on_change если есть подписчики
                    if hasattr(self, 'on_change') and self.on_change:
                        self.on_change(self.value)

        return super().on_event(event)