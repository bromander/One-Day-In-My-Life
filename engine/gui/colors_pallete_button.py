import arcade.gui as agui
from arcade import Texture
import random
from PIL import Image


from ..globals import g


class ColorsPaletteButton(agui.UITextureButton):
    def __init__(self, **kwargs):
        self.now_color = None

        self.frame_texture: Texture = g.fm.get_texture("color_palette_chooser_button_frame.png")
        self.frame_texture_hovered: Texture = g.fm.get_texture("color_palette_chooser_button_frame_hovered.png")
        self.frame_texture_pressed: Texture = g.fm.get_texture("color_palette_chooser_button_frame_pressed.png")
        self.color_plaseholder: Texture = g.fm.get_texture("color_palette_chooser_button_color_plaseholder.png")
        self.random_state_texture: Texture = g.fm.get_texture("color_palette_chooser_button_random.png")

        self.style = g.STYLE_DEFAULT_BUTTON

        super().__init__(
            texture=self._create_texture(self.frame_texture),
            texture_hovered=self._create_texture(self.frame_texture_hovered),
            texture_pressed=self._create_texture(self.frame_texture_pressed),
            **kwargs
        )

    def _get_color(self):
        new_color = random.choice(list(g.SAVES_COLOR_PALLETE))
        while new_color == self.now_color:
            new_color = random.choice(list(g.SAVES_COLOR_PALLETE))
        return new_color

    def _get_plaseholder_in_color(self, color_to: tuple[int, int, int], color_from=(255, 0, 255)):
        if not color_to:
            return Image.new('RGBA', self.color_plaseholder.size)

        image = self.color_plaseholder.image.copy()

        table = list(range(256)) * 4

        for channel in range(3):
            offset = channel * 256
            table[offset + color_from[channel]] = color_to[channel]

        return image.point(table)

    def _create_texture(self, frame_texture: Texture):
        placeholder_colored = self._get_plaseholder_in_color(self.now_color)
        frame_image = frame_texture.image.copy()

        result = Image.new('RGBA', frame_image.size, (0, 0, 0, 0))
        result.paste(placeholder_colored, (0, 0), placeholder_colored)
        result.paste(frame_image, (0, 0), frame_image)

        texture = Texture(result)

        return texture

    def update(self):
        self.texture, self.texture_hovered, self.texture_pressed = tuple(self._create_texture(i) for i in (self.frame_texture, self.frame_texture_hovered, self.frame_texture_pressed))

    def set_color(self, color: tuple[int, int, int]):
        self.now_color = color
        self.update()

    def on_click(self, event: agui.UIOnClickEvent):
        self.now_color = self._get_color()
        self.update()