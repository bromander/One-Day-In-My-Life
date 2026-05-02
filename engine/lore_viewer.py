import os
import re
import ast
import copy
from arcade import Sprite
from typing import Optional
from .files_manager import FilesManager
from .Exceptions import MainLabelNotFoundError, LabelNotFoundError
from .audio import AudioManager

from .namespace import Namespace

from .globals import globals as g

class Wwl:

    def __init__(self, find_files_path: str = "./game"):
        """
        Отвечает за обработку сценариев
        """

        def find_files(extension: str, find_files_path: str = "./game"):
            results = {}
            start_path = find_files_path

            for root, dirs, files in os.walk(start_path):
                for file in files:
                    if file.lower().endswith(extension.lower()):
                        full_path = os.path.join(root, file)
                        results[file] = {"path": full_path.replace("\\", "/"), "content": {}}
            return results

        def build_graf():
            graf = {}
            for file_name, file_data in self.files.items():
                file_data = file_data["content"]
                for label, data in file_data.items():
                    for i in data.split("\n"):
                        i = i.strip()
                        if "Lore.jump" in i:

                            label_to = re.findall(r'["\']([^"\']*)["\']', i)[0]
                            if label in graf:
                                graf[label].append(label_to)
                            else:
                                graf[label] = [label_to]
            return graf

        self.files = find_files(".jpy", find_files_path)

        for file_key, file_data in self.files.items():
            """
            Проходимся по всем файлам и делим их на блоки по лейблам
            """
            with open(file_data["path"], "r", encoding="UTF-8") as f:
                content = f.read()
                lines = content.split("\n")

                label_positions = []
                for line_num, line in enumerate(lines):
                    line = line.strip("\n ")
                    if line.startswith("label"):
                        label_name = re.split(r"[() ]", line)[1]
                        label_positions.append((label_name, line_num))

                for i, (label_name, start_pos) in enumerate(label_positions):
                    if i < len(label_positions) - 1:
                        end_pos = label_positions[i + 1][1]
                        block_text = "\n".join(lines[start_pos:end_pos])
                    else:
                        block_text = "\n".join(lines[start_pos:])

                    file_data["content"][label_name] = block_text

        self.pose = 0 # Позиция в сценарии
        self.label = "main" # Текущий лейбл
        self.graf: dict[str: list[str]] = build_graf() # Граф сея сюжета

        self.last_lore_data: Optional[str] = None

        self.now_file = ""
        for e, i in self.files.items():
            if self.label in i['content']:
                self.now_file = e

        if not self.now_file:
            raise MainLabelNotFoundError("Лейбл 'main' не был найден в сценарии!")

        self.lore = self._get_lore()

        def replace_lines_starting_with_tag(text):
            lines = text.splitlines()
            result_lines = []

            for line in lines:
                leading_spaces = re.match(r'^(\s*)', line).group(1)

                if line.lstrip().startswith('<'):
                    line = line.replace("<>", "<narr>") # Заменяем пустые значения айди персонажа на narrator-а
                    dial = re.split(r"[<>]", str(line.lstrip()))
                    dial = [x for x in dial if x]
                    new_line = leading_spaces + f"talk(\"{dial[0]}\", {dial[1]})" # Заменяем все диалоги на функции talk()
                    result_lines.append(new_line)
                elif line.lstrip().startswith('#'):
                    continue
                else:
                    result_lines.append(line)

            return '\n'.join(result_lines)

        for i in self.files:
            for o in self.files[i]["content"]:
                self.files[i]["content"][o] = replace_lines_starting_with_tag(self.files[i]["content"][o])

    def _get_assets(self, string: str):
        fm = g.fm

        sprites = []
        for i in string.split("\n"):
            i = i.strip(" ")
            potential_assets = re.findall(r'["\']([^"\']*)["\']', i)
            for i in potential_assets:
                i = str(i)
                if len(i.split(".")) > 1:
                    if i in fm.textures_paths or i in fm.audio_paths:
                        sprites.append(i)
                else:
                    for o in [".png", ".jpg", ".jpeg", ".PNG", ".JPEG", ".gif", ".GIF"]:
                        i = i + o
                        if i in fm.textures_paths or i in fm.audio_paths:
                            sprites.append(i)
        return sprites

    def parse_label_string(self, label_str, default_values, param_names):

        content = re.sub(r'^label\s+[^(]*\(\s*', '', label_str)
        content = re.sub(r'\s*\)\s*:\s*$', '', content)

        params_list = []
        current_param = ''
        in_quotes = False
        quote_char = ''
        bracket_count = 0

        for char in content:
            if char in ['"', "'"] and not in_quotes:
                in_quotes = True
                quote_char = char
                current_param += char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = ''
                current_param += char
            elif char == '(' and not in_quotes:
                bracket_count += 1
                current_param += char
            elif char == ')' and not in_quotes:
                bracket_count -= 1
                current_param += char
            elif char == ',' and not in_quotes and bracket_count == 0:
                params_list.append(current_param.strip())
                current_param = ''
            else:
                current_param += char

        if current_param.strip():
            params_list.append(current_param.strip())

        params = {}
        position = 0

        for param_str in params_list:
            named_match = re.match(r'(\w+)\s*=\s*(.+)', param_str)

            if named_match:
                key, value = named_match.groups()
                value = value.strip()

                if (value.startswith('"') and value.endswith('"')) or \
                        (value.startswith("'") and value.endswith("'")):
                    params[key] = value[1:-1]
                elif value == 'True':
                    params[key] = True
                elif value == 'False':
                    params[key] = False
                elif value.replace('.', '').replace('-', '').isdigit():
                    params[key] = float(value) if '.' in value else int(value)
                else:
                    params[key] = value
            else:
                value = param_str.strip()

                if (value.startswith('"') and value.endswith('"')) or \
                        (value.startswith("'") and value.endswith("'")):
                    param_value = value[1:-1]
                elif value == 'True':
                    param_value = True
                elif value == 'False':
                    param_value = False
                elif value.replace('.', '').replace('-', '').isdigit():
                    param_value = float(value) if '.' in value else int(value)
                else:
                    param_value = value

                if position < len(param_names):
                    param_name = param_names[position]
                    if param_name not in params:
                        params[param_name] = param_value

                position += 1

        result = default_values.copy()
        result.update(params)

        return result

    def _preload_assets(self, label):
        fm = g.fm

        if label not in fm.loaded_labels:
            assets = []
            for e, i in self.files.items():
                if label in i['content']:
                    self.now_file = e
                    assets = self._get_assets(self.files[self.now_file]["content"][label])
            fm.load_assets(assets, label)

    def _get_lore(self):

        if self.label not in self.files[self.now_file]["content"]:
            for e, i in self.files.items():
                if self.label in i['content']:
                    self.now_file = e

        label = []
        index = 0

        self.last_lore_data = self.files[self.now_file]["content"][self.label].split("\n")

        self._preload_assets(self.label)
        if self.label in self.graf:
            for i in self.graf[self.label]:
                self._preload_assets(i)

        while len(self.last_lore_data) > index:
            index += 1
            i = self.last_lore_data[index-1].strip()
            match i:

                case n if i.strip().startswith("label"):

                    default_values = {
                        'name': '',
                        'description': '',
                        'duration': 1.0,
                        'show_splash': False
                    }
                    param_names = ['name', 'description', 'duration', 'show_splash']
                    data = self.parse_label_string(i.strip(" "), default_values, param_names)
                    label.append({"action": "SHOW_SPLASH", "data": data})

                    continue

                case _:
                    if not i.strip().startswith("label"):
                        data = i + "\n"

                        while index < len(self.last_lore_data):
                            next_line = self.last_lore_data[index].strip()

                            if (next_line.startswith("<") or
                                    next_line.startswith("$") or
                                    next_line.startswith("{") or
                                    next_line.startswith("label")):
                                break

                            data += self.last_lore_data[index][4:] + "\n"
                            index += 1

                        code_blocks = self._split_python_code(data)
                        for block in code_blocks:
                            if block.strip():
                                label.append({"action": "EXECUTE", "data": block})
                    else:
                        print(f"Не найдена команда: {i.strip()}")
        return label

    def _split_python_code(self, code):
        """Разбивает Python код на отдельные top-level блоки"""
        blocks = []
        lines = code.splitlines()

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [code]

        for node in tree.body:
            start_line = node.lineno - 1
            end_line = getattr(node, 'end_lineno', start_line)

            block_lines = lines[start_line:end_line]
            if block_lines:
                block = '\n'.join(block_lines)
                blocks.append(block)

        return blocks

    def get_thing(self, pos_offset: Optional[int] = None, edit_main: bool = True):
        """
        Возвращает готовую инструкцию действий на текущее положение в сценарии
        :param edit_main: Если False, текущее положение в сценарии не изменится
        """
        if edit_main:
            self.pose += pos_offset if pos_offset is not None else 0
            if len(self._get_lore()) - 1 < self.pose:
                self.pose = 0
                return None
            lore = self._get_lore()[self.pose]
            self.pose += 1
            return lore
        else:
            lore = self._get_lore()[self.pose if pos_offset is None else self.pose + pos_offset]
            return lore

