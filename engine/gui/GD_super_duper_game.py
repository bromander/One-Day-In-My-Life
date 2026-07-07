import time
from typing import Optional

from PIL import Image
import arcade
import math
import random
import time as Time

from ..globals import g
from ..audio import AudioChannel


sfx_channel = AudioChannel(super=True)


class SmartWall(arcade.SpriteList):
    def __init__(self):
        super().__init__()

        window = arcade.get_window()
        wall_texture = g.fm.get_texture("smart_wall.png")

        self.wall_sprite_1 = arcade.Sprite(wall_texture)
        self.wall_sprite_2 = arcade.Sprite(wall_texture)
        self.wall_sprite_3 = arcade.Sprite(wall_texture)

        self.append(self.wall_sprite_1)
        self.append(self.wall_sprite_2)
        self.append(self.wall_sprite_3)

        self.wall_sprite_1.center_x = window.center_x
        self.wall_sprite_1.center_y = window.center_y

        self.wall_sprite_2.left = self.wall_sprite_1.right
        self.wall_sprite_2.center_y = window.center_y

        self.wall_sprite_3.left = self.wall_sprite_2.right
        self.wall_sprite_3.center_y = window.center_y

        self.speed = 100

        self.lead_wall_index = 0

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        # Двигаем все стены влево
        self.wall_sprite_1.center_x -= self.speed * delta_time
        self.wall_sprite_2.center_x -= self.speed * delta_time
        self.wall_sprite_3.center_x -= self.speed * delta_time

        walls = [self.wall_sprite_1, self.wall_sprite_2, self.wall_sprite_3]

        lead_wall = walls[self.lead_wall_index]

        if lead_wall.right <= 0:
            next_index = (self.lead_wall_index + 1) % 3
            next_wall = walls[next_index]

            last_index = (self.lead_wall_index - 1) % 3
            last_wall = walls[last_index]

            last_wall.left = next_wall.right

            self.lead_wall_index = next_index

    def set_color(self, color):
        if color != self.wall_sprite_1.color:
            self.wall_sprite_1.color = color
            self.wall_sprite_2.color = color
            self.wall_sprite_3.color = color


class DefaultBullet(arcade.Sprite):
    def __init__(self, sprite_name: str, start_y: int, speed: float, start_x_modif: int = 0, spin_speed: float = 0, pattern: str = "default"):

        self.bullet_type = "DefaultBullet"

        self.window = arcade.get_window()
        self.sprite_name = sprite_name
        self.speed = speed
        self.spin_speed = spin_speed
        self.pattern = pattern
        self.time = 0
        self.start_y = start_y

        texture = g.fm.get_texture(self.sprite_name)
        self.death_texture = g.fm.get_texture("gangster_god_plz_save_us.png")

        super().__init__(
            texture,
            center_x=self.window.width + texture.width + start_x_modif + 50,
            center_y=start_y
        )

        self.radius = random.randint(10, 100)
        self.wave_pon = random.randint(50, 150)

        self.position = (float(self.center_x), float(self.center_y))
        self.not_real_angle = self.angle

        self.death = False
        self.waiter_death = 0

        self.strength = 1

        self.scale = 1.5

    def self_destroy(self, use_strength: bool = True):
        if random.random() > 0.85 and use_strength:
            self.strength -= 0.5
            self.color = (180, 180, 180, 255)
        else:
            self.strength -= 1

        if self.strength <= 0:
            self.color = (255, 255, 255, 255)
            sfx_channel.play(g.fm.get_audio("deltarune-explosion.mp3"), speed=random.randint(8, 12)/10)
            self.texture = self.death_texture
            self.scale = (
                random.randint(int(self.scale[0] * 10), int((self.scale[0] + 2) * 10)) / 10,
                random.randint(int(self.scale[0] * 10), int((self.scale[0] + 1) * 10)) / 10
            )
            self.angle = random.randint(0, 360)
            self.waiter_death = Time.time()
            self.hit_box = arcade.hitbox.HitBox(
                (
                    (0, 0),
                    (0, 0),
                    (0, 0),
                    (0, 0)
                )
            )
            self.death = True

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:

        self.center_x -= self.speed * delta_time

        if self.death:
            if Time.time() - self.waiter_death > 2:
                self.kill()
            return None


        self.time += delta_time

        if self.pattern == "sine":
            # Синусоида
            self.center_y = self.start_y + self.radius * math.sin(self.time * 3)

        elif self.pattern == "wave":
            # Волна с другой частотой
            self.center_y = self.start_y + self.wave_pon * math.sin(self.time * 2)

        elif self.pattern == "circle":
            # Круговая траектория
            self.center_x -= self.speed * delta_time * 0.5
            self.center_y = self.start_y + self.radius * math.sin(self.time * 2)
            self.center_x += self.radius * math.cos(self.time * 2) * 0.3

        elif self.pattern == "spiral":
            # Спираль
            radius = self.radius + self.time * 30
            self.center_x -= self.speed * delta_time * 0.7
            self.center_y = self.start_y + radius * math.sin(self.time * 3)
            self.center_x += radius * math.cos(self.time * 3) * 0.2

        elif self.pattern == "random":
            self.center_y += random.uniform(-5, 5)
            if self.center_y > self.window.height:
                self.center_y = self.window.height - 10
            elif self.center_y < 0:
                self.center_y = 10

        # Обновляем позицию
        self.position = (float(self.center_x), float(self.center_y))

        # Проверка на выход за экран
        if self.center_x < 50:
            self.self_destroy()

        # Вращение
        if self.spin_speed > 0:
            self.angle += self.spin_speed * delta_time
        elif self.spin_speed < 0:
            self.not_real_angle += self.spin_speed * delta_time
            self.angle = self.not_real_angle % 360

