import arcade.gui as agui
from arcade import cache, Sprite, Texture, color, get_window, LBWH, Scene
from arcade.gui import Surface
from typing import Optional
from PIL import Image

from .fashion_label import FashionUiLabel
from .sliders import UISliderSavesUpdater
from ..globals import g
from ..logger import get_logger
from ..text_converter import Parser
#from ..scene import Scene
from ..waiter import Waiter

logger = get_logger(__name__)

class SettingsManager(agui.UIManager):
    def __init__(self):
        super().__init__()
        self.Views = g.All_main_views

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
        texture = g.fm.get_texture("in_game_settings.png")

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
                g.actions.active_generators.clear()
                g.am.stop_music()
                g.am.stop_sound()

                tex_cache = cache.TextureCache()
                g.scene.clear_scene()
                for i in cache.TextureCache().get_all_textures():
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
            save_button.on_click = lambda action=None, session_id=g.main.session_id: g.sm.Save.create_save(session_id)

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

        self.parser = Parser()

        self.attributes = g.attributes
        self.FONT_NAME = g.FONT_NAME

        self.cname_text: Optional[UiLabelCNameText] = None

        self.strings_list: list[agui.UILabel] = []

        self.texts_widget_manager = agui.UIManager()

        self.last_character_text = self.attributes.character_text.copy()
        self.last_character_name = str(self.attributes.character_name)

        self._create_texts()

    def draw(self, **kwargs) -> None:
        super().draw(**kwargs)
        self.texts_widget_manager.draw(**kwargs)

    def _create_texts(self):
        self.cname_text = UiLabelCNameText(self.attributes, self.FONT_NAME)
        self.add(self.cname_text)

    def update_pos(self, width, height):
        self.cname_text.update_pos(width, height)

    def _get_xpos(self, width):
        if isinstance(self.attributes.text_anchor, str):
            match self.attributes.text_anchor:
                case "left":
                    x_pos = width * 0.18
                case "center":
                    x_pos = width * 0.5
                case "right":
                    x_pos = width * 0.82
                case _:
                    x_pos = width * 0.18
        elif isinstance(self.attributes.text_anchor, (int, float)):
            x_pos = width * self.attributes.text_anchor
        else:
            x_pos = width * 0.18

        return x_pos

    def _get_x(self, x_pos, line_width):
        match self.attributes.text_anchor:
            case "center":
                x = x_pos - line_width / 2
            case "right":
                x = x_pos - line_width
            case _:
                x = x_pos
        return x

    def _get_kargs(self, text_piece):
        kargs = {}

        tag = text_piece["tag"]

        if tag is None:
            return kargs

        tags = list(tag)

        if "b" in tags:
            kargs["bold"] = True
        if "i" in tags:
            kargs["italic"] = True
        if "u" in tags:
            kargs["underline"] = True
        if "s" in tags:
            kargs["stroke"] = True

        return kargs

    def prepare(self):

        if self.last_character_text != self.attributes.character_text:
            logger.debug("preparing text")
            self._prepare_text(self.attributes.character_text)

    def _prepare_text(self, dialogue: list[str]):

        self.strings_list.clear()
        self.texts_widget_manager.clear()

        self.last_character_text = dialogue.copy()

        if not dialogue[0]:
            return None

        slines = [self.parser.parse(sline)
                  for line in dialogue
                  for sline in self._split_by_length(line, 60)]

        for formatted_sline in slines:

            for text_piece in formatted_sline:
                args = self._get_kargs(text_piece)

                t = FashionUiLabel(
                    align=self.attributes.text_anchor,
                    font_size=30,
                    text_color=self.attributes.character_text_colour,
                    font_name=self.FONT_NAME,
                    **args
                )
                self.texts_widget_manager.add(t)
                self.strings_list.append(t)

    def update_character_text(self):

        if not self.strings_list:
            return None

        win_h = self.window.height
        width = self.window.width
        y_start = win_h * 0.2 - 15
        x_pos = self._get_xpos(width)

        slines = [self.parser.parse(sline)
                  for line in self.attributes.character_text
                  for sline in self._split_by_length(line, 60)]

        text_piece_counter = 0

        for line_counter, formatted_sline in enumerate(slines):

            y_pos = y_start - line_counter * 40 + 35

            line_width = 0

            for i, text_piece in enumerate(formatted_sline):

                if len(self.strings_list) - 1 < text_piece_counter + i:
                    self.prepare()
                    return None

                label = self.strings_list[text_piece_counter + i]
                label.text = text_piece["text"]
                line_width += label._label.content_width

            x = self._get_x(x_pos, line_width)

            for text_piece in formatted_sline:
                label = self.strings_list[text_piece_counter]

                label.left = x
                label.bottom = y_pos

                x += label._label.content_width
                text_piece_counter += 1

    def _split_by_length(self, text, max_length):
        if max_length <= 0:
            raise ValueError("max_length must be positive")
        if len(text) <= max_length:
            return [text]

        parts = []
        words = text.split(" ")
        current_line = []
        current_len = 0

        for word in words:
            word_len = len(word)
            if word_len > max_length:
                if current_line:
                    parts.append(" ".join(current_line))
                    current_line = []
                    current_len = 0
                parts.extend(word[i:i + max_length] for i in range(0, word_len, max_length))
                continue

            new_len = current_len + (1 if current_line else 0) + word_len
            if new_len <= max_length:
                current_line.append(word)
                current_len = new_len
            else:
                if current_line:
                    parts.append(" ".join(current_line))
                current_line = [word]
                current_len = word_len

        if current_line:
            parts.append(" ".join(current_line))


        #print(parts)
        return parts

    def update(self, time_delta):
        super().on_update(time_delta)

        self.update_character_text()

        if self.attributes.character_text != self.last_character_text:
            self.last_character_text = self.attributes.character_text.copy()

        if self.attributes.character_name != self.last_character_name:
            self.cname_text.update_text()
            self.last_character_name = self.attributes.character_name

        if repr(self.attributes.character_name).strip("'") in [
            " ",
            "",
            "\t",
            "\n",
            g.UNSEEN_TEXT_PLACEHOLDER,
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
        self.img = g.fm.get_texture("name_window.png").image.copy()
        self.last_text = attributes.character_name

    def update_text(self):
        self.update_pos()
        self.text = self.attributes.character_name
        self.update_font(
            font_color=self.attributes.character_name_colour
        )

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
