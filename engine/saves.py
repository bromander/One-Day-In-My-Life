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

        self.defines = {}

    class persistent:

        @staticmethod
        def get_persistent(name: str):
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))

            if name not in file["persistent"]:
                raise PersistentDoesNotExistError(f"Persistent \"{name}\" does not exist!")

            return file["persistent"].get(name, None)

        @staticmethod
        def set_persistent(name: str, data: any):
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["persistent"][name] = data
            with open("game/saves.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

        @staticmethod
        def del_persistent(name: str):
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()

            if name not in file_data["persistent"]:
                raise PersistentDoesNotExistError(f"Persistent \"{name}\" does not exist!")

            del file_data["persistent"][name]

            with open("game/saves.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

    class volume:
        @staticmethod
        def set_music(value: float):
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["options"]["volume"]["music"] = value
            with open("game/saves.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

        @staticmethod
        def set_sound(value: float):
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["options"]["volume"]["sound"] = value
            with open("game/saves.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

        @staticmethod
        def set_voice(value: float):
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["options"]["volume"]["voice"] = value
            with open("game/saves.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

        @staticmethod
        def set_other(name: str, value: float):
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()

            if name not in file_data["options"]:
                raise VolumeDoesNotExistError(f"Volume \"{name}\" does not exist!")

            file_data["options"][name] = value

            with open("game/saves.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)


        @staticmethod
        def get_music():
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            return file["options"]["volume"].get("music", None)

        @staticmethod
        def get_sound():
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            return file["options"]["volume"].get("sound", None)

        @staticmethod
        def get_voice():
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            return file["options"]["volume"].get("voice", None)

        @staticmethod
        def get_other(name: str):
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))

            if name not in file["options"]:
                raise VolumeDoesNotExistError(f"Volume \"{name}\" does not exist!")

            return file["options"].get(name, None)

    class save:

        @staticmethod
        def create_save(session_id, am, scene, NAMESPACE, wwl):
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
            Saves_manager().save._add_save(session_id,
                                           defines=NAMESPACE["Define"].defines,
                                           position=wwl.pose - 1,
                                           label=wwl.label, scene=scene)

        @staticmethod
        def _add_save(session_id: str, defines: dict, position: int, label: str, scene: dict):
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["saves"][session_id] = {
                "position" : position,
                "label" : label,
                "defines" : defines,
                "scene" : scene
            }
            with open("game/saves.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

        @staticmethod
        def get_save(session_id: str) -> dict:
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file_data = dict(json.load(file))

            if session_id not in file_data["saves"]:
                raise SaveDoesNotExistError(f"Save \"{session_id}\" does not exist!")

            return file_data["saves"][session_id]

        @staticmethod
        def get_all_saves() -> dict:
            with open("game/saves.JSON", "r", encoding="UTF-8") as file:
                file_data = dict(json.load(file))
            return [[i, o] for i, o in file_data["saves"].items()]