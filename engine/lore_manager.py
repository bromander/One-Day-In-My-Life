import os
from pathlib import Path
import re
from base64 import b64encode, b64decode
from binascii import Error as binascii_Error
import zlib, json
import ast
from typing import Optional, Union
from functools import lru_cache

from .globals import g

logger = g.get_logger(__name__)


class LoreFileManager:
    def __init__(self, lore_files: list[Path]):
        """
        Работает с файлами сценария и их скомпилированными версиями
        :param lore_files: Список объектов pathlib.Path, ведущих к файлам сценария
        """
        self.lore_files = lore_files

        self.delete_unused_compiled()

    def delete_unused_compiled(self):
        compiled_files = self._find_files(g.DEFAULT_LORE_COMPILED_FILE_EXT)

        for filepath in compiled_files:
            if (
                not filepath.with_suffix(g.DEFAULT_LORE_FILE_EXT).exists()
                and filepath.exists()
            ):
                logger.debug(f"Удаляем ненужный скомпилированный файл {filepath.name}!")
                filepath.unlink()

    def _find_files(
        self, extension: str, start_path: Union[str] = "./game"
    ) -> list[Path]:

        start = Path(start_path).absolute()
        results = []
        for entry in os.scandir(start):
            if entry.is_dir():
                results.extend(self._find_files(extension, entry.path))
            elif entry.name.lower().endswith(extension.lower()):
                results.append(Path(entry.path))
        return results

    def _check_file_jpya(self, jpy_filepath: Path) -> bool:
        return jpy_filepath.with_suffix(g.DEFAULT_LORE_COMPILED_FILE_EXT).exists()

    def _check_jpy_last_edit(self, filepath: Path) -> bool:

        jpy_last_edit = float(filepath.stat().st_mtime)

        jpyc_filepath = filepath.with_suffix(g.DEFAULT_LORE_COMPILED_FILE_EXT)
        jpyc_last_edit = float(
            self._get_uncompiled_file_data(jpyc_filepath)["last_updated"]
        )

        return jpy_last_edit == jpyc_last_edit

    def _should_recompile(self, filepath: Path) -> bool:
        if not self._check_file_jpya(filepath):
            return True
        if not self._check_jpy_last_edit(filepath):
            return True

        return False

    def get_lore_by_files(self) -> dict[Path:dict]:
        """
        Просматривает каждый скомпилированный файл и берёт из него данные, если они актуальны.
        Может передавать None вместо данных, если они не были скомпилированны
        """

        lore_by_files = {}

        for filepath in self.lore_files:
            if not self._should_recompile(filepath):
                labels_data = {}

                jpyc_filepath = filepath.with_suffix(g.DEFAULT_LORE_COMPILED_FILE_EXT)
                file_data = self._get_uncompiled_file_data(jpyc_filepath)

                for label, label_data in file_data["label_data"].items():
                    unzipped_label_data = self._unzip_data(label_data, label)

                    if unzipped_label_data is None:
                        labels_data = None
                        break

                    labels_data[label] = unzipped_label_data

                lore_by_files[filepath.absolute()] = labels_data
            else:
                lore_by_files[filepath.absolute()] = None

        return lore_by_files

    def save_compile_data(self, lore_by_files: dict, files_to_recompile: list[str]):
        """
        Сохраняет актуальные скомпилированные данные файла сценария
        :param lore_by_files: Словарь {Путь к файлу : Данные лейблов}
        :param files_to_recompile: Список абсолютных путей к файлам
        :return:
        """
        recompile_set = set(files_to_recompile)
        abs_paths = {fp: str(fp) for fp in lore_by_files}
        for filename, labels in lore_by_files.items():
            if self._should_recompile(filename) or abs_paths[filename] in recompile_set:
                self._compile_file(filename, labels)

    def _compile_file(self, filepath: Path, labels: dict[str:dict]):

        jpyc_filepath = filepath.with_suffix(g.DEFAULT_LORE_COMPILED_FILE_EXT)

        compiled_labels = {
            label_name: self._zip_data(compiled_data)
            for label_name, compiled_data in labels.items()
        }

        write_data = {
            "last_updated": filepath.stat().st_mtime,
            "label_data": compiled_labels,
        }

        with jpyc_filepath.open("w", encoding="UTF-8") as file:
            json.dump(write_data, file)

    def _get_uncompiled_file_data(self, filepath: Path):

        with filepath.open("r", encoding="UTF-8") as file:
            return json.load(file)

    def _zip_data(self, data: dict) -> str:
        return b64encode(
            zlib.compress(json.dumps(data, ensure_ascii=False).encode("utf-8"), 9)
        ).decode("ascii")

    def _unzip_data(self, data: str, label_name: str = None) -> Optional[dict]:
        try:
            loaded = json.loads(zlib.decompress(b64decode(data)))
        except (  # Обрабатываем случаи, если данные были повреждены
            binascii_Error,
            ValueError,
            TypeError,  # Повреждения на уровне Base64
            zlib.error,  # Повреждения на уровне zlib
            json.JSONDecodeError,
            UnicodeDecodeError,  # Повреждения на уровне JSON
        ):
            logger.error(
                f"Данные лейбла {label_name} были повреждены! Перекомпилируем..."
            )
            loaded = None

        return loaded


