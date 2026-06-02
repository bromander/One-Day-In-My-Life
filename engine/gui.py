import arcade.cache
import arcade.gui as agui
import warnings
import random
from PIL import Image
from typing_extensions import override
from arcade.gui.widgets.slider import UISliderStyle, UIBaseSlider
from typing import Optional
from arcade import (
    uicolor,
    Scene,
    load_texture,
    Sprite,
    color,
    draw_lrbt_rectangle_filled,
    draw_circle_filled,
    draw_circle_outline,
    Texture,
    get_sprites_at_point,
    LBWH,
    Text,
    get_window,
)
from arcade.gui.events import (
    UIMousePressEvent,
    UIMouseReleaseEvent,
    UIMouseMovementEvent,
    UIOnUpdateEvent,
)
from arcade.gui import Surface, UIEvent, UIMouseDragEvent, UIWidget

from .waiter import Waiter

from .globals import g


class UISliderVertical(agui.style.UIStyledWidget[UISliderStyle], UIBaseSlider):
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
            warnings.warn(
                f"No style found for state {self.get_current_state()}", UserWarning
            )
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
            draw_lrbt_rectangle_filled(
                left=slider_left,
                right=slider_right,
                bottom=slider_bottom - self.content_rect.bottom,
                top=thumb_y - padding,  # Используем padding вместо cursor_radius
                color=fg_slider_color,
            )

        # Рисуем незаполненную часть трека
        if slider_top > thumb_y:
            draw_lrbt_rectangle_filled(
                left=slider_left,
                right=slider_right,
                bottom=thumb_y + padding,  # Используем padding вместо cursor_radius
                top=slider_top - self.content_rect.bottom,
                color=bg_slider_color,
            )

    @override
    def _render_steps(self, surface: Surface):
        if not self.step:
            return

        style = self.get_current_style()
        if style is None:
            warnings.warn(
                f"No style found for state {self.get_current_state()}", UserWarning
            )
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

                draw_circle_filled(
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
            warnings.warn(
                f"No style found for state {self.get_current_state()}", UserWarning
            )
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
        draw_circle_filled(
            slider_center_x, cursor_center_y, cursor_radius, cursor_color
        )

        # Рисуем внутренний круг
        draw_circle_filled(
            slider_center_x, cursor_center_y, cursor_radius // 2, cursor_outline_color
        )

        # Рисуем обводку
        draw_circle_outline(
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
                        self.rect.left <= event.x <= self.rect.right
                        and self.rect.bottom <= event.y <= self.rect.top
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
                    if hasattr(self, "on_change") and self.on_change:
                        self.on_change(self.value)
                return True

        elif isinstance(event, UIMousePressEvent):
            # Проверяем, находится ли мышь над слайдером при клике
            is_over = False
            if self.rect:
                is_over = (
                    self.rect.left <= event.x <= self.rect.right
                    and self.rect.bottom <= event.y <= self.rect.top
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
                    if hasattr(self, "on_change") and self.on_change:
                        self.on_change(self.value)
                self.trigger_render()
                return True

        elif isinstance(event, UIMouseReleaseEvent):
            if self.pressed:
                self.pressed = False
                # Обновляем состояние наведения после отпускания
                if self.rect:
                    self.hovered = (
                        self.rect.left <= event.x <= self.rect.right
                        and self.rect.bottom <= event.y <= self.rect.top
                    )
                self.trigger_render()
                return True

        elif isinstance(event, UIOnUpdateEvent):
            # Обновляем состояние наведения (только если не нажато)
            if not self.pressed and hasattr(self, "ui_manager") and self.ui_manager:
                mouse_x, mouse_y = self.ui_manager.mouse_x, self.ui_manager.mouse_y
                old_hovered = self.hovered

                if self.rect:
                    self.hovered = (
                        self.rect.left <= mouse_x <= self.rect.right
                        and self.rect.bottom <= mouse_y <= self.rect.top
                    )
                else:
                    self.hovered = False

                if old_hovered != self.hovered:
                    self.trigger_render()

            # Если слайдер нажат, продолжаем отслеживать движение мыши
            # даже если она за пределами слайдера
            if self.pressed and hasattr(self, "ui_manager") and self.ui_manager:
                mouse_x, mouse_y = self.ui_manager.mouse_x, self.ui_manager.mouse_y
                # Обновляем значение независимо от позиции мыши
                new_value = self._value_for_y(mouse_y)
                # Ограничиваем значение в пределах min_value и max_value
                new_value = max(self.min_value, min(self.max_value, new_value))

                if new_value != self.value:
                    self.value = new_value
                    self.trigger_full_render()
                    # Вызываем событие on_change если есть подписчики
                    if hasattr(self, "on_change") and self.on_change:
                        self.on_change(self.value)

        return super().on_event(event)


class UISliderSavesUpdater(agui.UISlider):
    def __init__(
        self,
        type: str,
        value: float = 0,
        start_value: Optional[float] = None,
        min_value: float = 0,
        max_value: float = 100,
        x: float = 0,
        y: float = 0,
        width: float = 300,
        height: float = 25,
        size_hint=None,
        size_hint_min=None,
        size_hint_max=None,
        style: dict[str, UISliderStyle] | None = None,
        step: float | None = None,
    ):
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
        )

        self.sm = g.sm
        self.am = g.am
        self.type = type

        self.start_value = start_value

        self.directed = False

    def do_render(self, surface: Surface):
        super().do_render(surface)

        if self.start_value:
            self._render_start_pos(surface)

    def _render_start_pos(self, surface: Surface):
        if self.start_value is None:
            return

        if self.step:
            steps_count = round((self.start_value - self.min_value) / self.step)
            start_value = self.min_value + steps_count * self.step
        else:
            start_value = self.start_value

        value_ratio = (start_value - self.min_value) / (self.max_value - self.min_value)

        slider_left_x = self._x_for_value(self.min_value) - self.content_rect.left
        slider_right_x = self._x_for_value(self.max_value) - self.content_rect.left
        track_width = slider_right_x - slider_left_x

        start_x = slider_left_x + value_ratio * track_width

        slider_height = self.content_height // 3
        slider_bottom = (self.content_height - slider_height) // 2 - 5

        start_color = self.get_current_style().border
        rect_width = max(3, slider_height // 2)

        arcade.draw_lbwh_rectangle_filled(
            start_x - rect_width / 2,
            slider_bottom,
            rect_width,
            slider_height + 10,
            start_color,
        )

    def on_event(self, event: UIEvent) -> bool | None:
        super().on_event(event)

        if UIMouseMovementEvent is type(event):
            if self in [
                i for i in self.get_ui_manager().get_widgets_at((event.x, event.y))
            ]:
                self.directed = True
            else:
                self.directed = False

        if UIMouseReleaseEvent is type(event) and self.directed:
            match self.type:
                case "music":
                    self.am.music.set_volume(round(self.value / 100, 2))
                case "sound":
                    self.am.sound.set_volume(round(self.value / 100, 2))
                case "voice":
                    self.am.voice.set_volume(round(self.value / 100, 2))
                case "lps":
                    self.sm.Volume.lps = self.value
                case "fade_speed":
                    self.sm.Volume.fade_speed = self.value
            self.sm.Volume._save_data()


class Managers:
    class SettingsManager(agui.UIManager):
        def __init__(self):
            super().__init__()
            self.Views = g.All_views

            self.settings_scene = Scene()

            self.waiting_settings = Waiter()

            self.settings_v_box = agui.UIBoxLayout(space_between=10)
            self.settings_v_box_1 = agui.UIBoxLayout(space_between=10)
            self.settings_v_box_1 = agui.UIBoxLayout(space_between=10)
            self.settings_h_box = agui.UIBoxLayout(vertical=False, space_between=20)
            self.settings_h_box.visible = False

            self.ui_anchor_layout = agui.UIAnchorLayout()

            self._create_settings()

        def update_size(self, width, height):
            self.ui_anchor_layout.default_anchor_x = height * 0.05

        def _create_settings(self):
            texture = load_texture("game/images/gui/in_game_settings.png")

            sprite = Sprite(
                texture,
                center_x=self.window.width * 0.5,
                center_y=self.window.height * 0.5,
                scale=1.0,
            )
            self.settings_scene.add_sprite("in_game_settings", sprite)
            self.settings_scene["in_game_settings"].alpha = 0

            def create_settings_buttons():

                volumes = g.sm.Volume

                def return_to_main_menu(event=None):

                    self.window.set_fullscreen(True)
                    g.main.actions.active_generators.clear()
                    g.am.stop_music()
                    g.am.stop_sound()

                    tex_cache = arcade.cache.TextureCache()
                    g.scene.clear_scene()
                    for i in arcade.cache.TextureCache().get_all_textures():
                        tex_cache.delete(i)

                    self.window.set_fullscreen(False)
                    self.window.size = (1024, 786)
                    self.window.center_window()
                    game = self.Views.GameMenu(show_lc=True)
                    self.window.show_view(game)

                return_button = agui.UIFlatButton(
                    text="Главное меню",
                    width=300,
                    height=50,
                    style=g.STYLE_DEFAULT_BUTTON,
                )
                return_button.on_click = return_to_main_menu
                self.settings_v_box.add(return_button)

                save_button = agui.UIFlatButton(
                    text="Сохранить", width=200, style=g.STYLE_DEFAULT_BUTTON
                )
                save_button.on_click = lambda action=None: g.sm.Save.create_save()

                self.settings_v_box.add(save_button)

                self.settings_v_box.add(agui.UISpace(height=20))

                music_volume_label = agui.UILabel(
                    "Музыка",
                    text_color=color.WHITE,
                    font_size=20,
                    font_name=g.FONT_NAME,
                )
                self.settings_v_box.add(music_volume_label)

                music_volume_slider = UISliderSavesUpdater(
                    "music",
                    value=volumes.music * 100,  # начальное значение
                    min_value=0,
                    max_value=200,
                    width=300,
                    height=20,
                    start_value=g.DEFAULT_OPTIONS_PARAM["volume"]["music"] * 100,
                )
                self.settings_v_box.add(music_volume_slider)
                self.settings_v_box.add(agui.UISpace(height=10))

                sound_volume_label = agui.UILabel(
                    "Звуки", text_color=color.WHITE, font_size=20, font_name=g.FONT_NAME
                )
                self.settings_v_box.add(sound_volume_label)

                sound_volume_slider = UISliderSavesUpdater(
                    "sound",
                    value=volumes.sound * 100,  # начальное значение
                    min_value=0,
                    max_value=200,
                    width=300,
                    height=20,
                    start_value=g.DEFAULT_OPTIONS_PARAM["volume"]["sound"] * 100,
                )
                self.settings_v_box.add(sound_volume_slider)
                self.settings_v_box.add(agui.UISpace(height=10))

                voice_volume_label = agui.UILabel(
                    "Голос", text_color=color.WHITE, font_size=20, font_name=g.FONT_NAME
                )
                self.settings_v_box.add(voice_volume_label)

                """voice_volume_slider = UISliderSavesUpdater(
                    "voice",
                    g.sm,
                    g.am,
                    value=volumes.voice * 100,  # начальное значение
                    min_value=0,
                    max_value=200,
                    width=300,
                    height=20,
                    start_value=g.DEFAULT_OPTIONS_PARAM["volume"]["voice"]*100
                )
                self.settings_v_box.add(voice_volume_slider)"""

                lps_label = agui.UILabel(
                    "Скорость появления букв",
                    text_color=color.WHITE,
                    font_size=20,
                    font_name=g.FONT_NAME,
                )
                self.settings_v_box_1.add(lps_label)
                self.lps_slider = UISliderSavesUpdater(
                    "lps",
                    value=volumes.lps,  # начальное значение
                    min_value=0.1,
                    max_value=3.0,
                    width=300,
                    height=20,
                    start_value=g.DEFAULT_OPTIONS_PARAM["lps"],
                )
                self.settings_v_box_1.add(self.lps_slider)
                self.settings_v_box_1.add(agui.UISpace(height=20))

                fade_speed_label = agui.UILabel(
                    "Скорость переходов",
                    text_color=color.WHITE,
                    font_size=20,
                    font_name=g.FONT_NAME,
                )
                self.settings_v_box_1.add(fade_speed_label)
                self.fade_speed_slider = UISliderSavesUpdater(
                    "fade_speed",
                    value=volumes.fade_speed,  # начальное значение
                    min_value=0.0,
                    max_value=2.0,
                    width=300,
                    height=20,
                    start_value=g.DEFAULT_OPTIONS_PARAM["fade_speed"],
                )
                self.settings_v_box_1.add(self.fade_speed_slider)

                self.settings_h_box.add(self.settings_v_box_1)
                self.settings_h_box.add(self.settings_v_box)

                window = get_window()
                self.ui_anchor_layout.add(
                    child=self.settings_h_box,
                    anchor_x="left",
                    align_x=window.height * 0.05,
                )

                self.add(self.ui_anchor_layout)

            create_settings_buttons()

        def _show_settings(self, state: Optional[bool] = None):

            settings = self.settings_scene["in_game_settings"]

            if state is not None:
                turn_on = state
            else:
                turn_on = settings.alpha <= 0

            (self.waiting_settings.on if turn_on else self.waiting_settings.off)()
            self.settings_h_box.visible = turn_on
            settings.alpha = 255 if turn_on else 0

        def draw(self, **kwargs) -> None:
            self.settings_scene.draw()
            super().draw(**kwargs)

        def turn_visibl(self, event=None, state: Optional[bool] = None):
            if state is not None:
                self.waiting_settings.state = state
                self._show_settings(state)
                if state:
                    self.enable()
                else:
                    self.disable()
            else:
                self._show_settings(not self.waiting_settings.state)
                if self.waiting_settings.state:
                    self.enable()
                else:
                    self.disable()

    class CharactersTextManager(agui.UIManager):
        def __init__(self):
            super().__init__()

            self.attributes = g.attributes
            self.FONT_NAME = g.FONT_NAME

            self.cname_text: Optional[Managers.UiLabelCNameText] = None

            self.texts_widget = UIWidget()
            self.add(self.texts_widget)

            self.last_character_text = self.attributes.character_text.copy()
            self.last_character_name = str(self.attributes.character_name)

            self._create_texts()

        def _create_texts(self):
            self.cname_text = Managers.UiLabelCNameText(self.attributes, self.FONT_NAME)
            self.add(self.cname_text)

        def update_pos(self, width, height):
            self.cname_text.update_pos(width, height)
            self.update_character_text(width, height)

        def update_character_text(
            self, width: Optional[int] = None, height: Optional[int] = None
        ):

            if not (width and height):
                window = get_window()
                width = window.width
                height = window.height

            self.remove(self.texts_widget)

            self.texts_widget = UIWidget()

            self.last_character_text = self.attributes.character_text.copy()

            line_counter = 0

            if isinstance(self.attributes.text_anchor, str):
                match self.attributes.text_anchor:
                    case "left":
                        x_pos = width * 0.18
                    case "center":
                        x_pos = width * 0
                    case "right":
                        x_pos = width * 0.82
                    case _:
                        x_pos = width * 0.18
            elif isinstance(self.attributes.text_anchor, (int, float)):
                x_pos = width * self.attributes.text_anchor
            else:
                x_pos = width * 0.18

            for i, line in enumerate(self.attributes.character_text):
                split_lines = self._split_by_length(line, 60)

                for sline in split_lines:
                    y_pos = (self.window.height * 0.2) - line_counter * 40

                    t = agui.UILabel(
                        text=sline,
                        x=x_pos,
                        y=y_pos,
                        font_size=30,
                        text_color=self.attributes.character_text_colour,
                        font_name=self.FONT_NAME,
                        width=width,
                        align=self.attributes.text_anchor,
                    )
                    line_counter += 1

                    self.texts_widget.add(t)

            self.add(self.texts_widget)

        def _split_by_length(self, text, max_length):
            if len(text) <= max_length:
                return [text]

            parts = []
            words = text.split(" ")
            current_line = []

            for word in words:
                if len(word) > max_length:
                    if current_line:
                        parts.append(" ".join(current_line))
                        current_line = []

                    for i in range(0, len(word), max_length):
                        parts.append(word[i : i + max_length])
                else:
                    test_line = " ".join(current_line + [word])
                    if len(test_line) <= max_length:
                        current_line.append(word)
                    else:
                        if current_line:
                            parts.append(" ".join(current_line))
                        current_line = [word]

            if current_line:
                parts.append(" ".join(current_line))

            return parts

        def update(self, time_delta):
            super().on_update(time_delta)

            if self.attributes.character_text != self.last_character_text:
                self.update_character_text()

            if self.attributes.character_name != self.last_character_name:
                self.cname_text.update_text(self.attributes.character_name)
                self.cname_text.update_font(
                    font_color=self.attributes.character_name_colour
                )

            if repr(self.attributes.character_name).strip("'") in [
                " ",
                "",
                "\t",
                "\n",
                " ",
            ]:
                self.cname_text.visible = None
            else:
                self.cname_text.update_pos()
                self.cname_text.visible = True

    class InGameManager(agui.UIManager):
        def __init__(self):
            super().__init__()
            self.autoskip_waiter = g.main.waiting_autoskip
            self.last_autoskip_waiter_data = None
            self.BUTTONS_STYLE = {
                "normal": agui.UIFlatButton.UIStyle(
                    bg=(0, 0, 0, 0),
                    font_color=(255, 255, 255, 200),
                    font_name=g.FONT_NAME,
                    border=(0, 0, 0, 0),
                    border_width=0,
                    font_size=20,
                ),
                "hover": agui.UIFlatButton.UIStyle(
                    bg=(0, 0, 0, 0),
                    font_color=(128, 128, 128, 200),
                    border=(0, 0, 0, 0),
                    border_width=0,
                    font_name=g.FONT_NAME,
                    font_size=20,
                ),
                "press": agui.UIFlatButton.UIStyle(
                    bg=(0, 0, 0, 0),
                    font_color=(210, 210, 210, 200),
                    border=(0, 0, 0, 0),
                    border_width=0,
                    font_name=g.FONT_NAME,
                    font_size=20,
                ),
                "disabled": agui.UIFlatButton.UIStyle(font_color=(90, 90, 90, 180)),
            }
            self.BUTTONS_STYLE_ON_STATE = {
                "normal": agui.UIFlatButton.UIStyle(
                    bg=(0, 0, 0, 0),
                    font_color=(191, 161, 27, 255),
                    font_name=g.FONT_NAME,
                    border=(255, 255, 255, 0),
                    border_width=0,
                    font_size=20,
                ),
                "hover": agui.UIFlatButton.UIStyle(
                    bg=(0, 0, 0, 0),
                    font_color=(128, 128, 128, 255),
                    border=(255, 255, 255, 0),
                    border_width=0,
                    font_name=g.FONT_NAME,
                    font_size=20,
                ),
                "press": agui.UIFlatButton.UIStyle(
                    bg=(0, 0, 0, 0),
                    font_color=(210, 210, 210, 255),
                    border=(255, 255, 255, 0),
                    border_width=0,
                    font_name=g.FONT_NAME,
                    font_size=20,
                ),
                "disabled": agui.UIFlatButton.UIStyle(font_color=(90, 90, 90, 180)),
            }

            self._create_buttons()

        def _create_buttons(self):
            window = get_window()

            hbox = agui.UIBoxLayout(
                align="center",
                justify="center",
                y=window.height * 0.02,
                width=window.width,
                vertical=False,
                spacing=50,
            )
            hbox.width = window.width

            button_width = 60

            self.return_button = agui.UIFlatButton(
                text="←", style=self.BUTTONS_STYLE, width=button_width
            )
            hbox.add(self.return_button)

            self.skip_button = agui.UIFlatButton(
                text=">>", style=self.BUTTONS_STYLE, width=button_width
            )
            hbox.add(self.skip_button)

            self.settings_button = agui.UIFlatButton(
                text="☰", style=self.BUTTONS_STYLE, width=button_width
            )
            hbox.add(self.settings_button)

            ui_anchor_layout = agui.UIAnchorLayout()
            ui_anchor_layout.add(child=hbox, anchor_x="center_x", anchor_y="bottom")

            self.add(ui_anchor_layout)

        def on_update(self, time_delta):
            super().on_update(time_delta)

            if self.last_autoskip_waiter_data != self.autoskip_waiter.state:
                if self.autoskip_waiter:
                    self.skip_button.style = self.BUTTONS_STYLE_ON_STATE
                else:
                    self.skip_button.style = self.BUTTONS_STYLE
                self.skip_button.trigger_full_render()
                self.last_autoskip_waiter_data = self.autoskip_waiter.state

    class UiLabelCNameText(agui.UILabel):
        def __init__(self, attributes, FONT_NAME):
            window = get_window()
            super().__init__(
                attributes.character_name,
                x=window.width * 0.19,
                y=window.height * 0.32,
                font_size=40,
                text_color=attributes.character_name_colour,
                font_name=FONT_NAME,
            )
            self.attributes = attributes
            self.img = Image.open("./game/images/gui/name_window.png")
            self.last_text = attributes.character_name

        def update_text(self, text):
            self.update_pos()
            self.text = text

        def update_pos(self, height: Optional[int] = None, width: Optional[int] = None):
            if not (height and width):
                window = get_window()
                width = window.width
                height = window.height

            self.center_x = width * 0.19
            self.center_y = height * 0.32

        def _alpha_smooth_img(self, image, r_start, r_end):
            image = image.convert("RGBA")
            width, height = image.size

            cx, _cy = width // 2, height // 2

            alpha = Image.new("L", (width, height), 0)
            pixels = alpha.load()

            for y in range(height):
                for x in range(width):
                    # расстояние до центра
                    dx = abs(x - cx)

                    if dx <= r_start:
                        a = 255
                    elif dx >= r_end:
                        a = 0
                    else:
                        t = (dx - r_start) / (r_end - r_start)
                        a = int(255 * (1 - t))

                    pixels[x, y] = a

            image.putalpha(alpha)
            return image

        def do_render_base(self, surface: Surface):
            surface.limit(
                LBWH(
                    self.rect.left - 25,
                    self.rect.bottom,
                    self.rect.width + 50,
                    self.rect.height,
                )
            )

            if self.attributes.character_name != self.last_text:
                try:
                    self.last_text = str(self.attributes.character_name)
                    self.fit_content()

                    self.img = self.img.resize(
                        (int(self.rect.size[0] + 50), int(self.rect.size[1]))
                    )
                    img = self._alpha_smooth_img(
                        self.img, self.width / 2, self.img.width / 2
                    )
                    self._bg_tex = Texture(img)
                except ValueError:
                    self.last_text = str(self.attributes.character_name)

            if self._bg_tex:
                surface.draw_texture(
                    x=0,
                    y=0,
                    width=self.width + 50,
                    height=self.height,
                    tex=self._bg_tex,
                )


class MovableBlock(Sprite):
    def __init__(
        self,
        texture,
        center_x=0,
        center_y=0,
        angle=0,
        scale=1.0,
        collecting_zone: Optional[tuple] = None,
        collect: bool = False,
    ):
        super().__init__(path_or_texture=texture)
        self.start_x = center_x
        self.start_y = center_y
        self.start_angle = angle + random.randint(-5, 5)
        self.center_x = int(center_x) + random.randint(-30, 30)
        self.center_y = int(center_y) + random.randint(-15, 30)
        color_rand = random.randint(230, 255)
        self.angle = int(self.start_angle)
        self.color = (color_rand, color_rand, color_rand, 255)
        self.scale = scale
        self.scale_x = self.scale_x * random.randint(95, 105) / 100
        self.scale_y = self.scale_y * random.randint(95, 105) / 100

        self.collecting_zone = collecting_zone
        self.collect = collect

        self.clicked = False
        self.freezed = False

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:

        if 1 in args[0]:
            if args[0][1]:
                if (
                    self.left <= args[0]["x"] <= self.right
                    and self.bottom <= args[0]["y"] <= self.top
                ):
                    list_children = []
                    for i in self.sprite_lists:
                        list_children = list_children + list(
                            get_sprites_at_point((args[0]["x"], args[0]["y"]), i)
                        )
                    if len(list_children) > 0:
                        if list_children[-1] is self:
                            self.clicked = True
                    else:
                        self.clicked = True
            else:
                self.clicked = False

        if self.clicked:
            self.angle = 0
            self.center_x = args[0]["x"]
            self.center_y = args[0]["y"]

        if (
            self.collecting_zone[0] <= self.center_x <= self.collecting_zone[1]
            and self.collecting_zone[2] <= self.center_y <= self.collecting_zone[3]
        ):
            if self.collect:
                if not self.clicked:
                    if not self.freezed:
                        self.center_x = random.randint(
                            int(self.collecting_zone[0] + self.width / 2),
                            int(self.collecting_zone[1] - self.width / 2),
                        )
                        self.center_y = random.randint(
                            int(self.collecting_zone[2] + self.height / 2),
                            int(self.collecting_zone[3] - self.height / 2),
                        )
                    self.freezed = True
            else:
                self.center_x = self.start_x
                self.center_y = self.start_y
                self.angle = self.start_angle
                self.freezed = False
        else:
            if self.freezed:
                self.freezed = False


class MovableBlockFalling(Sprite):
    def __init__(self, texture, center_x=0, center_y=0, scale=1.0):
        super().__init__(path_or_texture=texture)
        self.center_x = int(center_x) + random.randint(-30, 30)
        self.center_y = int(center_y) + random.randint(-15, 30)
        # self.scale = scale
        # self.scale_x = self.scale_x * random.randint(95, 105)/100
        # self.scale_y = self.scale_y * random.randint(95, 105) / 100
        color_rand = random.randint(230, 255)
        self.color = (color_rand, color_rand, color_rand, 255)
        self.clicked = False
        self.freeze = True
        self.falling_speed = 0.0

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:

        if 1 in args[0]:
            if args[0][1]:
                if (
                    self.left <= args[0]["x"] <= self.right
                    and self.bottom <= args[0]["y"] <= self.top
                ):
                    list_children = []
                    for i in self.sprite_lists:
                        list_children = list_children + list(
                            get_sprites_at_point((args[0]["x"], args[0]["y"]), i)
                        )
                    if len(list_children) > 0:
                        if list_children[-1] is self:
                            self.clicked = True
                            self.freeze = False
                    else:
                        self.clicked = True
                        self.freeze = False

            else:
                self.clicked = False

        if self.clicked:
            self.center_x = args[0]["x"]
            self.center_y = args[0]["y"]

        if not self.clicked and not self.freeze:
            self.falling_speed = self.falling_speed - 2500 * delta_time
            self.center_y = self.center_y + self.falling_speed * delta_time
        else:
            self.falling_speed = 0.0


class ItemsNotifText(Text):
    def __init__(self, text, x, y, color, FONT_NAME):
        super().__init__(
            text=text, x=x, y=y, color=color, font_size=35, font_name=FONT_NAME
        )
        self.velocity = 0.0
        self.color = (
            self.color[0] + 10 if self.color[0] + 10 <= 255 else self.color[0],
            self.color[1] + 10 if self.color[1] + 10 <= 255 else self.color[1],
            self.color[2] + 10 if self.color[2] + 10 <= 255 else self.color[2],
            225,
        )
        self.bold = True

        self.window = get_window()

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        self.velocity = self.velocity + 200 * delta_time
        self.y = self.y + self.velocity * delta_time

        if self.y > self.window.height + 300:
            self.visible = False


class ClickableSprite(Sprite):
    def __init__(self, textures: list, center_x=0, center_y=0, angle=0, scale=1.0):
        super().__init__(path_or_texture=textures[0])
        self.start_angle = angle + random.randint(-5, 5)
        self.center_x = int(center_x) + random.randint(-30, 30)
        self.center_y = int(center_y) + random.randint(-15, 30)
        color_rand = random.randint(230, 255)
        self.angle = int(self.start_angle)
        self.color = (color_rand, color_rand, color_rand, 255)
        self.scale = scale
        self.scale_x = self.scale_x * random.randint(95, 105) / 100
        self.scale_y = self.scale_y * random.randint(95, 105) / 100

        self.textures = textures
        self.clicked = False

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:

        if 1 in args[0]:
            if args[0][1]:
                if (
                    self.left <= args[0]["x"] <= self.right
                    and self.bottom <= args[0]["y"] <= self.top
                ):
                    list_children = []
                    for i in self.sprite_lists:
                        list_children = list_children + list(
                            get_sprites_at_point((args[0]["x"], args[0]["y"]), i)
                        )
                    if len(list_children) > 0:
                        if list_children[-1] is self:
                            self.clicked = True
                    else:
                        self.clicked = True

            else:
                self.clicked = False

        if self.clicked:
            self.set_texture(1)
        else:
            self.set_texture(0)
