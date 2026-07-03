import time
from typing import Optional
import arcade
from arcade import gui as agui
from pyglet.gl import GLException
import random

from .globals import g
from .logger import get_logger
from .gui import SettingsManager, CharactersTextManager
from .gui import MovableBlockFalling, MovableBlock, ItemsNotifText, ClickableSprite
from .character import Attributes

logger = get_logger(__name__)

get_real_filename = g.fm.get_original_filename

class GameViews:

    class GameViewTemplate(arcade.View):
        def __init__(self, using_sprites: Optional[list] = None) -> None:
            """
            Является "Шаблоном".
            Создаёт счётчик ФПС и отвечает за курсор
            """
            super().__init__()

            if using_sprites is not None:
                self._load_using_sprites(using_sprites)

            self.window.set_mouse_visible(False)

            self.scale = arcade.get_screens()[0].get_scale()

            self.cursor_texture = arcade.Sprite(g.fm.get_texture("cursor.png"), 0.2)
            self.window.background_color = arcade.color.WHITE
            self.background_color = arcade.color.WHITE
            self.fps = {
                "window": [],
                "window_size": 100,
                "last_print_time": time.time(),
                "avg_fps": 0.0,
                "min_fps": 0.0,
                "max_fps": 0.0,
                "label": arcade.Text(
                    f"FPS: Avg=0, Min=0, Max=0, Window size: 0. Vsync: {self.window.vsync}",
                    x=10,
                    y=self.window.height - 10,
                    color=arcade.color.ARCADE_GREEN,
                    font_size=14,
                    anchor_x="left",
                    anchor_y="top",
                ),
            }

        def _load_using_sprites(self, sprite_name_list: list):
            g.fm.load_assets(sprite_name_list)

        def cleanup_ui(self):
            if hasattr(self, "manager"):
                self.manager.clear()
                self.manager.disable()

            if hasattr(self, "menu_manager"):
                self.menu_manager.clear()
                self.menu_manager.disable()

            if hasattr(self, "settings_manager"):
                if hasattr(self.settings_manager, "clear"):
                    self.settings_manager.clear()

            if hasattr(self, "splash_manager"):
                self.splash_manager.clear()
                self.splash_manager.disable()

            if hasattr(self, "in_game_manager"):
                if hasattr(self.in_game_manager, "clear"):
                    self.in_game_manager.clear()

        def _get_amend_color(self, border_thickness=20, min_border=2):
            sprite = None
            bg_values = list(g.scene["bg"].values())
            if bg_values:
                sprite = bg_values[-1]
            elif g.scene["bg_parallax"]:
                sprite = g.scene["bg_parallax"][0]["sprite"]
            if not sprite or not hasattr(sprite, "texture") or sprite.texture is None:
                return None

            img = sprite.texture.image.copy()
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img.thumbnail((img.width // 2, img.height // 2))
            width, height = img.size

            border = min(border_thickness, width // 2, height // 2)
            pixels = img.load()

            visible_pixels = []

            while border >= min_border:
                for x in range(width):
                    for y in range(border):
                        if pixels[x, y][3] > 0:
                            visible_pixels.append(pixels[x, y])
                    for y in range(height - border, height):
                        if pixels[x, y][3] > 0:
                            visible_pixels.append(pixels[x, y])
                for y in range(border, height - border):
                    for x in range(border):
                        if pixels[x, y][3] > 0:
                            visible_pixels.append(pixels[x, y])
                    for x in range(width - border, width):
                        if pixels[x, y][3] > 0:
                            visible_pixels.append(pixels[x, y])

                if visible_pixels:
                    break
                border //= 2

            if not visible_pixels:
                cx0, cy0 = width // 4, height // 4
                cx1, cy1 = width * 3 // 4, height * 3 // 4
                for x in range(cx0, cx1):
                    for y in range(cy0, cy1):
                        if pixels[x, y][3] > 0:
                            visible_pixels.append(pixels[x, y])
                if not visible_pixels:
                    return None

            count = len(visible_pixels)
            red = sum(p[0] for p in visible_pixels) // count
            green = sum(p[1] for p in visible_pixels) // count
            blue = sum(p[2] for p in visible_pixels) // count

            return (red, green, blue)

        def set_bg_by_scene_bg(self):
            color = self._get_amend_color()
            if color:
                self.background_color = color
                logger.debug(f"Бекгрунд установлен на {color}")
            else:
                logger.warning(
                    "При попытке вызова GameViewTemplate._get_amend_color, возвращено None. Бекграунд не установлен"
                )

        def on_update(self, delta_time: float) -> None:
            if "x" in self.window.mouse.data and "y" in self.window.mouse.data:
                mouse_x, mouse_y = (
                    self.window.mouse.data["x"],
                    self.window.mouse.data["y"],
                )
                self.cursor_texture.position = (mouse_x, mouse_y)

            if not g.sm:
                return None

            if g.sm.Volume.show_fps:
                current_fps = 1.0 / delta_time if delta_time > 0 else 0

                self.fps["window"].append(current_fps)
                if len(self.fps["window"]) > self.fps["window_size"]:
                    self.fps["window"].pop(0)

                if time.time() - self.fps["last_print_time"] >= 1.0:
                    self.fps["avg_fps"] = sum(self.fps["window"]) / len(
                        self.fps["window"]
                    )
                    self.fps["min_fps"] = min(self.fps["window"])
                    self.fps["max_fps"] = max(self.fps["window"])

                    self.fps["label"].text = (
                        f"FPS: Avg={int(self.fps['avg_fps'])}, Min={int(self.fps['min_fps'])}, Max={int(self.fps['max_fps'])}, "
                        f"Window size: {self.fps['window_size']}. "
                        f"Vsync: {self.window.vsync}"
                    )

                    self.fps["last_print_time"] = time.time()

        def on_mouse_leave(self, x: int, y: int) -> bool | None:
            self.cursor_texture.alpha = 0

        def on_mouse_enter(self, x: int, y: int) -> bool | None:
            self.cursor_texture.alpha = 255

        def on_draw(self) -> None:

            arcade.draw_sprite(self.cursor_texture)

            if not g.sm:
                return None

            if g.sm.Volume.show_fps:
                arcade.draw_lrbt_rectangle_filled(
                    left=5,
                    right=8 * len(self.fps["label"].text),
                    bottom=self.window.height - 35,
                    top=self.window.height - 10,
                    color=(0, 0, 0, 200),
                )
                self.fps["label"].x = 10
                self.fps["label"].y = self.window.height - 10
                self.fps["label"].draw()


    class MenuView(GameViewTemplate):
        def __init__(self):
            super().__init__(
                using_sprites=[
                    "dialog_window.png",

                ]
            )

            texture = g.fm.get_texture("dialog_window.png")

            self.dialog_window = arcade.Sprite(
                texture,
                scale=6 * min(self.width / 1920, self.height / 1080),
                center_x=self.width * 0.5,
                center_y=self.height * 0.13,
            )

            g.actions = g.actions
            self.NAMESPACE = g.main.NAMESPACE
            self.fm = g.fm

            self.window.background_color = (198, 166, 128)
            self.background_color = (198, 166, 128)

            self.menu_v_box = agui.UIBoxLayout(space_between=20)

            # self.window.set_vsync(True)
            self.menu_manager = agui.UIManager()
            self.lore = self._lore()

            self.settings_manager = SettingsManager()
            self.settings_manager.enable()

            self.attributes = Attributes()
            self.attributes.character_text_colour = arcade.color.WHITE
            self.attributes.text_anchor = "center"

            self.characters_texts_manager = CharactersTextManager()
            self.characters_texts_manager.enable()

            self.correct_ans = 0
            self.NAMESPACE["Define"].correct_ans = 0
            next(self.lore)

        def plus(self, do: bool):
            if do:
                self.correct_ans += 1
            try:
                next(self.lore)
            except StopIteration:
                pass

        def show_menu(self, data) -> None:
            self.menu_manager.clear()
            self.menu_manager.enable()
            self.menu_v_box = agui.UIBoxLayout(space_between=20)

            for k, v in data.items():
                button = agui.UIFlatButton(
                    text=k,
                    width=250,
                    height=100,
                    font_name=g.FONT_NAME,
                    style=g.STYLE_DEFAULT_BUTTON,
                )
                button.on_click = lambda event, do=v: self.plus(do)
                self.menu_v_box.add(button)

            ui_anchor_layout = agui.UIAnchorLayout()
            ui_anchor_layout.add(
                child=self.menu_v_box, anchor_x="center_x", anchor_y="center_y"
            )

            self.menu_manager.add(ui_anchor_layout)

        def on_update(self, delta_time: float) -> None:
            super().on_update(delta_time)
            g.scene.update(delta_time)
            self.characters_texts_manager.update(delta_time)
            self.settings_manager.on_update(delta_time)
            self.menu_manager.on_update(delta_time)

            g.actions.update(delta_time)

        def on_draw(self) -> None:
            self.clear()
            g.scene.draw()
            arcade.draw_sprite(self.dialog_window)
            self.characters_texts_manager.draw()
            self.menu_manager.draw()
            self.settings_manager.draw()
            super().on_draw()

        def _lore(self):
            self.attributes.character_text = ["Какое из слов является местоимением?"]
            self.show_menu(
                {
                    "'Другой'": True,
                    "'Первый'": False,
                    "'Отдельный'": False,
                    "'Вчерашний'": False,
                }
            )
            yield
            self.attributes.character_text = [
                "Что вы скажете об очень эффективном человеке?"
            ]
            self.show_menu(
                {
                    "Супер эфективный": False,
                    "Суперэффективный": True,
                    "Супер эффективный": False,
                    "Супер-эффективный": False,
                }
            )
            yield
            self.attributes.character_text = ["Как правильно?"]
            self.show_menu({"ТвОрог": True, "ТворОг": True})
            yield
            self.NAMESPACE["Define"].correct_ans = self.correct_ans
            self.window.show_view(self.window.GameView)

        def on_key_press(self, key: int, modifiers: int) -> bool | None:
            if key == arcade.key.S or key == arcade.key.ESCAPE:
                self.settings_manager.turn_visibl()

    class MenuViewFood(GameViewTemplate):
        def __init__(self):
            super().__init__(
                using_sprites=[
                    "dialog_window.png",
                    "home_kitchen.jpg"
                ]
            )

            texture = g.scene.get_texture("dialog_window.png")

            self.dialog_window = arcade.Sprite(
                texture,
                scale=6 * min(self.width / 1920, self.height / 1080),
                center_x=self.width * 0.5,
                center_y=self.height * 0.13,
            )
            self.NAMESPACE = g.main.NAMESPACE
            self.fm = g.fm

            self.menu_v_box = agui.UIBoxLayout(space_between=20)

            # self.window.set_vsync(True)
            self.menu_manager = agui.UIManager()
            self.lore = self._lore()

            self.settings_manager = SettingsManager()
            self.settings_manager.enable()

            self.attributes = Attributes()
            self.attributes.character_text_colour = arcade.color.WHITE
            self.attributes.text_anchor = "center"

            self.characters_texts_manager = CharactersTextManager()
            self.characters_texts_manager.enable()

            if not hasattr(self.NAMESPACE["Persistent"], "collected_foods"):
                self.NAMESPACE["Persistent"].collected_foods = []

            if self.NAMESPACE["Persistent"].collected_foods is None:
                self.NAMESPACE["Persistent"].collected_foods = []

            self.available_food = self.NAMESPACE["Data"].get_food_root()
            self.menu = {i[0]: i[1] for i in self.available_food}

            self.food = {}
            for i in self.NAMESPACE["Data"].mix:
                if i not in self.available_food:
                    self.food[i] = False
                else:
                    self.food[i] = True

            if (
                "cooking_omlet" in self.NAMESPACE["Persistent"].collected_foods
                and "cooking_bliny" in self.NAMESPACE["Persistent"].collected_foods
                and "cooking_salad" in self.NAMESPACE["Persistent"].collected_foods
            ):
                self.menu["???"] = "MGRoL"
                self.food["???"] = "MGRoL"

            next(self.lore)

        def set_choice(self, label):
            self.NAMESPACE["Define"].cooking_label = label
            self.NAMESPACE["Persistent"].collected_foods = self.NAMESPACE[
                "Persistent"
            ].collected_foods + [label]

            try:
                next(self.lore)
            except StopIteration:
                pass

        def show_menu(self, data) -> None:
            self.menu_manager.clear()
            self.menu_manager.enable()
            self.menu_v_box = agui.UIBoxLayout(space_between=20)

            for name, state in self.food.items():
                _text = name
                if name in data:
                    _label = data[name]
                    state = True
                else:
                    _label = "bad_ending_golubi"  # просто заглушка
                    state = False

                button = agui.UIFlatButton(
                    text=_text,
                    width=250,
                    height=100,
                    font_name=g.FONT_NAME,
                    style=g.STYLE_DEFAULT_BUTTON,
                )
                button.on_click = lambda event, label=_label: self.set_choice(label)
                if not state:
                    button.disabled = True
                self.menu_v_box.add(button)

            ui_anchor_layout = agui.UIAnchorLayout()
            ui_anchor_layout.add(
                child=self.menu_v_box, anchor_x="center_x", anchor_y="center_y"
            )

            self.menu_manager.add(ui_anchor_layout)

        def on_update(self, delta_time: float) -> None:
            super().on_update(delta_time)
            g.scene.update(delta_time)
            self.characters_texts_manager.update(delta_time)
            self.settings_manager.on_update(delta_time)
            self.menu_manager.on_update(delta_time)

            g.actions.update(delta_time)

        def on_draw(self) -> None:
            self.clear()
            g.scene.draw()
            arcade.draw_sprite(self.dialog_window)
            self.characters_texts_manager.draw()
            self.menu_manager.draw()
            self.settings_manager.draw()
            super().on_draw()

        def _lore(self):
            self.attributes.character_text = ["Что готовить будем?"]
            self.show_menu(
                self.menu,
            )
            yield
            self.window.show_view(self.window.GameView)

        def on_key_press(self, key: int, modifiers: int) -> bool | None:
            if key == arcade.key.S or key == arcade.key.ESCAPE:
                self.settings_manager.turn_visibl()

    class ShopCollecting(GameViewTemplate):
        def __init__(self):
            super().__init__(
                using_sprites=[
                    "shop_shelf_bg_1.png",
                    "shop_shelf_bg_2.png",
                    "puki.png",
                    "eggs.png",
                    "teramisu.png",
                    "pineapple.png",
                    "tomatoes.png",
                    "cheese.png",
                    "cheremsha.png",
                    "meat.png",
                    "milk.png",
                    "penis.png",
                    "penis_bread.png",

                ]
            )

            def return_back(event=None):
                if len(g.main.NAMESPACE["Define"].collected_items) > 0:
                    self.window.show_view(self.window.GameView)

            g.main.NAMESPACE["Define"].collected_items = {}

            # self.window.set_vsync(True)
            self.NAMESPACE = g.main.NAMESPACE
            self.fm = g.fm

            self.layers = []
            self.layers_sprite_list = arcade.SpriteList()
            self.layers.append(
                {
                    "sprite": g.scene.get_sprite("shop_shelf_bg_1.png"),
                    "speed": 0.0,
                    "original_x": self.width // 2,
                    "original_y": self.height // 2,
                }
            )
            self.layers.append(
                {
                    "sprite": g.scene.get_sprite("shop_shelf_bg_1.png"),
                    "speed": 0.15,
                    "original_x": self.width // 2,
                    "original_y": self.height // 2,
                }
            )
            self.layers.append(
                {
                    "sprite": g.scene.get_sprite("shop_shelf_bg_2.png"),
                    "speed": 0.3,
                    "original_x": self.width // 2,
                    "original_y": self.height // 2,
                }
            )

            self.settings_manager = SettingsManager()
            self.settings_manager.enable()

            width = self.width
            height = self.height
            scene = g.scene
            items = [
                MovableBlockFalling(
                    scene.get_texture("puki.png"), width * 0.1, height * 0.33
                ),
                MovableBlockFalling(
                    scene.get_texture("puki.png"), width * 0.12, height * 0.33
                ),
                MovableBlockFalling(
                    scene.get_texture("puki.png"), width * 0.14, height * 0.33
                ),
                MovableBlockFalling(
                    scene.get_texture("eggs.png"), width * 0.3, height * 0.28
                ),
                MovableBlockFalling(
                    scene.get_texture("eggs.png"), width * 0.32, height * 0.28
                ),
                MovableBlockFalling(
                    scene.get_texture("teramisu.png"), width * 0.48, height * 0.33, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("teramisu.png"), width * 0.5, height * 0.33, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("teramisu.png"), width * 0.52, height * 0.33, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("pineapple.png"), width * 0.73, height * 0.30
                ),
                MovableBlockFalling(
                    scene.get_texture("tomatoes.png"), width * 0.1, height * 0.84, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("tomatoes.png"), width * 0.15, height * 0.84, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("tomatoes.png"), width * 0.2, height * 0.84, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("tomatoes.png"), width * 0.25, height * 0.84, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheese.png"), width * 0.4, height * 0.79, 0.8
                ),
                MovableBlockFalling(
                    scene.get_texture("cheremsha.png"), width * 0.55, height * 0.79
                ),
                MovableBlockFalling(
                    scene.get_texture("cheremsha.png"), width * 0.55, height * 0.79
                ),
                MovableBlockFalling(
                    scene.get_texture("cheremsha.png"), width * 0.55, height * 0.79
                ),
                MovableBlockFalling(
                    scene.get_texture("meat.png"), width * 0.7, height * 0.79
                ),
                MovableBlockFalling(
                    scene.get_texture("meat.png"), width * 0.7, height * 0.79
                ),
                MovableBlockFalling(
                    scene.get_texture("meat.png"), width * 0.7, height * 0.79
                ),
                MovableBlockFalling(
                    scene.get_texture("milk.png"), width * 0.91, height * 0.79
                ),
                MovableBlockFalling(
                    scene.get_texture("milk.png"), width * 0.91, height * 0.79
                ),
            ]
            if random.random() > 0.95:
                items.append(
                    MovableBlockFalling(
                        scene.get_texture("penis.png"), width * 0.90, height * 0.30
                    )
                )
            else:
                items.append(
                    MovableBlockFalling(
                        scene.get_texture("penis_bread.png"),
                        width * 0.93,
                        height * 0.30,
                    )
                )

            self.items_manager = arcade.SpriteList()
            random.shuffle(items)
            for i in items:
                self.layers.append(
                    {
                        "sprite": i,
                        "speed": 0.4,
                        "original_x": i.center_x,
                        "original_y": i.center_y,
                    }
                )
                self.items_manager.append(i)
            for i in self.layers:
                self.layers_sprite_list.append(i["sprite"])

            self.on_mouse_motion(self.window._mouse_x, self.window._mouse_y, 0, 0)

            self.table = {
                "Boobles.png": ("+ Лашчк", (218, 148, 111)),
                "cheremsha.png": ("+ Черемша", (149, 177, 125)),
                "crisps.png": ("+ Чипсеке", (103, 82, 64)),
                "meat.png": ("+ Лисья печень", (103, 82, 64)),
                "milk.png": ("+ Молочк Эпштейна", (189, 192, 212)),
                "penis.png": ("+ Дидлок", (159, 100, 118)),
                "penis_bread.png": ("+ Хлеб 100%", (199, 189, 181)),
                "pineapple.png": ("+ Дикий ананас", (210, 184, 138)),
                "puki.png": ("+ Пуки", (240, 234, 203)),
                "cheese.png": ("+ Козий сыр", (240, 200, 100)),
                "tomatoes.png": (
                    "+ Помидоры Скидка 15%! 1+1=3! Только сегодня по новой скидке. Действует до 24.09.2077г! Приведите друга и получите 1488 козьих сыров по ссылке https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    (255, 99, 71),
                ),
                "teramisu.png": ("+ Терамису", (131, 91, 58)),
                "eggs.png": ("+ Яйца мамонта", (31, 206, 203)),
            }

            self.notifiers = []

            self.return_button = agui.UIFlatButton(
                text="Продолжить",
                x=self.width * 0.90,
                y=self.height * 0.05,
                style=g.STYLE_DEFAULT_BUTTON,
                width=200,
            )
            self.return_button.on_click = return_back
            self.return_button_manager = agui.UIManager()
            self.return_button_manager.add(self.return_button)
            self.return_button_manager.enable()

        def on_draw(self) -> None:
            self.clear()
            g.scene.draw()
            self.layers_sprite_list.draw()
            for i in self.notifiers:
                if i.visible:
                    i.draw()
            self.return_button_manager.draw()
            self.settings_manager.draw()

            super().on_draw()

        def plus_item(self, name):
            if name in self.NAMESPACE["Define"].collected_items:
                self.NAMESPACE["Define"].collected_items[name] += 1
            else:
                self.NAMESPACE["Define"].collected_items[name] = 1

        def on_update(self, delta_time: float) -> None:
            super().on_update(delta_time)
            g.scene.update(delta_time)
            # if len(list(self.return_button_manager.get_widgets_at((self.window._mouse_x, self.window._mouse_y)))) == 0:
            self.items_manager.update(delta_time, self.window.mouse.data)
            for i in self.notifiers:
                i.update(delta_time)

            for e, i in enumerate(self.items_manager):
                if i.clicked:
                    self.items_manager.append(self.items_manager.pop(e))

                if i.center_y < -30:
                    filename = get_real_filename(i.texture.file_path.name)
                    self.plus_item(get_real_filename(filename))
                    print(self.NAMESPACE["Define"].collected_items)
                    text_data = self.table[get_real_filename(filename)]
                    text: arcade.Text = ItemsNotifText(
                        text_data[0], i.center_x, i.center_y, text_data[1], g.FONT_NAME
                    )
                    self.notifiers.append(text)
                    self.items_manager.remove(i)
                    i.kill()
                    del i

            g.actions.update(delta_time)

        def on_key_press(self, key: int, modifiers: int) -> bool | None:
            if key == arcade.key.S or key == arcade.key.ESCAPE:
                self.settings_manager.turn_visibl()

        def _move_parallax(self, layer, x, y):
            normalized_x = (x - self.width // 2) / (self.width // 2)
            normalized_y = (y - self.height // 2) / (self.height // 2)

            max_offset_x = 100 * layer["speed"]
            max_offset_y = 60 * layer["speed"]

            layer["sprite"].center_x = layer["original_x"] + normalized_x * max_offset_x
            layer["sprite"].center_y = layer["original_y"] + normalized_y * max_offset_y

        def on_mouse_motion(self, x, y, dx, dy):

            if self.settings_manager.waiting_settings:
                return None

            for e, layer in enumerate(self.layers):
                if hasattr(layer["sprite"], "freeze"):
                    if layer["sprite"].freeze:
                        self._move_parallax(layer, x, y)
                    else:
                        self.layers.append(self.layers.pop(e))
                else:
                    self._move_parallax(layer, x, y)

                if layer["sprite"].center_y < -30:
                    self.layers.remove(layer)

    class CTW(GameViewTemplate):
        def __init__(self):
            super().__init__(
                using_sprites=[
                    "golub.png",
                    "golub_click.png"
                ]
            )

            # self.window.set_vsync(True)
            self.NAMESPACE = g.main.NAMESPACE
            self.fm = g.fm

            self.settings_manager = SettingsManager()
            self.settings_manager.enable()

            self.sprites = [
                g.scene.get_sprite("golub.png"),
                g.scene.get_sprite("golub_click.png"),
            ]
            for i in self.sprites:
                i.center_x = self.center_x
                i.center_y = self.center_y
                i.width = self.width
                i.height = self.height

            self.draw_sprite = self.sprites[0]

            self.clicks = 1
            self.max_clicks = 42

            self.click_text = arcade.Text(
                f"0 / {self.max_clicks}", 0, 0, arcade.color.BLACK, 54
            )
            self.click_text.x = self.window.width * 0.02
            self.click_text.y = self.window.height * 0.95
            self.length = 10

            self.timer = time.time()

        def on_draw(self) -> None:
            self.clear()
            g.scene.draw()
            arcade.draw_sprite(self.draw_sprite)
            self.click_text.draw()
            arcade.draw_lrbt_rectangle_filled(
                self.width * 0.2,
                self.width * 0.8,
                self.height * 0.85,
                self.height * 0.95,
                (0, 0, 0, 120),
            )
            arcade.draw_lrbt_rectangle_filled(
                self.width * 0.21,
                self.width * 0.79,
                self.height * 0.87,
                self.height * 0.93,
                (0, 0, 0, 255),
            )
            try:
                arcade.draw_lrbt_rectangle_filled(
                    self.width * 0.21,
                    (self.width * 0.79) * self.length / 10,
                    self.height * 0.87,
                    self.height * 0.93,
                    (255, 255, 255, 255),
                )
            except ValueError:
                pass

            self.settings_manager.draw()

            super().on_draw()

        def on_key_press(self, key: int, modifiers: int) -> bool | None:
            if key == arcade.key.S or key == arcade.key.ESCAPE:
                self.settings_manager.turn_visibl()
            if key == arcade.key.SPACE:
                self.draw_sprite = self.sprites[1]
                self.clicks += 1
                self.click_text.text = f"{self.clicks} / {self.max_clicks}"

        def on_key_release(self, symbol: int, modifiers: int) -> bool | None:
            if symbol == arcade.key.SPACE:
                self.draw_sprite = self.sprites[0]

        def on_update(self, delta_time: float) -> None:
            if self.clicks >= self.max_clicks + 1:
                print(self.clicks, self.max_clicks)
                self.window.show_view(self.window.GameView)

            if time.time() - self.timer >= 1:
                self.timer = time.time()
                self.length -= 1

            if self.length <= 0:
                self.NAMESPACE["Lore"].jump("bad_ending_golubi")
                self.window.show_view(self.window.GameView)

            g.actions.update(delta_time)

    class ShopGetting(GameViewTemplate):
        def __init__(self):
            super().__init__(
                using_sprites=[
                    "background_ponn.png",
                    "background_ponnaqua.png",
                    "koshel.png",
                    "money_two.png",
                    "money_three.png",
                    "money_five.png",
                    "money_seven.png",
                    "money_wth_pon_zalupkin.png",
                    "money_wth.png", "money_wth_clicked.png"
                ]
            )

            def return_back(event=None):
                self.window.show_view(self.window.GameView)

            # self.window.set_vsync(True)
            self.NAMESPACE = g.main.NAMESPACE
            self.fm = g.fm

            self.layers = []
            scene = g.scene
            self.layers.append(
                {
                    "sprite": scene.get_sprite("background_ponn.png"),
                    "speed": 0.0,
                    "original_x": self.width // 2,
                    "original_y": self.height // 2,
                }
            )
            self.layers.append(
                {
                    "sprite": scene.get_sprite("background_ponn.png"),
                    "speed": 0.1,
                    "original_x": self.width // 2,
                    "original_y": self.height // 2,
                }
            )
            self.layers.append(
                {
                    "sprite": scene.get_sprite("background_ponnaqua.png"),
                    "speed": 0.15,
                    "original_x": self.width // 2,
                    "original_y": self.height // 2,
                }
            )
            koshel = scene.get_sprite("koshel.png")
            koshel.scale = 2.0
            self.layers.append(
                {
                    "sprite": scene.get_sprite("koshel.png"),
                    "speed": 0.2,
                    "original_x": self.width * 0.2,
                    "original_y": self.height * 0.2,
                }
            )

            self.settings_manager = SettingsManager()
            self.settings_manager.enable()

            self.collecting_zone = (
                self.width * 0.5,
                self.width * 0.97,
                self.height * 0.5,
                self.height * 0.97,
            )

            self.table = {
                "money_two.png": 2,
                "money_three.png": 3,
                "money_five.png": 5,
                "money_seven.png": 7,
                "money_wth_pon_zalupkin.png": 0,
                "money_wth.png": 0,
            }

            width = self.width
            height = self.height
            items = [
                MovableBlock(
                    scene.get_texture("money_two.png"),
                    width * 0.25,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                    True,
                ),
                MovableBlock(
                    scene.get_texture("money_two.png"),
                    width * 0.25,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                    True,
                ),
                MovableBlock(
                    scene.get_texture("money_two.png"),
                    width * 0.25,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                    True,
                ),
                MovableBlock(
                    scene.get_texture("money_two.png"),
                    width * 0.25,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                    True,
                ),
                MovableBlock(
                    scene.get_texture("money_three.png"),
                    width * 0.38,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                    True,
                ),
                MovableBlock(
                    scene.get_texture("money_three.png"),
                    width * 0.38,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                    True,
                ),
                MovableBlock(
                    scene.get_texture("money_five.png"),
                    width * 0.51,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                    True,
                ),
                MovableBlock(
                    scene.get_texture("money_five.png"),
                    width * 0.51,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                    True,
                ),
                MovableBlock(
                    scene.get_texture("money_five.png"),
                    width * 0.51,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                    True,
                ),
                MovableBlock(
                    scene.get_texture("money_five.png"),
                    width * 0.51,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                    True,
                ),
                MovableBlock(
                    scene.get_texture("money_seven.png"),
                    width * 0.64,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                    True,
                ),
                MovableBlock(
                    scene.get_texture("money_seven.png"),
                    width * 0.64,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                    True,
                ),
                MovableBlock(
                    scene.get_texture("money_seven.png"),
                    width * 0.64,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                    True,
                ),
                MovableBlock(
                    scene.get_texture("money_seven.png"),
                    width * 0.64,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                    True,
                ),
            ]
            coins = [
                (2, 3),  # 3 монеты по 2
                (3, 2),  # 2 монеты по 3
                (5, 4),  # 2 монеты по 5
                (7, 4),  # 4 монеты по 7
            ]

            random.shuffle(items)

            items.insert(
                0,
                MovableBlock(
                    scene.get_texture("money_wth_pon_zalupkin.png"),
                    width * 0.51,
                    height * 0.2,
                    100,
                    0.6,
                    self.collecting_zone,
                ),
            )
            items.insert(
                0,
                ClickableSprite(
                    [
                        scene.get_texture("money_wth.png"),
                        scene.get_texture("money_wth_clicked.png"),
                    ],
                    width * 0.64,
                    height * 0.2,
                    100,
                    0.6,
                ),
            )

            self.items_manager = arcade.SpriteList()
            for i in items:
                self.layers.append(
                    {
                        "sprite": i,
                        "speed": 0.3,
                        "original_x": i.center_x,
                        "original_y": i.center_y,
                        "collected": False,
                    }
                )
                self.items_manager.append(i)

            self.on_mouse_motion(self.window._mouse_x, self.window._mouse_y, 0, 0)

            self.NAMESPACE["Define"].should_money = random.choice(
                self.find_reachable_sums(coins)
            )
            self.NAMESPACE["Define"].got_money = 0

            self.return_button = agui.UIFlatButton(
                text="Продолжить",
                x=self.width * 0.90,
                y=self.height * 0.05,
                style=g.STYLE_DEFAULT_BUTTON,
                width=200,
            )
            self.return_button.on_click = return_back
            self.return_button_manager = agui.UIManager()
            self.return_button_manager.add(self.return_button)
            self.return_button_manager.enable()

            self.should_money_manager = agui.UIManager()
            self.should_money_text = agui.UILabel(
                "Внешний долг ЖАКЛИН:",
                font_name=g.FONT_NAME,
                font_size=40,
                bold=True,
                text_color=arcade.color.BLACK,
            )

            text = f"{self.NAMESPACE['Define'].should_money} Путинкоинов"

            self.should_money_counter = agui.UILabel(
                text,
                font_name=g.FONT_NAME,
                font_size=40,
                text_color=arcade.color.SCARLET,
            )
            self.should_money_box = agui.UIBoxLayout(
                align="left", x=self.width * 0.01, y=self.height * 0.8
            )
            self.should_money_box.with_background(color=(255, 255, 255, 200))

            self.should_money_box.add(self.should_money_text)
            self.should_money_box.add(self.should_money_counter)
            self.should_money_manager.add(self.should_money_box)

        def find_reachable_sums(self, coins, max_sum=None, min_sum=30):
            if max_sum is None:
                max_sum = sum(value * count for value, count in coins)

            if min_sum > max_sum:
                return tuple()

            bits = 1

            for value, count in coins:
                mask = 0
                for k in range(count + 1):
                    mask |= bits << (k * value)

                bits = mask & ((1 << (max_sum + 1)) - 1)

            reachable = []
            for s in range(min_sum, max_sum + 1):
                if (bits >> s) & 1:
                    reachable.append(s)

            return tuple(reachable)

        def on_draw(self) -> None:
            self.clear()
            g.scene.draw()
            for layer in self.layers[:4]:
                arcade.draw_sprite(layer["sprite"])

            arcade.draw_lrbt_rectangle_filled(
                self.collecting_zone[0],
                self.collecting_zone[1],
                self.collecting_zone[2],
                self.collecting_zone[3],
                (0, 0, 0, 125),
            )

            for layer in self.layers[3:]:
                arcade.draw_sprite(layer["sprite"])
            self.should_money_manager.draw()
            self.return_button_manager.draw()
            self.settings_manager.draw()

            super().on_draw()

        def on_update(self, delta_time: float) -> None:
            super().on_update(delta_time)
            g.scene.update(delta_time)
            if (
                len(
                    list(
                        self.return_button_manager.get_widgets_at(
                            (self.window._mouse_x, self.window._mouse_y)
                        )
                    )
                )
                == 0
            ):
                self.items_manager.update(delta_time, self.window.mouse.data)

            for e, i in enumerate(self.items_manager):
                if i.clicked:
                    self.items_manager.append(self.items_manager.pop(e))

            for e, layer in enumerate(self.layers):
                if layer["speed"] != 0.0:
                    if hasattr(layer["sprite"], "clicked"):
                        if layer["sprite"].clicked:
                            self.layers[e]["original_x"] = layer["sprite"].center_x
                            self.layers[e]["original_y"] = layer["sprite"].center_y

                    if hasattr(layer["sprite"], "freezed"):
                        filename = get_real_filename(layer["sprite"].texture.file_path.name)
                        if layer["sprite"].freezed:
                            if not self.layers[e]["collected"]:
                                self.NAMESPACE["Define"].got_money += self.table[
                                    filename
                                ]

                            self.layers[e]["collected"] = True
                        else:
                            if self.layers[e]["collected"]:
                                self.NAMESPACE["Define"].got_money -= self.table[
                                    filename
                                ]
                            self.layers[e]["collected"] = False

            g.actions.update(delta_time)

        def on_key_press(self, key: int, modifiers: int) -> bool | None:
            if key == arcade.key.S or key == arcade.key.ESCAPE:
                self.settings_manager.turn_visibl()

        def _move_parallax(self, layer, x, y):
            normalized_x = (x - self.width // 2) / (self.width // 2)
            normalized_y = (y - self.height // 2) / (self.height // 2)

            max_offset_x = 100 * layer["speed"]
            max_offset_y = 60 * layer["speed"]

            layer["sprite"].center_x = layer["original_x"] + normalized_x * max_offset_x
            layer["sprite"].center_y = layer["original_y"] + normalized_y * max_offset_y

        def on_mouse_motion(self, x, y, dx, dy):

            if self.settings_manager.waiting_settings:
                return None

            for e, layer in enumerate(self.layers):
                if hasattr(layer["sprite"], "clicked"):
                    if not layer["sprite"].clicked:
                        if hasattr(layer["sprite"], "freezed"):
                            if not layer["sprite"].freezed:
                                self._move_parallax(layer, x, y)
                        else:
                            self._move_parallax(layer, x, y)
                    else:
                        self.layers[e]["original_x"] = layer["sprite"].center_x
                        self.layers[e]["original_y"] = layer["sprite"].center_y
                        if (
                            isinstance(layer["sprite"], MovableBlock)
                            and layer["sprite"].collect
                        ):
                            self.layers.append(self.layers.pop(e))

                else:
                    self._move_parallax(layer, x, y)