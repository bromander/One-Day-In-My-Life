import arcade.gui as agui
from arcade.gui import Surface
from arcade import draw_line
import re


from ..globals import g

class FashionUiLabel(agui.UILabel):
    def __init__(self, *args, underline: bool = False, stroke: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.underline = underline
        self.stroke = stroke

        self.pattern = re.compile(rf" *{re.escape(g.UNSEEN_TEXT_PLACEHOLDER)} *")

    def _clean_text_width(self, clean_text):
        old = self._label.text
        self._label.text = clean_text
        width = self._label.content_width
        self._label.text = old
        return width

    def _get_real_width(self):

        if g.UNSEEN_TEXT_PLACEHOLDER in self.text:

            clean_text = self.pattern.sub("", self.text)
            real_width = self._clean_text_width(clean_text)

            return real_width
        else:
            return self._label.content_width

    def do_render(self, surface: Surface):
        self.prepare_render(surface)

        self._label.draw()
        #self._label.draw_debug()

        if self.text.replace(g.UNSEEN_TEXT_PLACEHOLDER, "").strip():
            if self.underline or self.stroke:
                real_width = self._get_real_width()

            if self.underline:
                line_y = 10
                draw_line(
                    0, line_y,
                    real_width, line_y,
                    self.font_color,
                    2
                )
            if self.stroke:
                line_y = self.height/2
                draw_line(
                    0, line_y,
                    real_width, line_y,
                    self.font_color,
                    2
                )