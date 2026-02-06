import arcade
import arcade.gui

class SpriteButton(arcade.gui.UIWidget):

    def __init__(self, x=0, y=0, width=100, height=100,
                 normal_texture=None,
                 hover_texture=None,
                 press_texture=None,
                 disabled_texture=None,
                 action=None,
                 pixelated=False):
        super().__init__(x, y, width, height)

        self.textures = {
            "normal": normal_texture,
            "hover": hover_texture,
            "press": press_texture,
            "disabled": disabled_texture
        }
        self.current_state = "normal"
        self.action = action
        self.pixelated = pixelated

        if isinstance(normal_texture, str):
            self.textures["normal"] = arcade.load_texture(normal_texture)

    def on_update(self, dt):
        if self.disabled:
            self.current_state = "disabled"
        elif self.pressed:
            self.current_state = "press"
        elif self.hovered:
            self.current_state = "hover"
        else:
            self.current_state = "normal"

    def on_draw(self):
        texture = self.textures.get(self.current_state) or self.textures["normal"]

        if texture:
            button_rect = arcade.Rect(self.x, self.y, self.width, self.height)

            arcade.draw_texture_rect(
                texture=texture,
                rect=button_rect,
                color=arcade.color.WHITE,
                angle=0.0,
                blend=True,
                alpha=self._alpha if hasattr(self, '_alpha') else 255,
                pixelated=self.pixelated
            )

    def on_click(self):
        if self.action:
            self.action()