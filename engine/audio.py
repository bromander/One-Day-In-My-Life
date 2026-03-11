import types
from pathlib import Path
from typing import Optional, Literal, Tuple
import sys, os
from pathlib import Path
from arcade import load_sound, sound
import random
import pyglet.media.player
from .saves import Saves_manager as sm


class AudioChannel:
    def __init__(self, default_volume: float=1.0, modifier: float = 1.0, volume_type: Optional[str] = None):
        '''
        Отвечает за отдельный канал аудио
        :param default_volume: Громкость по умолчанию
        :param volume_type: Тип звука ("music"/"sound"/"voice")
        '''
        self.player: Optional[pyglet.media.player.Player] = None
        self.default_volume: float = default_volume # Громкость по умолчанию
        self.volume_type: Optional[str] = volume_type # Тип канала
        self.modifier = modifier # Модификатор громкости. Предназначен для управления громкости с ползунков из настроек
        self._fade_modifier: float = 1.0 # Модификатор громкости. Предназначен для управления громкости во время плавных переходов (FADEIN/FADEOUT)
        self._local_modifier: float = 1.0 # Модификатор громкости. Предназначен для управления громкости текущего трека. Сбрасывается при запуске нового трека


    @property
    def fade_modifier(self) -> float:
        return self._fade_modifier

    @fade_modifier.setter
    def fade_modifier(self, value) -> None:
        self._fade_modifier = value
        if self.player:
            self.player.volume = self.default_volume * self.modifier * self._fade_modifier * self._local_modifier
            # Обновляем громкость проигрывателя, если параметр self._fade_modifier был изменён

    def play(self, file: Tuple[str, sound.Sound], loop=False, speed=1.0, local_volume: Optional[float]=None) -> None:
        """
        Начинает проигрывать звук
        :param file: Путь к файлу/уже готовый саунд
        :param loop: Если True, звук будет зацикливаться
        :param speed: Скорость проигрывания
        """
        self.stop()

        if local_volume:
            self._local_modifier = local_volume

        if type(file) is str or type(file) is type(Path()):
            file_sound = load_sound(file)
        elif type(file) is sound.Sound:
            file_sound = file
        else:
            raise TypeError("Sound type is not the desired data type")

        volume = self.default_volume * self.modifier * self._fade_modifier * self._local_modifier

        self.player = file_sound.play(volume=volume, loop=loop, speed=speed)

    def stop(self) -> None:
        """
        Выключает проигрывание музыки
        """
        if self.player:
            self.player.delete()
        self._local_modifier = 1.0

    def pause(self) -> None:
        """
        Останавливает проигрывание музыки
        """
        if self.player:
            self.player.pause()

    def resume(self) -> None:
        """
        Продолжает проигрывание музыки, если та была остановлена
        """
        if self.player:
            self.player.play()

    def set_volume(self, vol, is_global: bool = True) -> None:
        """
        Изменяет громкость
        :param vol: Громкость
        :param is_global: Если True, применяет глобально, к этом и последующим звукам, а также, сохраняет значение. Если False, применяет громкость только к текущему звуку
        """

        if is_global:
            self.modifier = vol
            if self.player:
                self.player.volume = self.default_volume * self.modifier * self._fade_modifier * self._local_modifier

            # Сохраняем значения
            if self.volume_type == "music":
                sm.volume.set_music(self.modifier)
            elif self.volume_type == "sound":
                sm.volume.set_sound(self.modifier)
            elif self.volume_type == "voice":
                sm.volume.set_voice(self.modifier)
        else:
            self._local_modifier = vol
            if self.player:
                self.player.volume = self.default_volume * self.modifier * self._fade_modifier * self._local_modifier

    def is_playing(self) -> bool:
        if self.player:
            return self.player.playing
        else:
            return False

