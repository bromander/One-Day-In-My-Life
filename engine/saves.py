import copy
import pathlib
import json
import os
from .Exceptions import SaveDoesNotExistError
from .zipper import encode, decode
from arcade import TextureAnimationSprite

from .globals import g
from .logger import get_logger

logger = get_logger(__name__)


def _get_save_path():
    if os.name == "nt":  # Windows
        # Используем %APPDATA% (C:\Users\Имя\AppData\Roaming\Название_игры)
        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        save_dir = os.path.join(app_data, g.GAME_SAVES_FOLDER_NAME)
    else:
        # Linux/Mac
        save_dir = os.path.join(
            os.path.expanduser("~"), ".local", "share", g.GAME_SAVES_FOLDER_NAME
        )
    os.makedirs(save_dir, exist_ok=True)
    return save_dir

class Saves_manager:
    def __init__(self):
        """
        Отвечает за работу с сохранением различных данных.
        """
        save_folder = _get_save_path()
        if not os.path.exists(os.path.join(save_folder, g.DEFAULT_DATA_FILE_NAME)):
            logger.warning("Создаём файл сохранений!")
            self._create_save()
        else:
            with open(
                os.path.join(save_folder, g.DEFAULT_DATA_FILE_NAME),
                "r",
                encoding="UTF-8",
            ) as file:
                file = json.load(file)

            if ("saves_version" not in file) or (
                file["saves_version"] != g.TOPICAL_SAVES_VERSION
            ):
                logger.warning(
                    "НЕВЕРНАЯ ВЕРСИЯ ФАЙЛА СОХРАНЕНИЙ! Пересоздаём файл сохранений!"
                )
                self._create_save()
            else:
                logger.info("С файлом сохранений всё впорядке!")

        self.Persistent = self.Persistent()
        self.Volume = self.Volume()
        self.Save = self.Save()

    def _create_save(self):
        save_folder = _get_save_path()
        with open(
            os.path.join(save_folder, g.DEFAULT_DATA_FILE_NAME), "w", encoding="UTF-8"
        ) as file:
            data = {
                "saves_version": g.TOPICAL_SAVES_VERSION,
                "saves": encode({}),
                "persistent": {},
                "options": g.DEFAULT_OPTIONS_PARAM,
            }
            json.dump(data, file, indent=4, ensure_ascii=False)

    class Persistent:
        """
        Отвечает за работу с Persistent-переменными.
        Они отличаются тем, что сохраняются для всей игры и не  привязываются к определённой точке
        """

        def __init__(self):
            save_folder = _get_save_path()
            with open(
                os.path.join(save_folder, g.DEFAULT_DATA_FILE_NAME),
                "r",
                encoding="UTF-8",
            ) as file:
                file = dict(json.load(file))
            self.file = file

        def _save_data(self) -> None:
            save_folder = _get_save_path()
            with open(
                os.path.join(save_folder, g.DEFAULT_DATA_FILE_NAME),
                "w",
                encoding="UTF-8",
            ) as file:
                json.dump(self.file, file)

        def _get_data(self):
            save_folder = _get_save_path()
            with open(
                os.path.join(save_folder, g.DEFAULT_DATA_FILE_NAME),
                "r",
                encoding="UTF-8",
            ) as file:
                file = dict(json.load(file))
            self.file = file

        def get_persistent(self, name: str) -> any:
            """
            Возвращает значение persistent
            :param name: Название переменной
            """
            self._get_data()
            if name not in self.file["persistent"]:
                raise AttributeError(f'Persistent "{name}" does not exist!')

            return self.file["persistent"].get(name, None)

        def get_all_persistents(self) -> dict[str:any]:
            """
            Возвращает все persistent переменные, что есть
            :return: Словарь переменных со значениями {Название переменной : Значение}
            """
            self._get_data()
            params = {name: value for name, value in self.file["persistent"].items()}
            return params

        def set_persistent(self, name: str, data: any) -> None:
            """
            Устанавливает переменной значение
            :param name: Название переменной
            :param data: Данные переменной
            """
            self._get_data()
            self.file["persistent"][name] = data
            self._save_data()

        def del_persistent(self, name: str) -> None:
            """
            Удаляет переменную
            :param name: Название переменной
            """
            self._get_data()
            if name not in self.file["persistent"]:
                raise AttributeError(f'Persistent "{name}" does not exist!')

            del self.file["persistent"][name]

    class Volume:
        """
        Отвечает за работу с различными параметрами и ползунками из файлов сохранения
        """

        def __init__(self):
            save_folder = _get_save_path()
            with open(
                os.path.join(save_folder, g.DEFAULT_DATA_FILE_NAME),
                "r",
                encoding="UTF-8",
            ) as file:
                file = dict(json.load(file))

            super().__setattr__("file", file)

        def __getattr__(self, name):
            self._update_data()

            file = super().__getattribute__("file")

            if name in file["options"]["volume"]:
                return file["options"]["volume"][name]
            elif name in file["options"]:
                return file["options"][name]

            return None

        def __setattr__(self, key, value):
            file = super().__getattribute__("file")

            if key in file["options"]["volume"]:
                file["options"]["volume"][key] = value
            else:
                file["options"][key] = value

            self._save_data()

        def __delattr__(self, item):
            file = super().__getattribute__("file")

            if item in file["options"]["volume"]:
                del file["options"]["volume"][item]
            else:
                del file["options"][item]

            self._save_data()

        def _save_data(self) -> None:

            file = super().__getattribute__("file")

            save_folder = _get_save_path()
            with open(
                os.path.join(save_folder, g.DEFAULT_DATA_FILE_NAME),
                "w",
                encoding="UTF-8",
            ) as data_file:
                json.dump(file, data_file)

        def _update_data(self):
            save_folder = _get_save_path()
            with open(
                os.path.join(save_folder, g.DEFAULT_DATA_FILE_NAME),
                "r",
                encoding="UTF-8",
            ) as data_file:
                data_file = dict(json.load(data_file))
            super().__setattr__("file", data_file)

    class Save:
        """
        Отвечает за работу с сохранениями игры
        """

        def __init__(self):
            save_folder = _get_save_path()
            with open(
                os.path.join(save_folder, g.DEFAULT_DATA_FILE_NAME),
                "r",
                encoding="UTF-8",
            ) as file:
                file = dict(json.load(file))
            self.file = file

        def _save_data(self):
            save_folder = _get_save_path()
            with open(
                os.path.join(save_folder, g.DEFAULT_DATA_FILE_NAME),
                "w",
                encoding="UTF-8",
            ) as file:
                json.dump(self.file, file)

        def _get_data(self):
            save_folder = _get_save_path()
            with open(
                os.path.join(save_folder, g.DEFAULT_DATA_FILE_NAME),
                "r",
                encoding="UTF-8",
            ) as file:
                file = dict(json.load(file))
            self.file = file

        def _set_saves(self, saves: dict):
            if g.SHOULD_ZIP_SAVES_DATA:
                saves = encode(saves)
            self.file["saves"] = saves
            self._save_data()

        def _get_saves(self) -> dict:
            self._get_data()
            saves = self.file.get("saves")

            if saves is None:
                saves = {}
                self.file["saves"] = saves

            if g.SHOULD_ZIP_SAVES_DATA is not None: # Если установлены принудительные параметры
                if g.SHOULD_ZIP_SAVES_DATA and isinstance(saves, dict):
                    logger.error("Файл сохранения не заархивирован, архивируем...")
                    self._set_saves(saves)
                    return decode(encode(saves))

                if not g.SHOULD_ZIP_SAVES_DATA and isinstance(saves, str):
                    logger.error("Файл сохранения был заархивирован, разархивируем...")
                    decoded = decode(saves)
                    self._set_saves(decoded)
                    return decoded

                if g.SHOULD_ZIP_SAVES_DATA and isinstance(saves, str):
                    return decode(saves)

                if not g.SHOULD_ZIP_SAVES_DATA and isinstance(saves, dict):
                    return saves
            else: # Сжимаем автоматически
                if isinstance(saves, dict):
                    json_str = json.dumps(saves, ensure_ascii=True).encode('utf-8')
                    if len(json_str) > g.MAX_SAVESFILE_SIZE_LIMIT:
                        logger.log(f"Файл сохранений стал весить больше {g.MAX_SAVESFILE_SIZE_LIMIT} байт! Применяем сжатие")
                        self._set_saves(encode(saves))
                    return saves
                else:
                    saves = decode(saves)
                    json_str = json.dumps(saves, ensure_ascii=True).encode('utf-8')
                    if len(json_str) < g.MAX_SAVESFILE_SIZE_LIMIT:
                        logger.log(f"Файл сохранений стал весить меньше {g.MAX_SAVESFILE_SIZE_LIMIT} байт! Сжатие не будет использовано")
                        self._set_saves(saves)
                    return saves


        def create_save(self) -> None:
            """
            Создаёт сохранение
            """
            if g.am.music.is_playing():
                music_file = g.am.music.now_playing_path
                music_volume = g.am.music._local_modifier
            else:
                music_file = None
                music_volume = 1.0

            sprites = [
                {
                    "id": str(i),
                    "path": str(o.texture.file_path),
                    "size": o.size,
                    "pos": o.position,
                }
                for i, o in g.scene["sprites"].items()
            ]

            animated_sprites = [
                {
                    "id": str(str(pathlib.Path(i).name)),
                    "path": str(o.texture.file_path),
                    "size": o.size,
                    "pos": o.position,
                }
                for i, o in g.scene["animated_sprites"].items()
            ]

            defines = {}
            for name, value in g.main.NAMESPACE["Define"].get_all_variables().items():
                if not name.startswith("__") and not name.endswith("__"):
                    defines[name] = copy.deepcopy(value)

            bg = [
                {
                    "layer": 0,
                    "path": str(i.texture.file_path),
                    "size": i.size,
                    "pos": i.position,
                }
                for i in g.scene["bg"].values()
            ]

            bg_parallax = [
                {
                    "path": i["sprite"].texture.file_path.name,
                    "speed": i["speed"],
                    "original_x": i["original_x"],
                    "original_y": i["original_y"],
                    "scale": i["scale"],
                }
                for i in g.scene["bg_parallax"]
            ]

            files_manager = {
                "loaded_lables": copy.copy(g.fm.loaded_labels),
                "loaded_textures": {
                    filename: str(texture[1])
                    for filename, texture in g.fm.textures.items()
                    if type(texture) is not TextureAnimationSprite
                },
                "loaded_audios": {
                    filename: str(sound.file_name)
                    for filename, sound in g.fm.audios.items()
                },
            }
            for filename, sprite in g.fm.textures.items():
                if type(sprite) is TextureAnimationSprite:
                    files_manager["loaded_textures"][filename] = str(
                        sprite.texture.file_path.absolute()
                    )

            scene = {
                "bg": bg,
                "bg_parallax": bg_parallax,
                "sprites": sprites,
                "animated_sprites": animated_sprites,
                "music": {"volume": music_volume, "path": music_file},
                "characters_slice": g.scene.characters_slice,
            }

            saves = self._get_saves()

            saves[g.main.session_id] = {
                "position": g.lm.pose - 1,
                "label": g.lm.label,
                "defines": defines,
                "scene": scene,
                "files_manager": files_manager,
                "session_data": g.main.session_data,
            }

            self._set_saves(saves)

            self._save_data()

        def get_save(self, session_id: str) -> dict:
            """
            Возвращает сохранение по его айди
            :param session_id: Айди сохранения
            :raises SaveDoesNotExistError: Если сохранение не  существует
            """

            saves = self._get_saves()

            if session_id not in saves:
                raise SaveDoesNotExistError(f'Save "{session_id}" does not exist!')

            return saves[session_id]

        def get_all_saves(self) -> list:
            """
            Возвращает все игровые сохранения
            """
            saves = self._get_saves()

            return [[i, o] for i, o in saves.items()]

        def del_save(self, session_id):

            saves = self._get_saves()
            del saves[session_id]
            self._set_saves(saves)
