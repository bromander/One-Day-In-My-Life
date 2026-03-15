import time
from arcade import Sprite, draw_sprite, Texture, load_texture
import os
from pathlib import Path
import threading
from typing import Optional, List, Union, Literal
from .Exceptions import LayerDoesNotExistError, SpriteDoesNotExistError
from .files_manager import FilesManager

class Scene:
    def  __init__(self, fm: FilesManager) -> None:
        """
        Отвечает за работу со спрайтами со всей сцены
        """
        self.data: dict[str, Union[dict[str, Sprite], Sprite]] = {
            "bg": {},
            "sprites": {},
            "gui": {},
            "fade": {"fade" : Sprite(), "splash": Sprite()}
        }
        self.save_points = []

        self.fm: FilesManager = fm

        self.textures = {}


    def get_texture(self, filename: str) -> Optional[Texture]:
        return self.fm.textures.get(filename, None)

    def has_texture(self, filename: str) -> bool:
        if self.get_texture(filename) is None:
            return False
        return True

    def get_sprite(self, filename: str) -> Optional[Sprite]:
        texture = self.fm.textures.get(filename, None)
        if texture:
            sprite = Sprite(texture)
            return sprite
        return None

    def __getitem__(self, item):
        return self.data[item]

    def add_sprite(self, layer: Literal["bg", "sprites", "gui", "fade"],
                   name: str,
                   sprite: Union[Sprite, Texture, str]) -> None:
        """
        Добавляет спрайт на сцену
        :param layer: Слой
        :param name: Название спрайта
        :param sprite: Спрайт, путь или уже готовая текстура
        """
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

    def update(self) -> None:
        """Обновляет все спрайты"""
        for layer_content in self.data.values():
            if isinstance(layer_content, Sprite):
                layer_content.update()
            elif isinstance(layer_content, dict):
                for sprite in layer_content.values():
                    if isinstance(sprite, Sprite):
                        sprite.update()

    def draw(self) -> None:
        """
        Рисует спрайты со всей сцены
        """
        bg_items = self.data.get('bg', {})
        if bg_items:
            layers = [int(k) for k in bg_items.keys()]
            if layers:
                min_layer = min(layers)
                max_layer = max(layers)

                for layer in range(max_layer, min_layer - 1, -1):
                    if layer in bg_items:
                        draw_sprite(bg_items[layer])

        for o, i in self.data.items():
            if o == 'bg':
                continue
            elif isinstance(i, Sprite):
                draw_sprite(i)
            elif isinstance(i, dict):
                for o in i.values():
                    draw_sprite(o)

    def create_savepoint(self) -> None:
        """
        Созадёт копию сцены на данный момент
        Максимальное кол-во записываемых сцен - 5. Если становится больше, старые сохранения начинают удалятся
        """
        self.save_points.append(self.data)
        if len(self.save_points) >= 5:
            self.save_points.pop(-1)

    def load_savepoint(self, sp_id: int = 0) -> None:
        """
        Загружает копию сцены
        :param sp_id: Индекс сцены:
        :raises IndexError: если нет сохранений
        """
        if len(self.save_points) < 0:
            raise IndexError("There is no save points!")

        self.data = self.save_points[sp_id]