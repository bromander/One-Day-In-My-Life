import os
import re
import ast
import copy
from arcade import Sprite
from typing import Optional
from .files_manager import FilesManager
from .Exceptions import MainLabelNotFoundError
from .audio import AudioManager


class Wwl:

    def __init__(self, fm: FilesManager, find_files_path: str = "./game"):
        """
        Отвечает за обработку сценариев
        """

        self.fm: FilesManager = fm

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

        def get_assets(string: str):
            sprites = []
            for i in string.split("\n"):
                i = i.strip(" ")
                potential_assets = re.findall(r'["\']([^"\']*)["\']', i)
                for i in potential_assets:
                    i = str(i)
                    if len(i.split(".")) > 1:
                        if i in self.fm.textures_paths or i in self.fm.audio_paths:
                            sprites.append(i)
                    else:
                        for o in [".png", ".jpg", ".jpeg", ".PNG", ".JPEG", ".gif", ".GIF"]:
                            i = i + o
                            if i in self.fm.textures_paths or i in self.fm.audio_paths:
                                sprites.append(i)
            return sprites

        if label not in self.fm.loaded_labels:
            assets = get_assets(self.files[self.now_file]["content"][label])
            self.fm.load_assets(assets, label)

    def _get_lore(self):
        for e, i in self.files.items():
            if self.label in i['content']:
                self.now_file = e

        label = []
        index = 0
        files = self.files[self.now_file]["content"][self.label].strip().split("\n")

        self._preload_assets(self.label)
        if self.label in self.graf:
            for i in self.graf[self.label]:
                self._preload_assets(i)

        while len(files) > index:
            index += 1
            i = files[index-1].strip()
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

                        while index < len(files):
                            next_line = files[index].strip()

                            if (next_line.startswith("<") or
                                    next_line.startswith("$") or
                                    next_line.startswith("{") or
                                    next_line.startswith("label")):
                                break

                            data += files[index][4:] + "\n"
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
    def __init__(self, main_self, wwl: Wwl, am: AudioManager):
        self.main_self =  main_self
        self.wwl = wwl
        self.am = am
        self.logs = []

    def _snapshot_scene(self):
        snapshot = []
        for layer, layer_data in self.main_self.scene.data.items():
            if layer == "fade" or layer == "gui":
                continue

            try:
                if isinstance(self.main_self.scene[layer], dict):
                    for name, sprite in self.main_self.scene[layer].items():
                        sprite: Sprite = sprite

                        data = {
                            "name" : name,
                            "layer" : layer,
                            "pos" : sprite.position,
                            "size" : sprite.size,
                            "angle" : sprite.angle,
                            "alpha" : sprite.alpha,
                            "texture_name" : sprite.texture.file_path.name,
                            "visible" : sprite.visible,
                        }
                        snapshot.append(data)

                elif isinstance(self.main_self.scene[layer], list):
                    for attributes in self.main_self.scene[layer]:
                        data = {
                            "layer": layer,
                            "texture_name" : attributes['sprite'].texture.file_path.name,
                            'speed': attributes["speed"],
                            'original_x': attributes["original_x"],
                            'original_y': attributes['original_y']
                        }

                        snapshot.append(data)
            except AttributeError:
                pass
        return snapshot

    def _load_snapshot_scene(self, snapshot: list[dict]):
        for i in snapshot:
            if i["layer"] != "bg_parallax":
                sprite = self.main_self.scene.get_sprite(i["texture_name"])
                sprite.size, sprite.angle, sprite.visible, sprite.position, sprite.alpha = i["size"], i["angle"], i["visible"], i["pos"], i["alpha"]
                self.main_self.scene.add_sprite(i["layer"], i["name"], sprite)
            else:
                self.main_self.scene.add_parallax_bg(i["texture_name"], i["speed"], i["original_x"], i["original_y"])

    def _snapshot_namespace(self):
        for name, value in self.main_self.NAMESPACE.NAMESPACE.items():
            variables = {}
            functions = {}
            classes = {}

            if name.startswith('__') and name.endswith('__'):
                continue

            if isinstance(value, type):
                classes[name] = copy.copy(value)
            elif callable(value):
                functions[name] = copy.copy(value)
            else:
                variables[name] = copy.copy(value)

            return variables, functions, classes




    def create_log(self):

        scene_snapshot = list(self._snapshot_scene())
        namespace = copy.copy(self.main_self.NAMESPACE.NAMESPACE)

        gens = copy.copy(self.main_self.actions.active_generators.active_generators_consistently)
        for i in self.main_self.actions.active_generators.active_generators_consistently:
            if i[0] == 'talk':
                gens.remove(i)

        active_generators = copy.copy(self.main_self.actions.active_generators)
        attributes = copy.copy(self.main_self.attributes)
        lore_pos = copy.deepcopy(self.wwl.pose)
        lore_label = copy.deepcopy(self.wwl.label)
        lore_file = copy.deepcopy(self.wwl.now_file)

        self.logs.append({
            "scene_snapshot" : scene_snapshot,
            "namespace": namespace,
            "active_generators" : active_generators,
            "attributes" : {
                "character_name" : copy.copy(attributes.character_name),
                "character_text" : copy.copy(attributes.character_text),
                "character_name_colour" : copy.copy(attributes.character_name_colour),
                "character_text_colour" : copy.copy(attributes.character_text_colour),
                "text_anchor" : copy.copy(attributes.text_anchor)
            },
            "lore_pos" : lore_pos, "lore_label" : lore_label, "lore_file" : lore_file
        })

    def return_back(self, event=None):
        try:
            data = dict(self.logs[-2])
            self.main_self.actions.active_generators.clear()
            del self.logs[-1]
            self.wwl._get_lore()
            self._load_snapshot_scene(data["scene_snapshot"])
            self.main_self.NAMESPACE.NAMESPACE = data["namespace"]

            self.main_self.actions.active_generators = copy.copy(data["active_generators"])

            gens = self.main_self.actions.active_generators
            while gens.active_generators_consistently or gens.active_generators_together:
                gens.update(1 / 1000)

            self.wwl.pose, self.wwl.label, self.wwl.now_file = data["lore_pos"], data["lore_label"], data["lore_file"]

            self.main_self.attributes.text_anchor = data["attributes"]["text_anchor"]
            self.main_self.attributes.character_name = data["attributes"]["character_name"]
            self.main_self.attributes.character_text = data["attributes"]["character_text"]
            self.main_self.attributes.character_name_colour = data["attributes"]["character_name_colour"]
            self.main_self.attributes.character_text_colour = data["attributes"]["character_text_colour"]

            self.main_self.talk_manager(-1, clicked=True)
        except IndexError:
            pass



