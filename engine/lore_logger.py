import copy
import types

from arcade import Sprite

from .audio import AudioManager
from .files_manager import FilesManager
from .namespace import Namespace

from .globals import g


class LoreLogger:
    def __init__(self):
        self.logs: list[dict] = []

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
                    snapshot.append({
                        "type": "parallax",
                        "layer": layer,
                        "data": {
                            "texture": str(item["sprite"].texture.file_path.name),
                            "speed": item["speed"],
                            "original_x": item["original_x"],
                            "original_y": item["original_y"],
                        }
                    })
            else:
                for name, sprite in container.items():
                    snapshot.append({
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
                            "alpha": sprite.alpha,
                            "visible": sprite.visible,
                        }
                    })

        return snapshot

    def _restore_scene(self, snapshot):

        g.scene.clear_scene()

        for entry in snapshot:
            t = entry["type"]

            if t == "sprite":
                d = entry["data"]

                sprite = Sprite(d["texture"])
                sprite.center_x = d["center_x"]
                sprite.center_y = d["center_y"]
                sprite.width = d["width"]
                sprite.height = d["height"]
                sprite.angle = d["angle"]
                sprite.alpha = d["alpha"]
                sprite.visible = d["visible"]

                g.scene.add_sprite(entry["layer"], entry["name"], sprite)

            elif t == "parallax":
                d = entry["data"]

                g.scene.add_parallax_bg(
                    d["texture"],
                    d["speed"],
                    d["original_x"],
                    d["original_y"]
                )

        g.scene["fade"]["splash"].alpha = 0
        g.main.splash_manager.children[0][0].update_font(font_color=(255, 255, 255, 0))
        g.main.splash_manager.children[0][1].update_font(font_color=(255, 255, 255, 0))
        g.scene["fade"]["fade"].alpha = 0

    ### ==== NAMESPACE ===

    def _snapshot_namespace(self):
        variables = {}
        functions = {}
        classes = {}
        modules = {}
        defines = {}
        persistents = {}

        find_last_unnecessary_object = False # (__builtins__)

        for name, value in g.main.NAMESPACE.NAMESPACE.items():

            if not find_last_unnecessary_object and str(name) != "__builtins__":
                # Скипаем все стартовые функции т.к. они нам не нужны. __builtins__ - всегда самая последняя
                continue
            else:
                find_last_unnecessary_object = True


            if name.startswith('__') and name.endswith('__'):
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
            "modules" : modules,
            "defines": defines,
            "persistents" : persistents
        }

        return return_data

    def _restore_namespace(self, data: dict[str : dict]):

        new_namespace = Namespace()
        g.main.NAMESPACE = new_namespace

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

    ### ==== GENERATORS ===

    def _snapshot_generators(self):
        gens = g.main.actions.active_generators
        return {
            "consistently": [
                g for g in gens.active_generators_consistently
                if not g[0].startswith("talk")
            ],
            "together": copy.copy(gens.active_generators_together)
        }

    def _restore_generators(self, data):
        gens = g.main.actions.active_generators
        gens.clear()

        gens.active_generators_consistently = copy.copy(data["consistently"])
        gens.active_generators_consistently_async = copy.copy(data["consistently"])
        gens.active_generators_together = copy.copy(data["together"])

        while gens.active_generators_consistently or gens.active_generators_together or gens.active_generators_consistently_async:
            gens.update(1 / 1000)

    ### ==== ATTRIBUTES ===

    def _snapshot_attributes(self):
        a = g.attributes
        return copy.deepcopy({
            "character_name": a.character_name,
            "character_text": a.character_text,
            "character_name_colour": a.character_name_colour,
            "character_text_colour": a.character_text_colour,
            "text_anchor": a.text_anchor
        })

    def _restore_attributes(self, data):
        a = g.attributes

        a.character_name = data["character_name"]
        a.character_text = data["character_text"]
        a.character_name_colour = data["character_name_colour"]
        a.character_text_colour = data["character_text_colour"]
        a.text_anchor = data["text_anchor"]

    ### ==== WWL ===

    def _snapshot_lore(self):
        wwl = g.wwl
        return copy.deepcopy({
            "pose": wwl.pose,
            "label": wwl.label,
            "file": wwl.now_file
        })

    def _restore_lore(self, data):
        wwl = g.wwl
        wwl.pose = data["pose"]
        wwl.label = data["label"]
        wwl.now_file = data["file"]

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
            "lore": self._snapshot_lore()
        }

        self.logs.append(snapshot)

    def return_back(self, event=None):
        """
        Возвращает игру на последний созданный снимок
        :return:
        """
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

        g.main.talk_manager(-1, clicked=True, do_snapshot=False)