class LoreManager:
    """
    Отвечает за всю работу с файлами сценария.
    Парсит, обрабатывает и всему тому подобное...
    """

    def __init__(self):
        lore_files = self._find_files(g.DEFAULT_LORE_FILE_EXT)

        lore_data_by_files = self.get_lore_data_by_files(lore_files)

        self.lore = dict(
            (k, v)
            for file_data in lore_data_by_files.values()
            for k, v in file_data.items()
        )

        logger.debug(
            f"Обнаружено Файлов сценария: {len(lore_files)}, Лейблов: {len(self.lore)}"
        )

        self.graf = self._create_graf(self.lore)

        self.pose = 0
        self.label = g.DEFAULT_START_LABEL

        self.load_assets(self.label)

    def get_lore_data_by_files(self, lore_files: list[Path]) -> dict:
        """
        Работает с кешированными уже скомпилированными файлами и возвращает словарь с уже обработанным сценарием
        :param lore_files: Список Path объектов к файлам сценария
        """

        lore_files_manager = LoreFileManager(lore_files)

        lore_data_by_files = lore_files_manager.get_lore_by_files()

        reorganize = Reorganize()

        should_recompile = False

        reorganized_files = []

        for filepath, label_data in lore_data_by_files.items():
            if label_data is None:
                should_recompile = True
                lore_data_by_files[filepath] = reorganize.reorganize_file(filepath)
                reorganized_files.append(str(filepath.absolute()))

        reorganize.check_for_character.cache_clear()

        if should_recompile:
            logger.info(
                f"Файлы сценария были перекомпилированны! Всего: {len(reorganized_files)}, [{', '.join(reorganized_files)}]"
            )
            lore_files_manager.save_compile_data(lore_data_by_files, reorganized_files)
        else:
            logger.debug("Файлы сценария не были изменены!")

        return lore_data_by_files

    def _find_files(
        self, extension: str, start_path: Union[str] = "./game"
    ) -> list[Path]:

        start = Path(start_path).absolute()
        results = []
        for entry in os.scandir(start):
            if entry.is_dir():
                results.extend(self._find_files(extension, entry.path))
            elif entry.name.lower().endswith(extension.lower()):
                results.append(Path(entry.path))
        return results

    def _create_graf(self, lore_data: dict) -> dict[str : list[str]]:
        """
        Создаёт граф всего сюжета
        """

        graf = {}

        for label_name in lore_data.keys():
            for line in lore_data[label_name]["lore"]:
                under_lines = [i.lstrip() for i in line.splitlines()]

                for line in under_lines:
                    if "Lore.jump(" in line:
                        label_jump = re.split(r"[()]", line)
                        label_jump = label_jump[
                            label_jump.index("Lore.jump") + 1
                        ]  # Ну вдург там скобки ещё поставит ктот
                        label_jump = label_jump.strip("'")

                        if label_name not in graf:
                            graf[label_name] = [
                                label_jump,
                            ]
                        else:
                            graf[label_name].append(label_jump)
        return graf

    def _can_unload_asset(
        self,
        filename: str,
        label: str,
        scan_now: bool = True,
        scan_next: bool = True,
        scan_last=True,
    ) -> bool:
        """
        Проверяет, можно ли выгрузить ассет из файлов игры.
        Смотрит, требуется ли ассет в прошлом, текущем и следующем лейбле. Если нету - True
        :param filename: Название файла
        :param label: Лейбл
        :param scan_now: Проверяет по текущему лейблу
        :param scan_next: Проверяет по следующему лейблу
        :param scan_last: Проверяет по прошлому лейблу
        :return: Булевое значение, можно ли выгрузить ассет
        """

        if filename in g.IGNORE_FILES_FOR_UNLOADING:
            return False

        if filename not in g.fm.textures and filename not in g.fm.audios:
            return False

        # ассеты текущего лейбла
        if scan_now:
            if filename in self.lore[label]["assets"]:
                return False

        # ассеты прошлого лейбла
        if scan_last:
            last_labels = {
                node for node, neighbors in self.graf.items() if label in neighbors
            }
            for last_label in last_labels:
                if filename in self.lore[last_label]["assets"]:
                    return False

        # ассеты следующего лейла
        if scan_next:
            if label in self.graf:
                for graf_label in self.graf[label]:
                    if filename in self.lore[graf_label]["assets"]:
                        return False

        return True

    def unload_assets(
        self,
        label,
        scan_now: bool = True,
        scan_next: bool = True,
        scan_last=True,
    ) -> None:
        """
        Выгружает ненужные ассеты из памяти
        :param label: Название текущего лейбла
        :param scan_now: Проверяет по текущему лейблу
        :param scan_next: Проверяет по следующему лейблу
        :param scan_last: Проверяет по прошлому лейблу
        """

        loaded_assets = set(g.fm.textures.copy().keys()).union(
            set(g.fm.audios.copy().keys())
        )

        files_pack = [
            file_name
            for file_name in loaded_assets
            if self._can_unload_asset(file_name, label, scan_now, scan_next, scan_last)
            and not g.scene.find_sprite_in_scene(file_name)
        ]

        if files_pack:
            g.fm.unload_assets(files_pack, label)

    def _get_assets_pack(
        self, label, load_now: bool = True, load_next: bool = True, load_last=True
    ) -> dict[str : list[str]]:
        """
        Создаёт пак с ассетами, которые используются в текущих, прошлых и следующих лейблах
        :param label: Текущий лейбл
        :param load_now: Смотреть ли ассеты в текущем лейбле
        :param load_next: Смотреть ли ассеты в следующем лейбле
        :param load_last: Смотреть ли ассеты в прошлом лейбле
        :return: словарь название {лейбла : список ассетов}
        """

        assets_pack = {}

        if load_last:
            # асеты с прошлого лейбла
            last_labels = {
                node for node, neighbors in self.graf.items() if label in neighbors
            }
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

        return assets_pack

    def load_assets(self, label) -> None:
        """
        Загружает ассеты текущих, прошлых и следующих лейблов в память
        :param label: Название текущего лейбла
        """

        assets_pack = self._get_assets_pack(label)

        for label, assets in assets_pack.items():
            g.fm.load_assets(assets, label)

        self.unload_assets(label)

    def jump(self, label: str, pose: int) -> None:
        """
        Перемещает нас в сюжете.
        Также, загружает ассеты и выгружает ненужные
        :param label: Лейбл, куда нужно перенестись
        :param pose: Позиция в сюжете
        """
        self.label = label
        self.pose = pose

        if self.lore[label]["caption"]:
            g.main.NAMESPACE.execute(f"Lore.set_part({self.lore[label]['caption']})")

        self.load_assets(label)

    def get_thing(self, pos_offset=0) -> dict:
        """
        Возвращает инструкцию для текущего момента сюжета и двигает его дальше
        """

        self.pose += pos_offset

        block = self.lore[self.label]["lore"][self.pose]
        lore = {"action": "EXECUTE", "data": block}

        self.pose += 1

        return lore