class LoreLogger:
    def __init__(self):
        self.logs: list[dict] = []

    def _snapshot_scene(self):
        main = g.main
        snapshot = []

        for layer, layer_data in main.scene.data.items():
            if layer in ("fade", "gui"):
                continue

            container = main.scene[layer]

            # --- dict слои ---
            if isinstance(container, dict):
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

            elif isinstance(container, list):
                for item in container:
                    snapshot.append({
                        "type": "parallax",
                        "layer": layer,
                        "data": {
                            "texture": item["sprite"].texture.file_path,
                            "speed": item["speed"],
                            "original_x": item["original_x"],
                            "original_y": item["original_y"],
                        }
                    })

        return snapshot

    def _restore_scene(self, snapshot):
        main = g.main

        main.scene.clear_scene()

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

                main.scene.add_sprite(entry["layer"], entry["name"], sprite)

            elif t == "parallax":
                d = entry["data"]

                main.scene.add_parallax_bg(
                    d["texture"],
                    d["speed"],
                    d["original_x"],
                    d["original_y"]
                )

    def _snapshot_namespace(self):
        variables = {}
        functions = {}
        classes = {}


        find_last_unnecessary_object = False # (copyright)

        for name, value in g.main.NAMESPACE.NAMESPACE.items():

            if not find_last_unnecessary_object and name != "copyright":
                # Скипаем все стартовые функции т.к. они нам не нужны. copyright - всегда самая последняя
                continue
            else:
                find_last_unnecessary_object = True


            if name.startswith('__') and name.endswith('__'):
                continue
            if isinstance(value, type):
                classes[name] = copy.copy(value)
            elif callable(value):
                functions[name] = copy.copy(value)
            else:
                variables[name] = copy.copy(value)


        return {"variables" : variables, "functions" : functions, "classes" : classes}

    def _restore_namespace(self, data: dict[str : dict]):

        new_namespace = Namespace()
        g.main.NAMESPACE = new_namespace

        for snapshot_data in data.values():
            for name, value in snapshot_data.items():
                new_namespace.NAMESPACE[name] = value

    def _snapshot_generators(self):
        gens = g.main.actions.active_generators
        return {
            "consistently": [
                g for g in gens.active_generators_consistently
                if g[0] != "talk"
            ],
            "together": copy.copy(gens.active_generators_together)
        }

    def _restore_generators(self, data):
        gens = g.main.actions.active_generators
        gens.clear()

        gens.active_generators_consistently = copy.copy(data["consistently"])
        gens.active_generators_together = copy.copy(data["together"])

        while gens.active_generators_consistently or gens.active_generators_together:
            gens.update(1 / 1000)

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

    def create_log(self):
        snapshot = {
            "scene": self._snapshot_scene(),
            "namespace": self._snapshot_namespace(),
            "generators": self._snapshot_generators(),
            "attributes": self._snapshot_attributes(),
            "lore": self._snapshot_lore()
        }

        self.logs.append(snapshot)

    def return_back(self, event=None):
        if len(self.logs) < 2:
            return

        # удаляем текущий
        self.logs.pop()

        data = self.logs[-1]

        # восстановление
        self._restore_scene(data["scene"])
        self._restore_namespace(data["namespace"])
        self._restore_generators(data["generators"])
        self._restore_attributes(data["attributes"])
        self._restore_lore(data["lore"])

        g.main.talk_manager(-1, clicked=True, do_snapshot=False)