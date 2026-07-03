from typing import Optional
from arcade import Sprite, get_sprites_at_point, Text, get_window
import random

class MovableBlock(Sprite):
    def __init__(
        self,
        texture,
        center_x=0,
        center_y=0,
        angle=0,
        scale=1.0,
        collecting_zone: Optional[tuple] = None,
        collect: bool = False,
    ):
        super().__init__(path_or_texture=texture)
        self.start_x = center_x
        self.start_y = center_y
        self.start_angle = angle + random.randint(-5, 5)
        self.center_x = int(center_x) + random.randint(-30, 30)
        self.center_y = int(center_y) + random.randint(-15, 30)
        color_rand = random.randint(230, 255)
        self.angle = int(self.start_angle)
        self.color = (color_rand, color_rand, color_rand, 255)
        self.scale = scale
        self.scale_x = self.scale_x * random.randint(95, 105) / 100
        self.scale_y = self.scale_y * random.randint(95, 105) / 100

        self.collecting_zone = collecting_zone
        self.collect = collect

        self.clicked = False
        self.freezed = False

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:

        if 1 in args[0]:
            if args[0][1]:
                if (
                    self.left <= args[0]["x"] <= self.right
                    and self.bottom <= args[0]["y"] <= self.top
                ):
                    list_children = []
                    for i in self.sprite_lists:
                        list_children = list_children + list(
                            get_sprites_at_point((args[0]["x"], args[0]["y"]), i)
                        )
                    if len(list_children) > 0:
                        if list_children[-1] is self:
                            self.clicked = True
                    else:
                        self.clicked = True
            else:
                self.clicked = False

        if self.clicked:
            self.angle = 0
            self.center_x = args[0]["x"]
            self.center_y = args[0]["y"]

        if (
            self.collecting_zone[0] <= self.center_x <= self.collecting_zone[1]
            and self.collecting_zone[2] <= self.center_y <= self.collecting_zone[3]
        ):
            if self.collect:
                if not self.clicked:
                    if not self.freezed:
                        self.center_x = random.randint(
                            int(self.collecting_zone[0] + self.width / 2),
                            int(self.collecting_zone[1] - self.width / 2),
                        )
                        self.center_y = random.randint(
                            int(self.collecting_zone[2] + self.height / 2),
                            int(self.collecting_zone[3] - self.height / 2),
                        )
                    self.freezed = True
            else:
                self.center_x = self.start_x
                self.center_y = self.start_y
                self.angle = self.start_angle
                self.freezed = False
        else:
            if self.freezed:
                self.freezed = False


class MovableBlockFalling(Sprite):
    def __init__(self, texture, center_x=0, center_y=0, scale=1.0):
        super().__init__(path_or_texture=texture)
        self.center_x = int(center_x) + random.randint(-30, 30)
        self.center_y = int(center_y) + random.randint(-15, 30)
        # self.scale = scale
        # self.scale_x = self.scale_x * random.randint(95, 105)/100
        # self.scale_y = self.scale_y * random.randint(95, 105) / 100
        color_rand = random.randint(230, 255)
        self.color = (color_rand, color_rand, color_rand, 255)
        self.clicked = False
        self.freeze = True
        self.falling_speed = 0.0

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:

        if 1 in args[0]:
            if args[0][1]:
                if (
                    self.left <= args[0]["x"] <= self.right
                    and self.bottom <= args[0]["y"] <= self.top
                ):
                    list_children = []
                    for i in self.sprite_lists:
                        list_children = list_children + list(
                            get_sprites_at_point((args[0]["x"], args[0]["y"]), i)
                        )
                    if len(list_children) > 0:
                        if list_children[-1] is self:
                            self.clicked = True
                            self.freeze = False
                    else:
                        self.clicked = True
                        self.freeze = False

            else:
                self.clicked = False

        if self.clicked:
            self.center_x = args[0]["x"]
            self.center_y = args[0]["y"]

        if not self.clicked and not self.freeze:
            self.falling_speed = self.falling_speed - 2500 * delta_time
            self.center_y = self.center_y + self.falling_speed * delta_time
        else:
            self.falling_speed = 0.0


class ItemsNotifText(Text):
    def __init__(self, text, x, y, color, FONT_NAME):
        super().__init__(
            text=text, x=x, y=y, color=color, font_size=35, font_name=FONT_NAME
        )
        self.velocity = 0.0
        self.color = (
            self.color[0] + 10 if self.color[0] + 10 <= 255 else self.color[0],
            self.color[1] + 10 if self.color[1] + 10 <= 255 else self.color[1],
            self.color[2] + 10 if self.color[2] + 10 <= 255 else self.color[2],
            225,
        )
        self.bold = True

        self.window = get_window()

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        self.velocity = self.velocity + 200 * delta_time
        self.y = self.y + self.velocity * delta_time

        if self.y > self.window.height + 300:
            self.visible = False


class ClickableSprite(Sprite):
    def __init__(self, textures: list, center_x=0, center_y=0, angle=0, scale=1.0):
        super().__init__(path_or_texture=textures[0])
        self.start_angle = angle + random.randint(-5, 5)
        self.center_x = int(center_x) + random.randint(-30, 30)
        self.center_y = int(center_y) + random.randint(-15, 30)
        color_rand = random.randint(230, 255)
        self.angle = int(self.start_angle)
        self.color = (color_rand, color_rand, color_rand, 255)
        self.scale = scale
        self.scale_x = self.scale_x * random.randint(95, 105) / 100
        self.scale_y = self.scale_y * random.randint(95, 105) / 100

        self.textures = textures
        self.clicked = False

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:

        if 1 in args[0]:
            if args[0][1]:
                if (
                    self.left <= args[0]["x"] <= self.right
                    and self.bottom <= args[0]["y"] <= self.top
                ):
                    list_children = []
                    for i in self.sprite_lists:
                        list_children = list_children + list(
                            get_sprites_at_point((args[0]["x"], args[0]["y"]), i)
                        )
                    if len(list_children) > 0:
                        if list_children[-1] is self:
                            self.clicked = True
                    else:
                        self.clicked = True

            else:
                self.clicked = False

        if self.clicked:
            self.set_texture(1)
        else:
            self.set_texture(0)
