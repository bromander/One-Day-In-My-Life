import copy
from pathlib import Path
import types

from arcade import Sprite

from .namespace import Namespace
from .load_animated_gif import load_animated_gif
from .scene import Scene

from .globals import g


class LoreLogger:
    def __init__(self):
        self.logs: list[dict] = []

    ### ==== AUDIO ===

    def _snapshot_audio(self):
        return_data = {}

        if g.am.music.player:
            music = {
                "path": str(g.am.music.now_playing_path),
                "loop": g.am.music.player.loop,
                "pitch": g.am.music.player.pitch,
                # "paused": g.am.music.paused,
                "streaming": True,
                "default_volume": g.am.music.default_volume,
                "local_modifier": g.am.music._local_modifier,
                "modifier": g.am.music.modifier,
                "fade_modifier": 1.0,
            }
            return_data["music"] = music

        if g.am.sound.player:
            sound = {
                "path": str(g.am.sound.now_playing_path),
                "loop": g.am.sound.player.loop,
                "pitch": g.am.sound.player.pitch,
                # "paused": g.am.sound.paused,
                "streaming": False,
                "default_volume": g.am.sound.default_volume,
                "local_modifier": g.am.sound._local_modifier,
                "modifier": g.am.sound.modifier,
                "fade_modifier": 1.0,
            }
            return_data["sound"] = sound

        if g.am.voice.player:
            voice = {
                "path": str(g.am.voice.now_playing_path),
                "loop": g.am.voice.player.loop,
                "pitch": g.am.voice.player.pitch,
                # "paused": g.am.voice.paused,
                "streaming": False,
                "default_volume": g.am.voice.default_volume,
                "local_modifier": g.am.voice._local_modifier,
                "modifier": g.am.voice.modifier,
                "fade_modifier": 1.0,
            }
            return_data["voice"] = voice

        return return_data

    def _restore_audio(self, snapshot):

        if "music" not in snapshot:
            g.am.music.stop()
        if "sound" not in snapshot:
            g.am.sound.stop()
        if "voice" not in snapshot:
            g.am.voice.stop()

        for channel_name, music_data in snapshot.items():
            music_player = g.am.__getattribute__(channel_name)

            if str(music_player.now_playing_path) == str(music_data["path"]):
                continue

            music_player.play(
                music_data["path"],
                music_data["loop"],
                music_data["pitch"],
                music_data["local_modifier"],
                music_data["streaming"],
            )

            # if music_data["paused"]:
            #    music_player.pause()

            music_player.default_volume = music_data["default_volume"]
            music_player.modifier = music_data["modifier"]
            music_player._local_modifier = music_data["local_modifier"]

    ### ==== SCENE ===

    def _snapshot_scene(self):
        snapshot = []

        for layer, layer_data in g.scene.data.items():
            if layer in ("fade", "gui"):
                continue

            container = g.scene[layer]

            # --- dict слои ---
            if layer == "bg_parallax":
                for item in container:
                    snapshot.append(
                        {
                            "type": "parallax",
                            "layer": layer,
                            "data": {
                                "texture": str(item["sprite"].texture.file_path.name),
                                "speed": item["speed"],
                                "original_x": item["original_x"],
                                "original_y": item["original_y"],
                            },
                        }
                    )
            elif layer == "animated_sprites":
                for name, sprite in container.items():
                    snapshot.append(
                        {
                            "type": "animated_sprite",
                            "layer": layer,
                            "name": name,
                            "data": {
                                "texture": sprite.texture.file_path,
                                "center_x": sprite.center_x,
                                "center_y": sprite.center_y,
                                "width": sprite.width,
                                "height": sprite.height,
                                "angle": sprite.angle,
                                "alpha": sprite.alpha,
                                "visible": sprite.visible,
                            },
                        }
                    )
            else:
                for name, sprite in container.items():
                    snapshot.append(
                        {
                            "type": "sprite",
                            "layer": layer,
                            "name": name,
                            "data": {
                                "texture": sprite.texture.file_path,
                                "center_x": sprite.center_x,
                                "center_y": sprite.center_y,
                                "width": sprite.width,
                                "height": sprite.height,
                                "angle": sprite.angle,
                                "alpha": 255,  # при возврате назад, если к спрайтам применялся эффект растворения, то их 'растворяющиеся' версии остаются на сцене.
                                # Пока оставлю значение 255 как заглушку, но это надо в будущем пофиксить
                                "visible": sprite.visible,
                            },
                        }
                    )

        return {"snapshot": snapshot, "characters_slice": int(g.scene.characters_slice)}

    def _check_sprite_in_scene(self, sprite_data: dict):
        scene = g.scene

        sprite_name = str(Path(sprite_data["texture"]).name)

        same_old_sprite = None

        for layer, layer_data in scene.data.items():
            if layer in ("fade", "gui", "bg_parallax"):
                continue

            for sprite in layer_data.items():
                sprite: Sprite = sprite[1]
                if str(sprite.texture.file_path.name) == sprite_name:
                    same_old_sprite = sprite
                    break

            if same_old_sprite:
                if (
                    (
                        same_old_sprite.center_x == sprite_data["center_x"]
                        and same_old_sprite.center_y == sprite_data["center_y"]
                    )
                    and (
                        same_old_sprite.width == sprite_data["width"]
                        and same_old_sprite.height == sprite_data["height"]
                    )
                    and (same_old_sprite.angle == sprite_data["angle"])
                    and (same_old_sprite.alpha == sprite_data["alpha"])
                    and (same_old_sprite.visible == sprite_data["visible"])
                ):
                    return same_old_sprite

        return None

    def _restore_scene(self, data):

        snapshot = data["snapshot"]

        new_scene = Scene()
        new_scene["fade"] = g.scene["fade"]
        new_scene["gui"] = g.scene["gui"]

        for entry in snapshot:
            t = entry["type"]

            if t == "sprite":
                d = entry["data"]

                same_old_sprite = self._check_sprite_in_scene(d)
                if same_old_sprite:
                    new_scene.add_sprite(entry["layer"], entry["name"], same_old_sprite)
                    continue

                sprite = Sprite(d["texture"])
                sprite.center_x = d["center_x"]
                sprite.center_y = d["center_y"]
                sprite.width = d["width"]
                sprite.height = d["height"]
                sprite.angle = d["angle"]
                sprite.alpha = d["alpha"]
                sprite.visible = d["visible"]

                new_scene.add_sprite(entry["layer"], entry["name"], sprite)

            elif t == "animated_sprite":
                d = entry["data"]

                same_old_sprite = self._check_sprite_in_scene(d)
                if same_old_sprite:
                    new_scene.add_sprite(entry["layer"], entry["name"], same_old_sprite)
                    continue

                sprite = load_animated_gif(d["texture"])[0]
                sprite.center_x, sprite.center_y = d["center_x"], d["center_y"]
                sprite.width, sprite.height = d["width"], d["height"]
                sprite.angle = d["angle"]
                sprite.alpha = d["alpha"]
                sprite.visible = d["visible"]

                new_scene.add_sprite(entry["layer"], entry["name"], sprite)

            elif t == "parallax":
                d = entry["data"]

                new_scene.add_parallax_bg(
                    d["texture"], d["speed"], d["original_x"], d["original_y"]
                )

        new_scene["fade"]["splash"].alpha = 0
        g.main.splash_manager.children[0][0].update_font(font_color=(255, 255, 255, 0))
        g.main.splash_manager.children[0][1].update_font(font_color=(255, 255, 255, 0))
        new_scene["fade"]["fade"].alpha = 0

        g.scene = new_scene
        g.scene.set_characters_slice(data["characters_slice"])

    ### ==== NAMESPACE ===

    def _snapshot_namespace(self):
        variables = {}
        functions = {}
        classes = {}
        modules = {}
        defines = {}
        persistents = {}

        find_last_unnecessary_object = False  # (__builtins__)

        for name, value in g.main.NAMESPACE.NAMESPACE.items():
            if not find_last_unnecessary_object and str(name) != "__builtins__":
                # Скипаем все стартовые функции т.к. они нам не нужны. __builtins__ - всегда самая последняя
                continue
            else:
                find_last_unnecessary_object = True

            if name.startswith("__") and name.endswith("__"):
                continue
            if isinstance(value, type):
                classes[name] = copy.copy(value)
            elif callable(value):
                functions[name] = copy.copy(value)
            elif isinstance(value, types.ModuleType):
                modules[name] = value
            else:
                variables[name] = copy.copy(value)

        for name, value in g.main.NAMESPACE["Define"].get_all_variables().items():
            defines[name] = copy.copy(value)

        for name, value in g.sm.Persistent.get_all_persistents().items():
            persistents[name] = copy.copy(value)

        return_data = {
            "variables": variables,
            "functions": functions,
            "classes": classes,
            "modules": modules,
            "defines": defines,
            "persistents": persistents,
        }

        return return_data

    def _restore_namespace(self, data: dict[str:dict]):

        new_namespace = Namespace(g)

        for name, value in data["variables"].items():
            new_namespace.NAMESPACE[name] = value

        for name, value in data["functions"].items():
            new_namespace.NAMESPACE[name] = value

        for name, value in data["classes"].items():
            new_namespace.NAMESPACE[name] = value

        for name, value in data["modules"].items():
            new_namespace.NAMESPACE[name] = value

        for name, value in data["defines"].items():
            new_namespace["Define"].__setattr__(name, value)

        for name, value in data["persistents"].items():
            new_namespace["Persistent"].__setattr__(name, value)

        g.main.NAMESPACE = new_namespace

    ### ==== GENERATORS ===

    def _snapshot_generators(self):
        gens = g.actions.active_generators
        return {
            "consistently": [
                gen
                for gen in gens.active_generators_consistently
                if not gen[0].startswith("talk")
            ],
            "together": copy.copy(gens.active_generators_together),
        }

    def _restore_generators(self, data):
        gens = g.actions.active_generators
        gens.clear()

        gens.active_generators_consistently = copy.copy(data["consistently"])
        gens.active_generators_together = copy.copy(data["together"])

        while gens.active_generators_consistently or gens.active_generators_together:
            gens.update(1 / 1000)

    ### ==== ATTRIBUTES ===

    def _snapshot_attributes(self):
        a = g.attributes
        return copy.deepcopy(
            {
                "character_name": a.character_name,
                "character_text": a.character_text,
                "character_name_colour": a.character_name_colour,
                "character_text_colour": a.character_text_colour,
                "text_anchor": a.text_anchor,
            }
        )

    def _restore_attributes(self, data):
        a = g.attributes

        a.character_name = data["character_name"]
        a.character_text = data["character_text"]
        a.character_name_colour = data["character_name_colour"]
        a.character_text_colour = data["character_text_colour"]
        a.text_anchor = data["text_anchor"]

    ### ==== WWL ===

    def _snapshot_lore(self):
        lm = g.lm
        return copy.deepcopy({"pose": lm.pose, "label": lm.label})

    def _restore_lore(self, data):
        g.lm.jump(data["label"], data["pose"])

    ### ==== Main functions ===

    def create_log(self):
        """
        Создаёт 'Снимок' текущего состояния игры
        """

        snapshot = {
            "scene": self._snapshot_scene(),
            "namespace": self._snapshot_namespace(),
            "generators": self._snapshot_generators(),
            "attributes": self._snapshot_attributes(),
            "lore": self._snapshot_lore(),
            "audio": self._snapshot_audio(),
        }

        self.logs.append(snapshot)

    def return_back(self, event=None):
        """
        Возвращает игру на последний созданный снимок
        :return:
        """

        if g.main.waiting_autoskip:
            return None

        if len(self.logs) < 2:
            return

        # удаляем текущий
        self.logs.pop()

        data = self.logs[-1]

        # восстановление
        self._restore_namespace(data["namespace"])
        self._restore_attributes(data["attributes"])
        self._restore_lore(data["lore"])
        self._restore_generators(data["generators"])
        self._restore_scene(data["scene"])
        self._restore_audio(data["audio"])

        g.main.talk_manager(-1, clicked=True, do_snapshot=False)

        g.main.set_bg_by_scene_bg()
