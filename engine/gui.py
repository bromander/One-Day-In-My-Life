import arcade.gui as agui
import warnings
import json
import random
from typing_extensions import override
from arcade.gui.widgets.slider import UISliderStyle, UIBaseSlider
from typing import Optional, List, Tuple, Union
from arcade import (
    Window,
    uicolor,
    Scene,
    load_texture,
    Sprite,
    color,
    View,
    draw_lrbt_rectangle_filled,
    draw_circle_filled,
    draw_circle_outline,
    draw_polygon_filled, Texture,
    check_for_collision_with_list,
    sprite_list, get_sprites_at_point, get_sprites_in_rect,
    SpriteList
)
from arcade.gui.events import UIMousePressEvent, UIMouseReleaseEvent, UIMouseMovementEvent, UIMouseDragEvent, UIOnUpdateEvent
from arcade.gui import (
    Surface,
    UIEvent,
    UIMouseDragEvent, UIOnChangeEvent, UIOnClickEvent,
    UIWidget, UIInteractiveWidget, UISpriteWidget
)
from pyglet.graphics import Batch

from .saves import Saves_manager
from .audio import AudioManager
from .waiter import Waiter
from .character import Attributes


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
            draw_lrbt_rectangle_filled(
                left=slider_left,
                right=slider_right,
                bottom=slider_bottom - self.content_rect.bottom,
                top=thumb_y - padding,  # Используем padding вместо cursor_radius
                color=fg_slider_color
            )

        # Рисуем незаполненную часть трека
        if slider_top > thumb_y:
            draw_lrbt_rectangle_filled(
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
        draw_circle_filled(
            slider_center_x,
            cursor_center_y,
            cursor_radius,
            cursor_color
        )

        # Рисуем внутренний круг
        draw_circle_filled(
            slider_center_x,
            cursor_center_y,
            cursor_radius // 2,
            cursor_outline_color
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

class UISliderSavesUpdater(agui.UISlider):
    def __init__(
            self,
            type: str,
            sm: Saves_manager,
            am: AudioManager,
            value: float = 0,
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
            step: float | None = None
    ):
        super().__init__(
             value = value,
             min_value = min_value,
             max_value = max_value,
             x = x,
             y = y,
             width = width,
             height = height,
             size_hint = size_hint,
             size_hint_min = size_hint_min,
             size_hint_max = size_hint_max,
             style = style,
             step = step)

        self.sm = sm
        self.am = am
        self.type = type
    
    def on_click(self, event: UIOnClickEvent):
        super().on_click(event)
        print(self.type)
        match self.type:
            case "music":
                self.am.music.set_volume(round(self.value / 100, 2))
            case "sound":
                self.am.sound.set_volume(round(self.value / 100, 2))
            case "voice":
                self.am.voice.set_volume(round(self.value / 100, 2))
            case "lps":
                self.sm.Volume.set_other("lps", round(self.value, 2))
            case "fade_speed":
                self.sm.Volume.set_other("fade_speed", round(self.value, 2))
        self.sm.Volume._save_data()

class Managers:

    class SettingsManager(agui.UIManager):
        def __init__(self, MainView_self, Am: AudioManager, Sm: Saves_manager, Wwl, session_id: str, FONT_NAME: str, STYLE_DEFAULT_BUTTON: dict, Views):
            super().__init__()
            self.MainView_self = MainView_self
            self.Views = Views

            self.am = Am
            self.sm = Sm
            self.wwl = Wwl

            self.session_id  = session_id

            self.FONT_NAME = FONT_NAME
            self.STYLE_DEFAULT_BUTTON = STYLE_DEFAULT_BUTTON

            self.settings_scene = Scene()

            self.waiting_settings = Waiter()

            self.settings_v_box = agui.widgets.layout.UIBoxLayout(space_between=10)
            self.settings_v_box_1 = agui.widgets.layout.UIBoxLayout(space_between=10)
            self.settings_v_box_1 = agui.widgets.layout.UIBoxLayout(space_between=10)
            self.settings_h_box = agui.widgets.layout.UIBoxLayout(vertical=False, space_between=20)
            self.settings_h_box.visible = False

            self._create_settings()

        def _create_settings(self):
            texture = load_texture("game/images/gui/in_game_settings.png")

            sprite = Sprite(
                texture,
                center_x=self.window.width * 0.5,
                center_y=self.window.height * 0.5,
                scale=1.0
            )
            self.settings_scene.add_sprite("in_game_settings", sprite)
            self.settings_scene["in_game_settings"].alpha = 0

            def create_settings_buttons():
                with open("game/saves.JSON", "r", encoding="UTF-8") as data:
                    data = json.load(data)
                volumes = data['options']

                def return_to_main_menu(event=None):
                    self.MainView_self.actions.active_generators.clear()

                    self.am.stop_sound()
                    self.am.stop_music()
                    self.am.stop_voice()

                    self.window.set_fullscreen(False)
                    self.window.size = (1024, 786)
                    game = self.Views.GameMenu(show_lc=True)
                    self.window.show_view(game)

                return_button = agui.UIFlatButton(
                    text="Главное меню",
                    width=300,
                    height=50,
                    style=self.STYLE_DEFAULT_BUTTON
                )
                return_button.on_click = return_to_main_menu
                self.settings_v_box.add(return_button)

                save_button = agui.UIFlatButton(
                    text="Сохранить",
                    width=200,
                    style=self.STYLE_DEFAULT_BUTTON
                )
                save_button.on_click = lambda action=None, session_id=self.session_id, am=self.am, scene=self.MainView_self.scene, NAMESPACE=self.MainView_self.NAMESPACE, wwl=self.wwl: self.sm.Save.create_save(
                    session_id,
                    am,
                    scene,
                    NAMESPACE,
                    wwl
                )

                self.settings_v_box.add(save_button)

                self.settings_v_box.add(agui.UISpace(height=20))

                music_volume_label = agui.UILabel(
                    "Музыка",
                    text_color=color.WHITE,
                    font_size=20,
                    font_name=self.FONT_NAME
                )
                self.settings_v_box.add(music_volume_label)

                music_volume_slider = UISliderSavesUpdater(
                    "music",
                    self.sm,
                    self.am,
                    value=volumes['volume']["music"] * 100,  # начальное значение
                    min_value=0,
                    max_value=200,
                    width=300,
                    height=20
                )
                self.settings_v_box.add(music_volume_slider)
                self.settings_v_box.add(agui.UISpace(height=10))

                sound_volume_label = agui.UILabel(
                    "Звуки",
                    text_color=color.WHITE,
                    font_size=20,
                    font_name=self.FONT_NAME
                )
                self.settings_v_box.add(sound_volume_label)

                sound_volume_slider = UISliderSavesUpdater(
                    "sound",
                    self.sm,
                    self.am,
                    value=volumes['volume']["sound"] * 100,  # начальное значение
                    min_value=0,
                    max_value=200,
                    width=300,
                    height=20
                )
                self.settings_v_box.add(sound_volume_slider)
                self.settings_v_box.add(agui.UISpace(height=10))

                voice_volume_label = agui.UILabel(
                    "Голос",
                    text_color=color.WHITE,
                    font_size=20,
                    font_name=self.FONT_NAME
                )
                self.settings_v_box.add(voice_volume_label)

                voice_volume_slider = UISliderSavesUpdater(
                    "voice",
                    self.sm,
                    self.am,
                    value=volumes['volume']["voice"] * 100,  # начальное значение
                    min_value=0,
                    max_value=200,
                    width=300,
                    height=20
                )
                self.settings_v_box.add(voice_volume_slider)

                lps_label = agui.UILabel(
                    "Скорость появления букв",
                    text_color=color.WHITE,
                    font_size=20,
                    font_name=self.FONT_NAME
                )
                self.settings_v_box_1.add(lps_label)
                self.lps_slider = UISliderSavesUpdater(
                    "lps",
                    self.sm,
                    self.am,
                    value=volumes["lps"],  # начальное значение
                    min_value=20,
                    max_value=110,
                    width=300,
                    height=20
                )
                self.settings_v_box_1.add(self.lps_slider)
                self.settings_v_box_1.add(agui.UISpace(height=20))

                fade_speed_label = agui.UILabel(
                    "Скорость переходов",
                    text_color=color.WHITE,
                    font_size=20,
                    font_name=self.FONT_NAME
                )
                self.settings_v_box_1.add(fade_speed_label)
                self.fade_speed_slider = UISliderSavesUpdater(
                    "fade_speed",
                    self.sm,
                    self.am,
                    value=volumes["fade_speed"],  # начальное значение
                    min_value=-10,
                    max_value=10,
                    width=300,
                    height=20
                )
                self.settings_v_box_1.add(self.fade_speed_slider)

                self.settings_h_box.add(self.settings_v_box_1)
                self.settings_h_box.add(self.settings_v_box)

                ui_anchor_layout = agui.widgets.layout.UIAnchorLayout()
                ui_anchor_layout.add(child=self.settings_h_box, anchor_x="left", align_x=80)

                self.add(ui_anchor_layout)

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
        def __init__(self, attributes: Attributes, window: Window, FONT_NAME: str):
            super().__init__(window)
            self.attributes = attributes
            self.window = window
            self.FONT_NAME = FONT_NAME

            self.cname_text = agui.UILabel()

            self.texts_widget = UIWidget()
            self.add(self.texts_widget)

            self.last_character_text = self.attributes.character_text.copy()

            self._create_texts()

        def _create_texts(self):

            def create_cname_text():
                self.cname_text = agui.UILabel(
                    self.attributes.character_name,
                    x=self.window.width * 0.19,
                    y=self.window.height * 0.255,
                    font_size=40,
                    multiline=True,
                    width=1150,
                    text_color=self.attributes.character_name_colour,
                    font_name=self.FONT_NAME
                )
                self.add(self.cname_text)

            create_cname_text()

        def update(self, time_delta):
            super().on_update(time_delta)

            def split_by_length(text, max_length):
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
                            parts.append(word[i:i + max_length])
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

            if self.attributes.character_text != self.last_character_text:

                self.remove(self.texts_widget)

                self.texts_widget = UIWidget()

                self.last_character_text = self.attributes.character_text.copy()

                line_counter = 0

                if isinstance(self.attributes.text_anchor, str):
                    match self.attributes.text_anchor:
                        case "left":
                            x_pos = self.window.width * 0.18
                        case "center":
                            x_pos = self.window.width * 0
                        case "right":
                            x_pos = self.window.width * 0.82
                        case _:
                            x_pos = self.window.width * 0.18
                elif isinstance(self.attributes.text_anchor, (int, float)):
                    x_pos = self.window.width * self.attributes.text_anchor
                else:
                    x_pos = self.window.width * 0.18

                for i, line in enumerate(self.attributes.character_text):
                    split_lines = split_by_length(line, 60)

                    for sline in split_lines:
                        y_pos = (self.window.height * 0.2) - line_counter * 40

                        t = agui.UILabel(
                            text=sline,
                            x=x_pos,
                            y=y_pos,
                            font_size=30,
                            text_color=self.attributes.character_text_colour,
                            font_name=self.FONT_NAME,
                            width=self.window.width,
                            align=self.attributes.text_anchor
                        )
                        line_counter += 1

                        self.texts_widget.add(t)

                self.add(self.texts_widget)

    class InGameManager(agui.UIManager):
        def __init__(self, FONT_NAME, window: Window):
            super().__init__(window)
            self.window = window
            self.BUTTONS_STYLE = {
                "normal": agui.UIFlatButton.UIStyle(
                    bg=(0, 0, 0, 0),
                    font_color=(255, 255, 255, 255),
                    font_name=FONT_NAME,
                    border=(0, 0, 0, 0),
                    border_width=0,
                    font_size=20
                ),
                "hover": agui.UIFlatButton.UIStyle(
                    bg=(0, 0, 0, 0),
                    font_color=(128, 128, 128, 255),
                    border=(0, 0, 0, 0),
                    border_width=0,
                    font_name = FONT_NAME,
                    font_size=20
                ),
                "press": agui.UIFlatButton.UIStyle(
                    bg=(0, 0, 0, 0),
                    font_color=(210, 210, 210, 255),
                    border=(0, 0, 0, 0),
                    border_width=0,
                    font_name = FONT_NAME,
                    font_size=20
                ),
                "disabled": agui.UIFlatButton.UIStyle(font_color=(90, 90, 90, 180)),
            }
            self._create_buttons()

        def _create_buttons(self):
            hbox = agui.UIBoxLayout(
                align="center",
                justify="center",
                y=self.window.height * 0.02,
                width=self.window.width,
                vertical=False,
                spacing=50
            )
            hbox.width = self.window.width

            button_width = 60

            #self.return_button = agui.UIFlatButton(
            #    text="←",
            #    style=self.BUTTONS_STYLE,
            #    width=button_width
            #)
            #hbox.add(self.return_button)

            self.skip_button = agui.UIFlatButton(
                text=">>",
                style=self.BUTTONS_STYLE,
                width=button_width
            )
            hbox.add(self.skip_button)

            self.settings_button = agui.UIFlatButton(
                text="☰",
                style=self.BUTTONS_STYLE,
                width=button_width
            )
            hbox.add(self.settings_button)

            ui_anchor_layout = agui.UIAnchorLayout()
            ui_anchor_layout.add(child=hbox, anchor_x="center_x", anchor_y="bottom")

            self.add(ui_anchor_layout)


class MovableBlock(UISpriteWidget):
    def __init__(self, sprite, center_x = 0, center_y = 0, size=50):
        super().__init__(sprite=sprite)
        print(sprite)
        self.center_x = center_x
        self.center_y = center_y
        self.size = (size, size)
        self.size_default = size
        self.clicked = False
        self.disabled = False


    def on_event(self, event: UIEvent) -> bool | None:
        if type(event) is UIMousePressEvent:
            if self.rect.left <= event.x <= self.rect.right and self.rect.bottom <= event.y <= self.rect.top:
                if list(self.get_ui_manager().get_widgets_at((event.x, event.y), MovableBlock))[-1] is self:
                    self.clicked = True
                    #self.scale(1.5)

        if type(event) is UIMouseReleaseEvent:
            #if self.clicked:
                #self.scale(0.667)
            self.clicked = False
        if type(event) is UIOnUpdateEvent:
            if (self.get_ui_manager().window.width * 0.1 <= self.center_x <= self.get_ui_manager().window.width * 0.2
                    and self.get_ui_manager().window.height * 0.35 <= self.center_y <= self.get_ui_manager().window.height * 0.65):
                if not self.disabled and not self.clicked:
                    self.center_x = self.get_ui_manager().window.width * 0.15 + random.randint(-50, 50)
                    self.center_y = self.get_ui_manager().window.height * 0.5 + random.randint(-110, 110)
                    self.disabled  = True
            else:
                self.disabled = False

            if self.clicked:
                self.center_x = self.get_ui_manager().window._mouse_x
                self.center_y = self.get_ui_manager().window._mouse_y