class Reorganize:
    """
    "Реорганизует", парсит и обрабатывает файл сюжета для дальнейшей работы
    """

    def __init__(self):

        # Паттерн:
        # [^"\\] – любой символ, кроме " и \ (обратной косой черты)
        # \\. – любая escape-последовательность (например, \", \\, \n и т.д.)
        # (?: ... )* – незахватывающая группа, повторяющаяся ноль или более раз
        # Всё вместе захватывается в группу ((?:[^"\\]|\\.)*)
        self.pattern = re.compile(
            r'^(\s*)<([^>]+)>\s*"((?:[^"\\]|\\.)*)"', flags=re.MULTILINE
        )
        self.quotation_pattern = re.compile(r'["\'](.*?)["\']')

    def _del_trash(self, text: str) -> str:
        """
        Удаляет пустые и закомментированные строки, а также убирает лишнюю табуляцию
        :param text: Текст файла сюжета
        """
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
        """
        Заменяет вызовы персонажей на функцию talk()
        :param text: Текст файла сюжета
        """

        text = re.sub(
            r"<\s*>", "<narr>", text
        )  # Заменяем пустые значения айди персонажа на narrator-а

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
        """
        На основе уже подготовленного файла сюжета, собирает его в структурируемый и удобный словарь
        :param text: Текст файла сюжета
        """

        lines = text.splitlines()

        paths = {}
        lore_points = {}
        point_start = 0

        for index, line in enumerate(lines):
            line = line.lstrip()

            if line.startswith("label"):
                label_name = line.replace("label ", "").split("(")[0]
                label_data = re.split(r"[()]", line)[1]

                paths[label_name] = {"caption": label_data, "assets": [], "lore": []}

                point_start = (label_name, index + 1)

            elif "end(" in line or "Lore.jump(" in line:
                lore_points[point_start[0]] = (point_start[1], index + 1)

        for label_name, label_points in lore_points.items():
            unsplit = "\n".join(lines[label_points[0] : label_points[1]])
            split = self._split_code(unsplit)

            paths[label_name]["lore"] = split
            paths[label_name]["assets"] = self._guess_assets(unsplit)

        paths = self._check_assets(paths)

        return paths

    def _split_code(self, unsplitted_lore: str) -> list:
        """
        Разделяет код на строки, на основе python-синтаксиса
        """

        try:
            tree = ast.parse(unsplitted_lore)
            statements = [ast.unparse(node) for node in tree.body]
        except SyntaxError:
            logger.critical("Обнаружена ошибка в синтаксисе файла сценария!")
            raise

        return statements

    @lru_cache(1024)
    def check_for_character(self, name: str) -> Optional[str]:
        """
        Проверяет потенциальное название файла персонажа, на то, является ли оно им
        """

        for format in g.SUPPORTED_IMAGE_FORMATS:
            potential_asset = name + format

            if potential_asset in g.fm.textures_paths:
                return potential_asset

        return None

    def _create_graf(self, lore_data: dict) -> dict[str : list[str]]:

        graf = {}

        for label_name in lore_data.keys():
            for line in lore_data[label_name]["lore"]:
                under_lines = [i.lstrip() for i in line.splitlines()]

                for line in under_lines:
                    if "Lore.jump(" in line:
                        label_jump = re.split(r"[()]", line)
                        label_jump = label_jump[
                            label_jump.index("Lore.jump") + 1
                        ]  # Ну вдург там скобки ещё поставит ктот
                        label_jump = label_jump.strip("'")

                        if label_name not in graf:
                            graf[label_name] = [
                                label_jump,
                            ]
                        else:
                            graf[label_name].append(label_jump)
        return graf

    def _check_assets(self, paths: dict[str:dict]) -> dict:
        first = True

        graph = self._create_graf(paths)

        for label_name, label_data in paths.items():
            if first:
                first = False
                continue

            if "set_scene(" not in "".join(label_data["lore"]):
                labels_to = [
                    node for node, neighbors in graph.items() if label_name in neighbors
                ]

                for label_to in labels_to:
                    paths[label_name]["assets"] += paths[label_to]["assets"]
                    paths[label_name]["assets"] = list(set(paths[label_name]["assets"]))

        return paths

    def _guess_assets(self, unsplit_lore: str) -> list[str]:
        """
        Смотрит строку кода и парсит все строки в кавычках, пытаясь найти в них файлы с ассетами.
        """

        potential_assets = set(
            i
            for i in re.findall(r'["\'](.*?)["\']', unsplit_lore)
            if not bool(re.search("[а-яА-ЯёЁ]", i))
        )
        founded_assets = []

        for potential_asset in potential_assets:
            format = "." + potential_asset.split(".")[-1]
            if (
                format in g.SUPPORTED_IMAGE_FORMATS
                or format in g.SUPPORTED_AUDIO_FORMATS
                and potential_asset not in founded_assets
            ):
                founded_assets.append(potential_asset)
            else:
                check_for_character = self.check_for_character(potential_asset)

                if check_for_character and check_for_character not in founded_assets:
                    founded_assets.append(check_for_character)

        return founded_assets

    def reorganize_file(self, file_path: Path) -> dict:
        """
        Полностью организует и обрабатывает файлы сюжета, возвращая готовый материал для работы.
        :param file_path: Путь к файлам сюжета.
        :return: Возвращает подготовленные данные лейбла
        """

        with file_path.open("r", encoding="UTF-8") as lore_file:
            lore_file_data = lore_file.read()

        lore_file_data = self._del_trash(lore_file_data)
        lore_file_data = self._replace_characters_call(lore_file_data)

        labels_data = self._structure(lore_file_data)

        return labels_data
