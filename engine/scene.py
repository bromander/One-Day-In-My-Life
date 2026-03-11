from arcade import Sprite, draw_sprite, Texture, load_texture
import os
from pathlib import Path
from typing import Optional, List, Tuple, Literal
from .Exceptions import LayerDoesNotExistError, SpriteDoesNotExistError

class Scene:
    def  __init__(self) -> None:
        """
        Отвечает за работу со спрайтами со всей сцены
        """
        self.data: dict[str: Tuple[dict[str: Sprite], Sprite]] = {
            "bg": {},
            "sprites": {},
            "gui": {},
            "fade": {"fade" : Sprite(), "splash": Sprite()}
        }
        self.save_points = []

        def find_files(extension: list):
            results = {}
            start_path = f".\\game\\images\\"

            for i in extension:
                for root, dirs, files in os.walk(start_path):
                    if 'characters' in root.split(os.sep): # Пропускаем директорию со спрайтами персонажей т.к. за их спрайты отвечает уже сам объект Character
                        continue
                    for file in files:
                        if file.lower().endswith(i.lower()):
                            texture = load_texture(os.path.join(root, file))
                            results[file] = texture

            return results

        self.textures = find_files([".png", ".jpg", ".jpeg", ".PNG", ".JPG"])
        self.hashed_sprites = {}


    def get_texture(self, filename):
        return self.textures.get(filename, None)

    def has_texture(self, filename):
        if self.get_texture(filename) is None:
            return False
        return True

    def get_sprite(self, filename):
        if filename in self.hashed_sprites:
            print("already_have!")
            original = self.hashed_sprites[filename]
            return Sprite(original.texture)

        texture = self.textures.get(filename, None)
        if texture:
            sprite = Sprite(texture)
            self.hashed_sprites[filename] = sprite
            return sprite
        return None


    def __getitem__(self, item):
        return self.data[item]

    def add_sprite(self, layer: Literal["bg", "sprites", "gui", "fade"],
                   name: str,
                   sprite: Tuple[Sprite, Texture, str]) -> None:
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


    def delete_sprite(self, layer: Tuple[Literal["bg", "sprites", "gui", "fade"], str],
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

    def clear_layer(self, layer: Tuple[Literal["bg", "sprites", "gui", "fade"], str]) -> None:
        """
        Очищает слой

        :var layer Слой
        :raises LayerDoesNotExistError
        """
        if layer not in self.data:
            raise LayerDoesNotExistError(f"Layer {layer} does not exist!")

        self.data[layer].clear()

    def update(self) -> None:
        """
        Обновляет спрайты всей сцены
        """
        for i in self.data.values():
            if type(i) is Sprite:
                i.update()
            elif type(i) is dict:
                for o in i.values():
                    i.update()

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