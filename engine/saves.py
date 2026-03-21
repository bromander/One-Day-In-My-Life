import  json, os
from .Exceptions import PersistentDoesNotExistError, VolumeDoesNotExistError, SaveDoesNotExistError

class Saves_manager:
    def  __init__(self):
        """
        Отвечает за работу с сохранением различных данных.
        """

        if not os.path.exists("game/saves.JSON"):
            with open("game/saves.JSON", "w", encoding="UTF-8") as file:
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

    class Persistent:
        """
        Отвечает за работу с Persistent-переменными.
        Они отличаются тем, что сохраняются для всей игры и не  привязываются к определённой точке
        """
        def  __init__(self):
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            self.file = file

        def get_persistent(self, name: str) -> any:
            """
            Возвращает значение persistent
            :param name: Название переменной
            """
            if name not in self.file["persistent"]:
                raise PersistentDoesNotExistError(f"Persistent \"{name}\" does not exist!")

            return self.file["persistent"].get(name, None)

        def set_persistent(self, name: str, data: any) -> None:
            """
            Устанавливает переменной значение
            :param name: Название переменной
            :param data: Данные переменной
            """
            self.file["persistent"][name] = data

        def del_persistent(self, name: str) -> None:
            """
            Удаляет переменную
            :param name: Название переменной
            :raises PersistentDoesNotExistError: Если переменная не существует
            """
            if name not in self.file["persistent"]:
                raise PersistentDoesNotExistError(f"Persistent \"{name}\" does not exist!")

            del self.file["persistent"][name]

    class Volume:
        """
        Отвечает за работу с различными параметрами и ползунками из файлов сохранения
        """
        def  __init__(self):
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            self.file = file

        def _save_data(self) -> None:
            with open("game/saves.JSON", "w", encoding="UTF-8") as file:
                json.dump(self.file, file)

        def set_music(self, value: float) -> None:
            """
            Устанавливает значение параметру music
            :param value: Значение
            """
            self.file["options"]["volume"]["music"] = value

        def set_sound(self, value: float) -> None:
            """
            Устанавливает значение параметру sound
            :param value: Значение
            """
            self.file["options"]["volume"]["sound"] = value

        def set_voice(self, value: float) -> None:
            """
            Устанавливает значение параметру voice
            :param value: Значение
            """
            self.file["options"]["volume"]["voice"] = value

        def set_other(self, name: str, value: any) -> None:
            """
            Устанавливает значение
            :param name: Название значения
            :param value: Значение
            :raises VolumeDoesNotExistError: Если параметр не существует
            """
            if name not in self.file["options"]:
                raise VolumeDoesNotExistError(f"Volume \"{name}\" does not exist!")
            self.file["options"][name] = value


        def get_music(self) -> float:
            """
            Возвращает значение параметра music
            """
            return self.file["options"]["volume"].get("music", None)

        def get_sound(self) -> float:
            """
            Возвращает значение параметра music
            """
            return self.file["options"]["volume"].get("sound", None)

        def get_voice(self) -> float:
            """
            Возвращает значение параметра music
            """
            return self.file["options"]["volume"].get("voice", None)

        def get_other(self, name: str) -> any:
            """
            Возвращает значение параметра
            :param name: название параметра
            :raises VolumeDoesNotExistError: Если параметр не существует
            """
            if name not in self.file["options"]:
                raise VolumeDoesNotExistError(f"Volume \"{name}\" does not exist!")

            return self.file["options"].get(name, None)

    class Save:
        """
        Отвечает за работу с сохранениями игры
        """
        def  __init__(self):
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            self.file = file

        def _save_data(self):
            with open("game/saves.JSON", "w", encoding="UTF-8") as file:
                json.dump(self.file, file)


        def create_save(self, session_id, am, scene, NAMESPACE, wwl) -> None:
            """
            Создаёт текущее сохранение
            :param session_id: Айди сессии
            :param am: Класс AudioManager
            :param scene: Класс Scene
            :param NAMESPACE: Класс Namespace
            :param wwl: Класс WorkWithLore
            """
            try:
                music_file = am.music.sound.file_name
            except FileNotFoundError:
                music_file = None
            except AttributeError:
                music_file = None

            sprites = [
                {
                    "id": str(i),
                    "path": str(o.texture.file_path),
                    "size": o.size,
                    "pos": o.position
                }
                for i, o in scene["sprites"].items()
            ]

            bg = [
                {
                    "layer": 0,
                    "path": str(i.texture.file_path),
                    "size": i.size,
                    "pos": i.position
                }
                for i in scene["bg"].values()
            ]

            scene = {
                "bg": bg,
                "sprites": sprites,
                "music": music_file

            }
            self._add_save(session_id,
                           defines=NAMESPACE["Define"].defines,
                           position=wwl.pose - 1,
                           label=wwl.label,
                           scene=scene
                           )

        def _add_save(self, session_id: str, defines: dict, position: int, label: str, scene: dict) -> None:
            self.file["saves"][session_id] = {
                "position" : position,
                "label" : label,
                "defines" : defines,
                "scene" : scene
            }
            self._save_data()

        def get_save(self, session_id: str) -> dict:
            """
            Возвращает сохранение по его айди
            :param session_id: Айди сохранения
            :raises SaveDoesNotExistError: Если сохранение не  существует
            """

            if session_id not in self.file["saves"]:
                raise SaveDoesNotExistError(f"Save \"{session_id}\" does not exist!")

            return self.file["saves"][session_id]

        def get_all_saves(self) -> list:
            """
            Возвращает все игровые сохранения
            """
            return [[i, o] for i, o in self.file["saves"].items()]