class AudioManager:
    def __init__(self):
        """
        Управляет 3 основными каналами: music, sound, voice
        """
        def find_files(extension: list, start_path):
            results = {}

            for i in extension:
                for root, dirs, files in os.walk(start_path):
                    if "voice" in root.split("\\"):
                        continue
                    for file in files:
                        if file.lower().endswith(i.lower()):
                            full_path = os.path.join(root, file)
                            results[file] = load_sound(full_path.replace("\\", "/"))
            return results

        self.sound_files = find_files([".mp3", ".wav", ".ogg"], f"./game/sounds")
        self.music_files = find_files([".mp3", ".wav", ".ogg"], f"./game/music")

        self.music = AudioChannel(modifier=sm.volume.get_music(), volume_type="music")
        self.sound = AudioChannel(modifier=sm.volume.get_sound(), volume_type="sound")
        self.voice = AudioChannel(modifier=sm.volume.get_voice(), volume_type="voice", default_volume=2.0)

    def play_music_gen(self, path: Tuple[str, Path], loop: bool = False, volume: float = 1.0, effect: Optional[str] = None):
        """
        Отличается от play_music тем, что поддерживает эффекты
        :return: генератор
        """
        path = Path(path)
        if path.name in self.music_files:
            path = self.music_files[path.name]
        elif path.name in self.sound_files:
            path = self.sound_files[path.name]

        match effect:
            case "FADE":
                def fadeout_music():
                    while self.music.fade_modifier < 1.0:
                        self.music.fade_modifier += 0.005
                        yield
                    self.music.fade_modifier = 1.0

                self.music.fade_modifier = 0.0
                self.music.play(path, loop=loop, local_volume=volume)
                return fadeout_music()

            case _:
                def music():
                    self.music.play(path, loop=loop, local_volume=volume)
                    yield
                return music()

    def play_music(self, path: Tuple[str, Path], loop: bool = False, volume: float = 1.0) -> None:
        path = Path(path)
        if path.name in self.music_files:
            path = self.music_files[path.name]
        elif path.name in self.sound_files:
            path = self.sound_files[path.name]

        self.music.play(path, loop=loop, local_volume=volume)

    def play_sound_gen(self, path: Tuple[str, Path], loop: bool = False, volume: float = 1.0, effect: Optional[Literal["fade"]] = None):
        """
        Отличается от play_sound тем, что поддерживает эффекты
        :return: генератор
        """
        path = Path(path)
        if path.name in self.music_files:
            path = self.music_files[path.name]
        elif path.name in self.sound_files:
            path = self.sound_files[path.name]


        match effect:
            case "fade":
                def fadeout_sound():
                    while self.sound.fade_modifier < 1.0:
                        self.sound.fade_modifier += 0.005
                        yield
                    self.sound.fade_modifier = 1.0

                self.sound.fade_modifier = 0.0
                self.sound.play(path, loop=loop, local_volume=volume)
                return fadeout_sound()

            case _:
                def sound():
                    self.sound.play(path, loop=loop, local_volume=volume)
                    yield
                return sound()

    def play_sound(self, path: Tuple[str, Path], loop: bool = False, volume: float = 1.0) -> None:
        path = Path(path)
        if path.name in self.music_files:
            path = self.music_files[path.name]
        elif path.name in self.sound_files:
            path = self.sound_files[path.name]

        self.sound.play(path, loop=loop, local_volume=volume)

    def play_voice(self, path: Tuple[str, sound.Sound], loop=False) -> None:
        self.voice.play(path, loop=loop, speed=random.randint(99, 101) / 100)

    def stop_music_gen(self, effect: Optional[Literal["fade"]] = None):
        """
        Отличается от stop_music тем, что поддерживает эффекты
        :return: Генератор
        """
        match effect:
            case "fade":
                def fadeout_music():
                    while 0.0 < self.music.fade_modifier:
                        self.music.fade_modifier -= 0.005
                        yield
                    self.music.fade_modifier = 0.0
                    self.music.stop()
                    self.music.fade_modifier = 1.0
                return fadeout_music()
            case _:
                def music():
                    self.music.stop()
                    yield
                return music()

    def stop_music(self) -> None:
        self.music.stop()

    def stop_sound_gen(self, effect: Optional[str] = None):
        """
         Отличается от stop_sound тем, что поддерживает эффекты
        :return: Генератор
        """
        match effect:
            case "FADE":
                def fadeout_sound():
                    while 0.0 < self.sound.fade_modifier:
                        self.sound.fade_modifier -= 0.005
                        yield
                    self.sound.fade_modifier = 0.0
                    self.sound.stop()
                    self.sound.fade_modifier = 1.0

                return fadeout_sound()

            case _:
                def sound():
                    self.sound.stop()
                    yield
                return sound()

    def stop_sound(self):
        self.sound.stop()

    def stop_voice(self):
        self.voice.stop()