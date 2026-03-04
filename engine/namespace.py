from typing import Optional, Literal, Tuple
import sys, os
import arcade
from .saves import Saves_manager


class Namespace:
    def __init__(self, GameView, ListCharacters, Wwl, AudioManager, Wait_trigger):
        self.Game_view = GameView
        self.ListCharacters = ListCharacters()
        self.Wwl = Wwl
        self.AudioManager = AudioManager
        self.Wait_trigger = Wait_trigger
        self.NAMESPACE = {
            "Persistent": self.Persistent(),
            "Define": self.Define(),
            "Scene": self.Scene(GameView, ListCharacters(), Wwl, Wait_trigger),
            "Audio": self.Audio(GameView, AudioManager),
            "Lore": self.Lore(GameView),
            "SpriteEffects": self.SpriteEffects(),
            "wait": self.wait
        }

    def __getitem__(self, item):
        return self.NAMESPACE[item]

    def execute(self, command: str):
        exec(command, self.NAMESPACE)

    def get(self, key: str, default: any = None):
        return self.NAMESPACE.get(key, default)

    class Persistent:

        def __setattr__(self, name, value):
            Saves_manager().persistent.set_persistent(name, value)
            super().__setattr__(name, value)

        def __getattribute__(self, item):
            super().__setattr__(item, Saves_manager().persistent.get_persistent(item))
            return Saves_manager().persistent.get_persistent(item)

    class Define:
        def __init__(self):
            object.__setattr__(self, 'defines', {})

        def __setattr__(self, name, value):
            defines = object.__getattribute__(self, 'defines')
            defines[name] = value
            object.__setattr__(self, name, value)

        def __getattribute__(self, name):
            if name == 'defines':
                return object.__getattribute__(self, 'defines')
            try:
                return object.__getattribute__(self, name)
            except AttributeError:
                defines = object.__getattribute__(self, 'defines')
                return defines.get(name, {})

    class Scene:
        def __init__(self, Game_view, ListCharacters, Wwl, Wait_trigger):
            self.Game_view = Game_view
            self.ListCharacters = ListCharacters
            self.Wwl = Wwl
            self.Wait_trigger = Wait_trigger

        def show_sprite(self, character: str,
                        at: Optional[Tuple[str, tuple]] = None,
                        effect: Optional[classmethod] = None,
                        stream: Literal["consistently", "together"] = "consistently"):

            char_id = character.split(" ")[0]
            sprite = self.ListCharacters[char_id].show(character)
            if at is not None:
                sprite.center_y = sprite.height / 2
                match at:
                    case "center":
                        sprite.center_x = self.Game_view.width // 2
                    case "left":
                        sprite.center_x = (self.Game_view.width // 2) * 0.4
                    case "right":
                        sprite.center_x = (self.Game_view.width // 2) * 1.6
                    case _ if type(at) is tuple:

                        if at[0] == -1:
                            at = (self.Game_view.scene["characters"][char_id].position[0] / self.Game_view.width, at[0])
                        if at[1] == -1:
                            at = (
                            at[0], self.Game_view.scene["characters"][char_id].position[1] / self.Game_view.height)

                        sprite.center_x = self.Game_view.width * at[0]
                        sprite.center_y = self.Game_view.height * at[1]
            else:
                if char_id in self.Game_view.scene["characters"]:
                    sprite.position = self.Game_view.scene["characters"][char_id].position
                    sprite.scale = self.Game_view.scene["characters"][char_id].scale
                else:
                    sprite.center_x = self.Game_view.width // 2
                    sprite.center_y = self.Game_view.height * 0.2

            if effect is not None:
                sprite.alpha = 0
            else:
                sprite.alpha = 255

            def target():
                self.Game_view.scene.add_sprite("characters", character.split(" ")[0], sprite)
                yield

            self.Game_view.actions.active_generators.add_generator(stream, target(), "show_sprite")
            if effect is not None:
                self.Game_view.actions.active_generators.add_generator(
                    stream,
                    effect.effect(character.split(" ")[0], "characters", self.Game_view),
                    "show_sprite_effect"
                )

        def hide_sprite(self, character: str, effect: Optional[classmethod] = None,
                        stream: Literal["consistently", "together"] = "consistently"):

            def target():
                self.Game_view.scene.delete_sprite("characters", character)
                yield

            if effect is not None:
                self.Game_view.actions.active_generators.add_generator(
                    stream,
                    effect.effect(character, "characters", self.Game_view, 0),
                    "hide_sprite_effect"
                )
            self.Game_view.actions.active_generators.add_generator(stream, target(), "hide_sprite")

        def set_scene(self,
                      file_name: str,
                      scale: float,
                      layer: int = 0,
                      effect: Optional[classmethod] = None,
                      stream: Literal["consistently", "together"] = "consistently"):

            self.Game_view.scene.clear_layer("characters")
            texture = arcade.load_texture(f"game/images/scenes/{file_name}")
            sprite = arcade.Sprite(
                texture,
                scale=scale,
                center_x=self.Game_view.width * 0.5,
                center_y=self.Game_view.height * 0.5
            )

            bg_id = int(layer)
            if effect is not None:
                sprite.alpha = 0
                bg_id = -1
            else:
                self.Game_view.scene.clear_layer("bg")

            def target(bg_id):
                self.Game_view.scene.add_sprite(f"bg", f"bg_{bg_id}", sprite)
                yield

            def edit_layer_name_and_del_old(bg_id, layer):
                old_bg = self.Game_view.scene["bg"][f"bg_{bg_id}"]
                self.Game_view.scene.clear_layer("bg")
                self.Game_view.scene["bg"][f"bg_{layer}"] = old_bg
                yield

            self.Game_view.actions.active_generators.add_generator(stream, target(bg_id), "set_scene")
            if effect is not None:
                self.Game_view.actions.active_generators.add_generator(stream, effect.effect(f"bg_{bg_id}", "bg",
                                                                                             self.Game_view),
                                                                       "set_scene_effect")
                self.Game_view.actions.active_generators.add_generator(stream,
                                                                       edit_layer_name_and_del_old(bg_id, layer),
                                                                       "edit_layer_name_and_del_old")

        def move(self, character: str, position: tuple, speed: float,
                 stream: Literal["consistently", "together"] = "consistently"):
            now = {"character": character, "pos": position, "speed": speed}
            self.Game_view.actions.start_action("move_sprite", now, stream=stream)

        def fade(self, type: Literal["fadein", "fadeout"], duration: float,
                 stream: Literal["consistently", "together"] = "consistently"):
            match type:
                case "fadein":
                    self.Game_view.actions.start_action("fadein", {"time": duration}, stream=stream)
                case "fadeout":
                    self.Game_view.actions.start_action("fadeout", {"time": duration}, stream=stream)

        def show_menu(self, buttons: dict):
            '''
            Пример параметра buttons:
            {
                "Кнопка1" : "Лейбл1",
                "Кнопка2" : "Лейбл3",
                "Сдохнуть" : "Лейбл_сдохнуть"
            }
            '''
            self.Wait_trigger.on()

            self.Game_view.show_menu(buttons)

    class Lore:
        def __init__(self, Game_view):
            self.Game_view = Game_view

        def jump(self, label: str, position: int = 0):
            self.Wwl.pose = position
            self.Wwl.label = label

    class Audio:
        def __init__(self, Game_view, AudioManager):
            self.Game_view = Game_view
            self.AudioManager = AudioManager

        def play(self, channel: Literal["music", "sound"], file_name: str, volume: float = 1.0,
                 loop: Optional[bool] = None, effect: Optional[str] = None,
                 stream: Literal["consistently", "together"] = "together"):
            match channel:
                case "music":
                    loop = True if loop is None else loop
                    target = self.AudioManager.play_music_gen(f"game/music/{file_name}", loop, volume, effect)
                    self.Game_view.actions.active_generators.add_generator(stream, target, "play_music")
                case "sound":
                    loop = False if loop is None else loop
                    target = self.AudioManager.play_sound_gen(f"game/sounds/{file_name}", loop, volume, effect)
                    self.Game_view.actions.active_generators.add_generator(stream, target, "play_sound")

        def stop(self, channel: Literal["music", "sound"], effect: Optional[str] = None,
                 stream: Literal["consistently", "together"] = "together"):
            match channel:
                case "music":
                    self.Game_view.actions.active_generators.add_generator(stream, self.AudioManager.stop_music_gen(effect), "stop_music")
                case "sound":
                    self.Game_view.actions.active_generators.add_generator(stream, self.AudioManager.stop_sound_gen(effect), "stop_sound")

    class SpriteEffects:

        class Dissolve:
            def __init__(self, duration: float = 1.0):
                self.name = "DISSOLVE"
                self.duration = duration

            def effect(self, sprite_name: str, layer: str, Game_view: classmethod, target_alpha: int = 255):

                if sprite_name not in Game_view.scene[layer]:
                    yield
                    return

                sprite = Game_view.scene[layer][sprite_name]
                duration = max(self.duration + Saves_manager().volume.get_other("fade_speed"), 0.001)

                start_alpha = sprite.alpha
                progress = 0.0

                while progress < 1.0:
                    dt = yield

                    if dt is None or dt <= 0:
                        continue

                    progress = min(progress + dt / duration, 1.0)

                    new_alpha = int(start_alpha + (target_alpha - start_alpha) * progress)
                    sprite.alpha = new_alpha

    def wait(self, duration: float):
        self.Wait_trigger.on()
        self.Game_view.actions.start_action("wait", {"time": duration})
