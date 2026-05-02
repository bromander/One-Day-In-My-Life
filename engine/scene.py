import time
from arcade import Sprite, draw_sprite, Texture, load_texture, get_window, TextureAnimationSprite
import os
from pathlib import Path
import threading
from typing import Optional, List, Union, Literal
from .Exceptions import LayerDoesNotExistError, SpriteDoesNotExistError
from .files_manager import FilesManager

from .globals import globals as g

class Scene:
    def  __init__(self) -> None:
        """
        Отвечает за работу со спрайтами со всей сцены
        """
        self.data: dict[str : dict[Union[dict[str : Sprite], str : Sprite]]] = {
            "bg": {},
            "bg_parallax": [],
            "animated_sprites": {},
            "sprites": {},
            "gui": {},
            "fade": {"fade" : Sprite(), "splash": Sprite()}
        }

        self.save_points = []

        self.characters_slice = -1

        self.fm: FilesManager = g.fm

        self.len_loaded_textures = 0

        self.textures = {}

    def set_characters_slice(self, value):
        self.characters_slice = value

    def get_texture(self, filename: str) -> Optional[Union[Texture, TextureAnimationSprite]]:
        return self.fm.get_texture(filename)

    def has_texture(self, filename: str) -> bool:
        if self.get_texture(filename) is None:
            return False
        return True

    def get_sprite(self, filename: str) -> Optional[Sprite]:
        texture = self.get_texture(filename)
        if isinstance(texture, TextureAnimationSprite):
            return texture
        if texture:
            sprite = Sprite(texture)
            return sprite
        return None

    def __getitem__(self, item):
        return self.data[item]

    def clear_scene(self):
        for name, dat in self.data.items():
            if name == "fade" or "gui":
                continue
            if isinstance(dat, dict):
                for i in dat.values():
                    i: Sprite = i
                    i.kill()
                    del i
            elif isinstance(dat, list):
                for i in dat:
                    i["sprite"].kill()
                    del i["sprite"]

        self.data = {
            "bg": {},
            "bg_parallax": [],
            "animated_sprites": {},
            "sprites": {},
            "gui": {},
            "fade": {"fade" : Sprite(), "splash": Sprite()}
        }

    def add_sprite(self, layer: Literal["bg", "sprites", "gui", "fade"],
                   name: str,
                   sprite: Union[Sprite, Texture, str]) -> None:
        """
        Добавляет спрайт на сцену
        :param layer: Слой
        :param name: Название спрайта
        :param sprite: Спрайт, путь или уже готовая текстура
        """
        if name in self.data[layer]:
            del self.data[layer][name]

        if isinstance(sprite, str):
            sprite_new = self.get_sprite(sprite)
            if sprite_new is None:
                raise FileNotFoundError(f"File {sprite} not found!")
            self.data[layer][name] = sprite_new

        elif isinstance(sprite, Sprite):
            self.data[layer][name] = sprite

        elif isinstance(sprite, Texture):
            self.data[layer][name] = Sprite(sprite)


    def delete_sprite(self, layer: Union[Literal["bg", "sprites", "gui", "fade"], str],
                      name: str) -> None:
        print("inside", id(self.data), self.data)
        """
        Удаляет спрайт со сцены
        :param layer: Слой
        :param name: Название спрайта
        :raises LayerDoesNotExistError: Если слой не существует
        """
        if layer not in self.data:
            raise LayerDoesNotExistError(f"Layer {layer} does not exist!")

        if name in self.data[layer]:
            del self.data[layer][name]
        else:
            raise SpriteDoesNotExistError(f"Sprite {name} does not exist in layer {layer}!")

    def clear_layer(self, layer: Union[Literal["bg", "sprites", "gui", "fade"], str]) -> None:
        """
        Очищает слой

        :var layer Слой
        :raises LayerDoesNotExistError
        """
        if layer not in self.data:
            raise LayerDoesNotExistError(f"Layer {layer} does not exist!")

        self.data[layer].clear()

    def update(self, delta_time = 1/60) -> None:
        """Обновляет все спрайты"""

        len_sprites = 0


        for layer, layer_content in self.data.items():
            if layer == "animated_sprites":
                for id, sprite in layer_content.items():
                    sprite : TextureAnimationSprite = sprite
                    if sprite._current_keyframe_index == 100:
                        del self.data[layer][id]
                        break
                    sprite.update_animation(delta_time)
                    continue

            if isinstance(layer_content, Sprite):
                layer_content.update()
            elif isinstance(layer_content, dict):
                for sprite in layer_content.values():
                    if isinstance(sprite, Sprite):
                        sprite.update()

        for i, v in self.data.items():
            if isinstance(v, dict):
                len_sprites += len(v.values())
            else:
                len_sprites += 1

        self.len_loaded_textures  = len_sprites

    def add_parallax_bg(self, filename, speed, center_x, center_y):
        sprite = self.get_sprite(filename)
        sprite.scale_x = float(sprite.scale_x + 0.1 * speed)
        sprite.scale_y = float(sprite.scale_y + 0.1 * speed)

        layer = {
                'sprite' : sprite,
                'speed': speed,
                'original_x': center_x,
                'original_y': center_y,
                "scale" : sprite.scale
        }
        self.data["bg_parallax"].append(layer)

        window = get_window()
        x, y = window.center_x, window.center_y

        self._move_parallax(self.data["bg_parallax"][-1], x, y)

    def _move_parallax(self, layer, x, y):
        window = get_window()
        normalized_x = (x - window.width // 2) / (window.width // 2)
        normalized_y = (y - window.height // 2) / (window.height // 2)

        max_offset_x = 100 * layer['speed']
        max_offset_y = 60 * layer['speed']

        layer['sprite'].center_x = layer['original_x'] + normalized_x * max_offset_x
        layer['sprite'].center_y = layer['original_y'] + normalized_y * max_offset_y

    def on_mouse_motion(self, x, y):

        for e, layer in enumerate(self.data["bg_parallax"]):
            if hasattr(layer['sprite'], "clicked"):
                if not layer['sprite'].clicked:
                    if hasattr(layer['sprite'], "freezed"):
                        if not layer['sprite'].freezed:
                            self._move_parallax(layer, x, y)
                    else:
                        self._move_parallax(layer, x, y)
                else:
                    self.data["bg_parallax"][e]['original_x'] = layer['sprite'].center_x
                    self.data["bg_parallax"][e]['original_y'] = layer['sprite'].center_y
                    self.data["bg_parallax"].append(self.data["bg_parallax"].pop(e))

            else:
                self._move_parallax(layer, x, y)

    def draw(self) -> None:
        """Рисует спрайты со всей сцены"""
        data = self.data

        # Фон
        if bg_items := data.get('bg'):
            for layer in sorted(bg_items, reverse=True):
                draw_sprite(bg_items[layer])

        # Параллакс
        bg_parallax = data.get('bg_parallax', [])
        slice_idx = self.characters_slice

        # Функция для слоя (избегаем дублирования кода)
        def draw_layer(layer):
            sprite = layer["sprite"]
            if "scale" in layer:
                sprite.scale = layer["scale"]
            draw_sprite(sprite)

        # Задние слои
        for layer in bg_parallax[:slice_idx]:
            draw_layer(layer)

        # Спрайты
        for sprite in data.get("sprites", {}).values():
            draw_sprite(sprite)

        # Передние слои
        for layer in bg_parallax[slice_idx - 1:]:
            draw_layer(layer)

        # Остальное
        skip_keys = {'bg', 'bg_parallax', 'sprites'}
        for key, value in data.items():
            if key in skip_keys:
                continue
            if isinstance(value, Sprite):
                draw_sprite(value)
            elif isinstance(value, dict):
                for sprite in value.values():
                    draw_sprite(sprite)

    def create_savepoint(self) -> None:
        """
        Созадёт копию сцены
        """
        self.save_points.append(self.data)

    def load_savepoint(self, sp_id: int = 0) -> None:
        """
        Загружает копию сцены
        :param sp_id: Индекс сцены:
        :raises IndexError: если нет сохранений
        """
        if len(self.save_points) < 0:
            raise IndexError("There is no save points!")

        self.data = self.save_points[sp_id]