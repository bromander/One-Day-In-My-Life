import arcade
from typing import Optional, List, Tuple

class Scene:
    def  __init__(self):
        self.data: dict[str: Tuple[dict[str: arcade.Sprite], str: arcade.Sprite]] = {
            "bg": {},
            "characters": {},
            "gui": {},
            "fade": arcade.Sprite()
        }

    def __getitem__(self, item):
        return self.data[item]

    def add_sprite(self, layer: str, name: str, sprite: arcade.Sprite):
        if layer != "fade":
            self.data[layer][name] = sprite
        else:
            self.data[layer] = sprite

    def delete_sprite(self, layer: str, name: str):
        if layer != "fade":
            del self.data[layer][name]
        else:
            self.data[layer].clear()

    def clear_layer(self, layer):
        self.data[layer].clear()

    def update(self):

        for i in self.data.values():
            if type(i) is arcade.Sprite:
                i.update()
            elif type(i) is dict:
                for o in i.values():
                    i.update()

    def draw(self):

        for i in self.data.values():
            if type(i) is arcade.Sprite:
                arcade.draw_sprite(i)
            elif type(i) is dict:
                for o in i.values():
                    arcade.draw_sprite(o)
