import copy
import sys
import  json, os
from .Exceptions import PersistentDoesNotExistError, VolumeDoesNotExistError, SaveDoesNotExistError
from .files_manager import FilesManager
from arcade import Sprite, TextureAnimationSprite

class Saves_manager:
    def  __init__(self):
        """
        Отвечает за работу с сохранением различных данных.
        """
        save_folder = self.get_save_path()
        if not os.path.exists(os.path.join(save_folder, 'saves.JSON')):
            with open(os.path.join(save_folder, 'saves.JSON'), "w", encoding="UTF-8") as file:
                data = {
                    "saves": {},
                    "persistent" : {},
                    "options": {
                        "volume": {
                            "music": 1.0,
                            "sound": 1.0,
                            "voice": 1.0
                        },
                        "lps" : 60,
                        "fade_speed" : 0,
                        "show_fps" : False
                    }
                }
                json.dump(data, file, indent=4, ensure_ascii=False)

        self.Persistent = self.Persistent()
        self.Volume = self.Volume()
        self.Save = self.Save()

    @staticmethod
    def get_save_path():
        if os.name == 'nt':  # Windows
            # Используем %APPDATA% (C:\Users\Имя\AppData\Roaming\Название_игры)
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
            save_dir = os.path.join(app_data, 'OneDay')
        else:
            # Linux/Mac
            save_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'OneDay')

        os.makedirs(save_dir, exist_ok=True)
        return save_dir

    class Persistent:
        """
        Отвечает за работу с Persistent-переменными.
        Они отличаются тем, что сохраняются для всей игры и не  привязываются к определённой точке
        """
        def  __init__(self):
            save_folder = Saves_manager.get_save_path()
            with open(os.path.join(save_folder, 'saves.JSON'), "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            self.file = file

        def _save_data(self) -> None:
            save_folder = Saves_manager.get_save_path()
            with open(os.path.join(save_folder, 'saves.JSON'), "w", encoding="UTF-8") as file:
                json.dump(self.file, file)

        def _get_data(self):
            save_folder = Saves_manager.get_save_path()
            with open(os.path.join(save_folder, 'saves.JSON'), "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            self.file = file

        def get_persistent(self, name: str) -> any:
            """
            Возвращает значение persistent
            :param name: Название переменной
            """
            self._get_data()
            if name not in self.file["persistent"]:
                raise AttributeError(f"Persistent \"{name}\" does not exist!")

            return self.file["persistent"].get(name, None)

        def set_persistent(self, name: str, data: any) -> None:
            """
            Устанавливает переменной значение
            :param name: Название переменной
            :param data: Данные переменной
            """
            self._get_data()
            self.file["persistent"][name] = data
            print(name, data)
            self._save_data()

        def del_persistent(self, name: str) -> None:
            """
            Удаляет переменную
            :param name: Название переменной
            """
            self._get_data()
            if name not in self.file["persistent"]:
                raise AttributeError(f"Persistent \"{name}\" does not exist!")

            del self.file["persistent"][name]

    class Volume:
        """
        Отвечает за работу с различными параметрами и ползунками из файлов сохранения
        """
        def  __init__(self):
            save_folder = Saves_manager.get_save_path()
            with open(os.path.join(save_folder, 'saves.JSON'), "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            self.file = file

        def _save_data(self) -> None:
            save_folder = Saves_manager.get_save_path()
            with open(os.path.join(save_folder, 'saves.JSON'), "w", encoding="UTF-8") as file:
                json.dump(self.file, file)

        def _get_data(self):
            save_folder = Saves_manager.get_save_path()
            with open(os.path.join(save_folder, 'saves.JSON'), "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            self.file = file

        def set_music(self, value: float) -> None:
            """
            Устанавливает значение параметру music
            :param value: Значение
            """
            self._get_data()
            self.file["options"]["volume"]["music"] = value

        def set_sound(self, value: float) -> None:
            """
            Устанавливает значение параметру sound
            :param value: Значение
            """
            self._get_data()
            self.file["options"]["volume"]["sound"] = value

        def set_voice(self, value: float) -> None:
            """
            Устанавливает значение параметру voice
            :param value: Значение
            """
            self._get_data()
            self.file["options"]["volume"]["voice"] = value

        def set_other(self, name: str, value: any) -> None:
            """
            Устанавливает значение
            :param name: Название значения
            :param value: Значение
            :raises VolumeDoesNotExistError: Если параметр не существует
            """
            self._get_data()
            if name not in self.file["options"]:
                raise VolumeDoesNotExistError(f"Volume \"{name}\" does not exist!")
            self.file["options"][name] = value


        def get_music(self) -> float:
            """
            Возвращает значение параметра music
            """
            self._get_data()
            return self.file["options"]["volume"].get("music", None)

        def get_sound(self) -> float:
            """
            Возвращает значение параметра music
            """
            self._get_data()
            return self.file["options"]["volume"].get("sound", None)

        def get_voice(self) -> float:
            """
            Возвращает значение параметра music
            """
            self._get_data()
            return self.file["options"]["volume"].get("voice", None)

        def get_other(self, name: str) -> any:
            """
            Возвращает значение параметра
            :param name: название параметра
            :raises VolumeDoesNotExistError: Если параметр не существует
            """
            self._get_data()
            if name not in self.file["options"]:
                raise VolumeDoesNotExistError(f"Volume \"{name}\" does not exist!")

            return self.file["options"].get(name, None)

    class Save:
        """
        Отвечает за работу с сохранениями игры
        """
        def  __init__(self):
            save_folder = Saves_manager.get_save_path()
            with open(os.path.join(save_folder, 'saves.JSON'), "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            self.file = file

        def _save_data(self):
            save_folder = Saves_manager.get_save_path()
            with open(os.path.join(save_folder, 'saves.JSON'), "w", encoding="UTF-8") as file:
                json.dump(self.file, file)

        def _get_data(self):
            save_folder = Saves_manager.get_save_path()
            with open(os.path.join(save_folder, 'saves.JSON'), "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            self.file = file


        def create_save(self, session_data: dict, session_id, am, scene, NAMESPACE, wwl, fm: FilesManager) -> None:
            """
            Создаёт текущее сохранение
            :param splash_data: Данные последнего сплеша
            :param session_id: Айди сессии
            :param am: Класс AudioManager
            :param scene: Класс Scene
            :param NAMESPACE: Класс Namespace
            :param wwl: Класс WorkWithLore
            """
            self._get_data()
            if am.music.is_playing():
                music_file = am.music.now_playing_path
                music_volume = am.music._local_modifier
            else:
                music_file =  None
                music_volume = 1.0


            sprites = [
                {
                    "id": str(i),
                    "path": str(o.texture.file_path),
                    "size": o.size,
                    "pos": o.position
                }
                for i, o in scene["sprites"].items()
            ]

            defines = {}
            for name, value in NAMESPACE.Define.__dict__.items():
                if not name.startswith("__") and not name.endswith("__"):
                    defines[name] = copy.deepcopy(value)


            bg = [
                {
                    "layer": 0,
                    "path": str(i.texture.file_path),
                    "size": i.size,
                    "pos": i.position
                }
                for i in scene["bg"].values()
            ]

            bg_parallax = [
                {
                    'path': i["sprite"].texture.file_path.name,
                    'speed': i["speed"],
                    'original_x': i["original_x"],
                    'original_y': i["original_y"],
                    "scale": i["scale"]
                }
                for i in scene["bg_parallax"]
            ]

            files_manager = {
                "loaded_lables" : copy.copy(fm.loaded_labels),
                "loaded_textures" : {
                    filename : str(texture[2]) for filename, texture in fm.textures.items() if type(texture) is not TextureAnimationSprite
                },
                "loaded_audios" : {
                    filename: str(sound.file_name) for filename, sound in fm.audios.items()
                }
            }
            for filename, texture in fm.textures.items():
                if type(texture) is TextureAnimationSprite:
                    paths = [str(i.texture.file_path) for i in texture.textures]
                    files_manager["loaded_textures"][filename] = paths


            scene = {
                "bg": bg,
                "bg_parallax" : bg_parallax,
                "sprites": sprites,
                "music": {"volume" : music_volume, "path" : music_file},
                "characters_slice": scene.characters_slice
            }

            self.file["saves"][session_id] = {
                "position": wwl.pose - 1,
                "label": wwl.label,
                "defines": defines,
                "scene": scene,
                "files_manager" : files_manager,
                "session_data" : session_data
            }
            self._save_data()

        def get_save(self, session_id: str) -> dict:
            """
            Возвращает сохранение по его айди
            :param session_id: Айди сохранения
            :raises SaveDoesNotExistError: Если сохранение не  существует
            """
            self._get_data()
            if session_id not in self.file["saves"]:
                raise SaveDoesNotExistError(f"Save \"{session_id}\" does not exist!")

            return self.file["saves"][session_id]

        def get_all_saves(self) -> list:
            """
            Возвращает все игровые сохранения
            """
            self._get_data()
            return [[i, o] for i, o in self.file["saves"].items()]

        def del_save(self, session_id):
            self._get_data()
            del self.file["saves"][session_id]
            self._save_data()