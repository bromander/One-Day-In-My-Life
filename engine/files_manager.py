from pathlib import Path
import os
from typing import Union, Optional, Dict, Literal
from threading import Thread
from arcade import load_sound, load_texture, Texture, Sound

class FilesManager:
    def __init__(self, paths: Optional[dict]=None):

        if paths is None:
            paths = {"images": "./game/images", "music": "./game/music", "sounds": "./game/sounds"}

        def find_files(extensions: list[str],
                       start_path: Union[str, Path],
                       exclude: Optional[list[str]] = None) -> dict:

            if exclude is None:
                exclude = []

            extensions_lower = [ext.lower() for ext in extensions]
            results = {}

            start_path = Path(start_path).resolve()
            if not start_path.exists():
                return results

            for root, dirs, files in os.walk(str(start_path)):
                root_parts = Path(root).parts
                if any(part in exclude for part in root_parts):
                    continue

                for file in files:
                    if any(file.lower().endswith(ext) for ext in extensions_lower):
                        file_path = Path(root) / file
                        results[str(file_path.name)] = file_path.absolute()

            return results


        self.images_path = Path(paths["images"]).absolute()
        self.music_path = Path(paths["music"]).absolute()
        self.sounds_path = Path(paths["sounds"]).absolute()

        self.image_extensions = [".png", ".jpg", ".jpeg", ".PNG", ".JPEG"]
        self.audio_extensions = [".mp3", ".wav", ".ogg"]

        self.textures_paths: dict[str : Path] = find_files(self.image_extensions, self.images_path, ["gui"])
        self.audio_paths: dict[str : Path] = find_files(self.audio_extensions, self.music_path, ["voice"]) | find_files(self.audio_extensions, self.sounds_path, ["voice"])

        self.loaded_labels: list[str] = []

        self.textures: dict[str : Texture] = {}
        self.audios: dict[str : Sound] = {}

    def load_assets(self, filenames: list[str], label: str) -> Optional[Thread]:

        if label in self.loaded_labels:
            return None

        self.loaded_labels.append(label)

        def load(filenames):
            for i in filenames:
                if i in self.textures_paths:
                    if i in self.textures:
                        continue
                    self.textures[i] = load_texture(str(self.textures_paths[i]))
                elif i in self.audio_paths:
                    if i in self.audios:
                        continue
                    self.audios[i] = load_sound(str(self.audio_paths[i]))

        target = Thread(target=load, args=(filenames,))
        target.start()
        return target

    def get_character_textures(self, char_id: str):
        textures = {}
        for i in self.textures:
            if str(i).startswith(char_id):
                textures[i] = self.textures[i]
