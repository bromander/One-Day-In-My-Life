import  json, os

class Saves_manager:
    def  __init__(self):

        if not os.path.exists("game/data.JSON"):
            with open("game/data.JSON", "w", encoding="UTF-8") as file:
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
                        "fade_speed" : 0
                    }
                }
                json.dump(data, file, indent=4, ensure_ascii=False)

        self.defines = {}

    class persistent:
        @staticmethod
        def get_persistent(name: str):
            with open("game/data.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            return file["persistent"].get(name, None)

        @staticmethod
        def set_persistent(name: str, data: any):
            with open("game/data.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["persistent"][name] = data
            with open("game/data.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

    class volume:
        @staticmethod
        def set_music(value: float):
            with open("game/data.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["options"]["volume"]["music"] = value
            with open("game/data.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

        @staticmethod
        def set_sound(value: float):
            with open("game/data.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["options"]["volume"]["sound"] = value
            with open("game/data.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

        @staticmethod
        def set_voice(value: float):
            with open("game/data.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["options"]["volume"]["voice"] = value
            with open("game/data.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

        @staticmethod
        def set_other(name: str, value: float):
            with open("game/data.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["options"][name] = value
            with open("game/data.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)


        @staticmethod
        def get_music():
            with open("game/data.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            return file["options"]["volume"].get("music", None)

        @staticmethod
        def get_sound():
            with open("game/data.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            return file["options"]["volume"].get("sound", None)

        @staticmethod
        def get_voice():
            with open("game/data.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            return file["options"]["volume"].get("voice", None)

        @staticmethod
        def get_other(name: str):
            with open("game/data.JSON", "r", encoding="UTF-8") as file:
                file = dict(json.load(file))
            return file["options"].get(name, None)

    class save:

        @staticmethod
        def create_save(session_id: str, defines: dict, position: int, label: str, scene: dict):
            with open("game/data.JSON", "r", encoding="UTF-8") as file:
                file_data_old = dict(json.load(file))
            file_data = file_data_old.copy()
            file_data["saves"][session_id] = {
                "position" : position,
                "label" : label,
                "defines" : defines,
                "scene" : scene
            }
            with open("game/data.JSON", "w", encoding="UTF-8") as file:
                json.dump(file_data, file, indent=4, ensure_ascii=False)

        @staticmethod
        def get_save(session_id: str) -> dict:
            with open("game/data.JSON", "r", encoding="UTF-8") as file:
                file_data = dict(json.load(file))
            return file_data["saves"][session_id]

        @staticmethod
        def get_all_saves() -> dict:
            with open("game/data.JSON", "r", encoding="UTF-8") as file:
                file_data = dict(json.load(file))
            return [[i, o] for i, o in file_data["saves"].items()]