class AdBullet(DefaultBullet):
    def __init__(self, sprite_name: str, start_y: int, speed: float, start_x_modif: int = 0, spin_speed: float = 0, pattern: str = "default"):
        super().__init__(sprite_name, start_y, speed, start_x_modif, spin_speed, pattern)

        self.bullet_type = "AdBullet"

        self.orig_image = self.texture.image.copy()

        self.scale = 0.8

        self.break_texture: Optional[arcade.Texture] = None

        self.state = 0

    def break_self(self):

        if random.random() > 0.15:
            self.state += 1

        if self.state > 4:
            return True

        texture = g.fm.get_texture(f"breaking_{int(self.state)}.png")
        if texture == self.break_texture:
            return False

        self.break_texture = g.fm.get_texture(f"breaking_{int(self.state)}.png")

        bg = self.orig_image
        fg = self.break_texture.image

        if fg.size != bg.size:
            fg = fg.resize(bg.size)

        bg = Image.alpha_composite(bg, fg)

        new_texture = arcade.Texture(bg)

        self.texture = new_texture

        return False

    def self_destroy(self, use_strength: bool = False):
        if self.sprite_name == "lonely_1.png":
            self.sprite_name = "lonely_2.png"
            self.texture = g.fm.get_texture("lonely_2.png")
        elif not self.sprite_name == "lonely_2.png":
            ret = self.break_self()
            if ret:
                self.scale = 2
                super().self_destroy(use_strength)
        else:
            if self.center_x < 0 - self.width:
                super().self_destroy(use_strength)

class VeryInterestingBullet(DefaultBullet):
    def __init__(self, start_y: int, speed: float, start_x_modif: int = 0, spin_speed: float = 0, pattern: str = "default"):
        super().__init__("gangster_normis.png", start_y, speed, start_x_modif, spin_speed, pattern)

        self.attack_texture = g.fm.get_texture("gangster_attack.png")

        self.wait = 0

        self.boomed = False

    def self_destroy(self, use_strength: bool = False):
        self.boom(wait=False)

        if self.wait == 0:
            self.wait = time.time()

        while time.time() - self.wait < 0.4:
            return None

        self.kill()

    def boom(self, wait = True):

        if not self.boomed:
            sfx_channel.play(g.fm.get_audio("gaster-vanish.mp3"), local_volume=666.0)
            self.texture = self.attack_texture
            self.speed /= 2

        self.boomed = True

        if wait:
            if self.wait == 0:
                self.wait = time.time()

            while time.time() - self.wait < 0.5:
                return None

        self.texture = self.death_texture
        self.scale = 3.0
        self.scale = (
            random.randint(int(self.scale[0] * 10), int((self.scale[0] + 2) * 10)) / 10,
            random.randint(int(self.scale[0] * 10), int((self.scale[0] + 1) * 10)) / 10
        )
        sfx_channel.play(g.fm.get_audio("deltarune-explosion.mp3"), speed=0.5)
        self.angle = random.randint(0, 360)
        self.sync_hit_box_to_texture()

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:
        super().update(delta_time)

        if kwargs["player_pos"][0] + self.width > self.center_x:
            self.boom()



class Player(arcade.Sprite):
    def __init__(self):

        hitbox = arcade.hitbox.HitBox(
            (
                (-10, -6),
                (-10, 6),
                (10, 6),
                (10, -6)
            )
        )

        self.window = arcade.get_window()

        texture = g.fm.get_texture("stamen.png")

        super().__init__(texture, 0.5, self.window.width*0.1, self.window.center_y)

        self.hit_box = hitbox

        self.move_up = None
        self.speed = 500

    def update(self, delta_time: float = 1 / 60, *args, **kwargs) -> None:

        if self.move_up is True:

            self.angle = 315
            self.center_y = self.center_y + self.speed * delta_time

        elif self.move_up is False:

            self.angle = 45
            self.center_y = self.center_y - self.speed * delta_time

        else:
            self.angle = 0