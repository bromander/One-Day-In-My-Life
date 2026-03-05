import arcade
import os
from typing import Optional, List, Tuple, Literal

class Scene:
    def  __init__(self) -> None:
        """
        Отвечает за работу со спрайтами со всей сцены
        """
        self.data: dict[str: Tuple[dict[str: arcade.Sprite], arcade.Sprite]] = {
            "bg": {},
            "characters": {},
            "gui": {},
            "fade": arcade.Sprite()
        }
        self.save_points = []

        def find_files(extension: list):
            results = {}
            start_path = f"./game/images/scenes/"

            for i in extension:
                for root, dirs, files in os.walk(start_path):
                    for file in files:
                        if file.lower().endswith(i.lower()):
                            full_path = os.path.join(root, file)
                            results[file] = arcade.Sprite(full_path.replace("\\", "/"))

            return results

        self.backgrounds = find_files([".png", ".jpg", ".jpeg", ".PNG", ".JPG"])


    def __getitem__(self, item):
        return self.data[item]

    def add_sprite(self, layer: Tuple[Literal["bg", "characters", "gui", "fade"], str],
                   name: Tuple[str, int],
                   sprite: arcade.Sprite) -> None:
        """
        Добавляет спрайт на сцену
        :param layer: Слой
        :param name: Название спрайта
        :param sprite: Сам спрайт
        """
        if layer == "fade":
            self.data["fade"] = sprite
        else:
            self.data[layer][name] = sprite

    def delete_sprite(self, layer: Tuple[Literal["bg", "characters", "gui", "fade"], str],
                      name: str) -> None:
        """
        Удаляет спрайт со сцены
        :param layer: Слой
        :param name: Название спрайта
        """
        if layer != "fade":
            if name in self.data[layer]:
                del self.data[layer][name]
        else:
            self.data[layer].clear()

    def clear_layer(self, layer: Tuple[Literal["bg", "characters", "gui", "fade"], str]) -> None:
        """
        Очищает слой
        """
        self.data[layer].clear()

    def update(self) -> None:
        """
        Обновляет спрайты всей сцены
        """
        for i in self.data.values():
            if type(i) is arcade.Sprite:
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
                        arcade.draw_sprite(bg_items[layer])

        for o, i in self.data.items():
            if o == 'bg':
                continue
            elif isinstance(i, arcade.Sprite):
                arcade.draw_sprite(i)
            elif isinstance(i, dict):
                for o in i.values():
                    arcade.draw_sprite(o)

    def create_savepoint(self) -> None:
        """
        Созадёт копию сцены на данный момент
        Максимальное кол-во записываемых сцен - 5. Если становится больше, старые сохранения начинают удалятся
        :return:
        """
        self.save_points.append(self.data)
        if len(self.save_points) >= 5:
            self.save_points.pop(-1)

    def load_savepoint(self, sp_id: int = 0) -> None:
        """
        Загружает копию сцены
        :param sp_id: Индекс сцены
        """
        self.data = self.save_points[sp_id]