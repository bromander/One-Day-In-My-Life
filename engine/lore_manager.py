import os
from pathlib import Path
import re
import ast
from typing import Optional, Literal, Tuple, Union
from functools import lru_cache

from .globals import g

logger = g.get_logger(__name__)

class LoreManager:
    def __init__(self):
        self.lore_files = self._find_files(g.DEFAULT_LORE_FILE_EXT)

        reorganizer = Reorganizer()
        self.lore = reorganizer.reorganize_files(self.lore_files) # {"labe_name" : {"caption" : "", "assets" : [], "lore" : [""]}}
        reorganizer.check_for_character.cache_clear()

        logger.debug(f"Обнаружено Файлов сценария: {len(self.lore_files)}, Лейблов: {len(self.lore)}")

        print(g.fm.audio_paths)

        self.graf = self._create_graf(self.lore)
        print(self.graf)

        self.pose = 0
        self.label = g.DEFAULT_START_LABEL

        self.load_assets(self.label, load_last=False)


    def _find_files(self, extension: str, start_path: Union[str] = "./game") -> list[Path]:

        if not isinstance(start_path, Path):
            start_path = Path(start_path)

        results = []
        for root, dirs, files in Path.walk(start_path):
            for file in files:
                if file.lower().endswith(extension.lower()):
                    full_path = Path(os.path.join(root, file)).absolute()
                    results.append(full_path)
        return results

    def _create_graf(self, lore_data: dict):
        graf = {}

        for label_name in lore_data.keys():
            for line in lore_data[label_name]['lore']:
                under_lines = [i.lstrip() for i in line.splitlines()]

                for line in under_lines:
                    if "Lore.jump(" in line:
                        label_jump = re.split(r'[()]', line)
                        label_jump = label_jump[label_jump.index('Lore.jump')+1] # Ну вдург там скобки ещё поставит ктот
                        label_jump = label_jump.strip("'")

                        if label_name not in graf:
                            graf[label_name] = [label_jump, ]
                        else:
                            graf[label_name].append(label_jump)
        return graf

    def load_assets(self, label, load_now: bool = True, load_next: bool = True, load_last = True):

        assets_pack = {}

        if load_last:
            # ссеты с прошлого лейбла
            last_labels = [node for node, neighbors in self.graf.items() if label in neighbors]
            for last_label in last_labels:
                assets_pack[last_label] = self.lore[last_label]["assets"]

        if load_now:
            # ассеты текущего лейбла
            assets_pack[label] = self.lore[label]["assets"]

        if load_next:
            # ассеты следующих лейблов
            if label in self.graf:
                for graf_label in self.graf[label]:
                    assets_pack[graf_label] = self.lore[graf_label]["assets"]

        for label, assets in assets_pack.items():
            g.fm.load_assets(assets, label)

    def jump(self, label: str, pose: int):
        self.label = label
        self.pose = pose

        if self.lore[label]["caption"]:
            g.main.NAMESPACE.execute(f"Lore.set_part({self.lore[label]["caption"]})")

        self.load_assets(label)

    def get_thing(self, pos_offset = 0):

        self.pose += pos_offset

        block = self.lore[self.label]['lore'][self.pose]
        lore = {"action": "EXECUTE", "data": block}

        self.pose += 1

        return lore


class Reorganizer:

    def __init__(self):

        # Паттерн:
        # [^"\\] – любой символ, кроме " и \ (обратной косой черты)
        # \\. – любая escape-последовательность (например, \", \\, \n и т.д.)
        # (?: ... )* – незахватывающая группа, повторяющаяся ноль или более раз
        # Всё вместе захватывается в группу ((?:[^"\\]|\\.)*)
        self.pattern = re.compile(r'^(\s*)<([^>]+)>\s*"((?:[^"\\]|\\.)*)"', flags=re.MULTILINE)
        self.quotation_pattern = re.compile(r'["\'](.*?)["\']')

    def _del_trash(self, text: str) -> str:
        lines = text.splitlines()

        def delete(line: str):
            if line.startswith("    "):
                line = line[4:]
            return line

        lines = [i for i in lines if not i.lstrip().startswith("#") and i]
        lines = list(map(delete, lines))

        text = "\n".join(lines)

        return text

    def _replace_characters_call(self, text: str) -> str:
        text = re.sub(r'<\s*>', '<narr>', text) # Заменяем пустые значения айди персонажа на narrator-а

        lines = text.splitlines()

        def transform_code(text: str) -> str:

            def repl(match):
                indent = match.group(1)
                tag = match.group(2)
                content = match.group(3)
                return f'{indent}talk("{tag}", "{content}")'

            return re.sub(self.pattern, repl, text)

        text = "\n".join(list(map(transform_code, lines)))
        return text

    def _structure(self, text: str) -> dict:
        lines = text.splitlines()

        paths = {}
        lore_points = {}
        point_start = 0

        for index, line in enumerate(lines):
            line = line.lstrip()

            if line.startswith("label"):

                label_name = line.replace("label ", "").split("(")[0]
                label_data = re.split(r'[()]', line)[1]

                paths[label_name] = {"caption" : label_data, "assets" : [], "lore" : [], "unsplit_lore" : ""}

                point_start = (label_name, index+1)

            elif "end(" in line or "Lore.jump(" in line:
                lore_points[point_start[0]] = (point_start[1], index+1)

        for label_name, label_points in lore_points.items():
            unsplit = "\n".join(lines[label_points[0] : label_points[1]])
            split = self._split_code(unsplit)

            paths[label_name]["lore"] = split
            paths[label_name]["assets"] = self._guess_assets(unsplit)

        return paths

    def _split_code(self, unsplitted_lore: str) -> list:

        try:
            tree = ast.parse(unsplitted_lore)
            statements = [ast.unparse(node) for node in tree.body]
        except SyntaxError:
            logger.critical("Обнаружена ошибка в синтаксисе файла сценария!")
            raise

        return statements

    @lru_cache(1024)
    def check_for_character(self, name: str):

        for format in g.SUPPORTED_IMAGE_FORMATS:
            potential_asset = name + format

            if potential_asset in g.fm.textures_paths:
                return potential_asset

    def _guess_assets(self, unsplit_lore: str):


        potential_assets = set(i for i in re.findall(r'["\'](.*?)["\']', unsplit_lore) if not bool(re.search('[а-яА-ЯёЁ]', i)))
        founded_assets = []

        for potential_asset in potential_assets:
            format = "." + potential_asset.split(".")[-1]
            if format in g.SUPPORTED_IMAGE_FORMATS or format in g.SUPPORTED_AUDIO_FORMATS:
                founded_assets.append(potential_asset)
            else:

                check_for_character = self.check_for_character(potential_asset)

                if check_for_character:
                    founded_assets.append(check_for_character)

        return founded_assets


    def reorganize_files(self, files: list[Path]):

        lore_file_data = ""

        for path in files:
            with path.open("r", encoding="UTF-8") as lore_file:
                lore_file_data += "\n" + lore_file.read()

        lore_file_data = self._del_trash(lore_file_data)
        lore_file_data = self._replace_characters_call(lore_file_data)

        labels_data = self._structure(lore_file_data)

        return labels_data
