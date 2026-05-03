from typing import Optional, Literal, Tuple, Union
from pathlib import Path
from arcade import load_sound, sound, Sound
import random

import pyglet.media.player
from .saves import Saves_manager
from .files_manager import FilesManager

from .globals import Globals as g


class AudioChannel:
    def __init__(self, sm: Saves_manager, default_volume: float=1.0, modifier: float = 1.0, volume_type: Optional[str] = None):
        '''
        Отвечает за отдельный канал аудио
        :param default_volume: Громкость по умолчанию
        :param volume_type: Тип звука ("music"/"sound"/"voice")
        '''
        self.player: Optional[pyglet.media.player.Player] = None
        self.default_volume: float = default_volume # Громкость по умолчанию
        self.volume_type: Optional[str] = volume_type # Тип канала
        self.now_playing_path:  Optional[str] = None
        self.modifier = modifier # Модификатор громкости. Предназначен для управления громкостью ползунками из настроек
        self._fade_modifier: float = 1.0 # Модификатор громкости. Предназначен для управления громкостью во время плавных переходов (FADEIN/FADEOUT)
        self._local_modifier: float = 1.0 # Модификатор громкости. Предназначен для управления громкостью текущего трека. Сбрасывается при запуске нового трека

        self.paused = False

        self.sm = sm


    @property
    def fade_modifier(self) -> float:
        return self._fade_modifier

    @fade_modifier.setter
    def fade_modifier(self, value) -> None:
        self._fade_modifier = value
        if hasattr(self, "player"):
            if self.player:
                self.player.volume = self.default_volume * self.modifier * self._fade_modifier * self._local_modifier
                # Обновляем громкость проигрывателя, если параметр self._fade_modifier был изменён

    def play(self, file: Union[str, sound.Sound], loop=False, speed=1.0, local_volume: Optional[float]=None, streaming: bool = False) -> None:
        """
        Начинает проигрывать звук
        :param file: Путь к файлу/уже готовый саунд
        :param loop: Если True, звук будет зацикливаться
        :param speed: Скорость проигрывания
        :param local_volume: Громкость звука только в этот раз
        :param streaming: Boolean for determining if we stream the sound or
            load it all into memory. Set to ``True`` for long sounds to
            save memory, ``False`` for short sounds to speed playback.
        """
        self.stop()

        if local_volume:
            self._local_modifier = local_volume
        else:
            self._local_modifier = 1

        if type(file) is str or type(file) is type(Path()):
            self.now_playing_path = str(file)
            file_sound = load_sound(str(file), streaming=streaming)
        elif type(file) is sound.Sound:
            file_sound = file
            self.now_playing_path = file.file_name
        else:
            raise TypeError("Sound type is not the desired data type")

        volume = self.default_volume * self.modifier * self._fade_modifier * self._local_modifier
        self.player = file_sound.play(volume=volume, loop=loop, speed=speed)
        self.paused = False

    def stop(self) -> None:
        """
        Выключает проигрывание музыки
        """
        if hasattr(self, "player"):
            if self.player:
                self.player.delete()
                del self.player
        self.paused = False
        self.now_playing_path = None

    def pause(self) -> None:
        """
        Останавливает проигрывание музыки
        """
        if hasattr(self, "player"):
            if self.player:
                self.player.pause()
                self.paused = True

    def resume(self) -> None:
        """
        Продолжает проигрывание музыки, если та была остановлена
        """
        if hasattr(self, "player"):
            if self.player:
                self.player.play()
        self.paused = False

    def set_volume(self, vol, is_global: bool = True) -> None:
        """
        Изменяет громкость
        :param vol: Громкость
        :param is_global: Если True, применяет глобально, к этом и последующим звукам, а также, сохраняет значение. Если False, применяет громкость только к текущему звуку
        """
        if hasattr(self, "player"):
            if is_global:
                self.modifier = vol
                if self.player:
                    self.player.volume = self.default_volume * self.modifier * self._fade_modifier * self._local_modifier

                # Сохраняем значения
                if self.volume_type == "music":
                    self.sm.Volume.set_music(self.modifier)
                elif self.volume_type == "sound":
                    self.sm.Volume.set_sound(self.modifier)
                elif self.volume_type == "voice":
                    self.sm.Volume.set_voice(self.modifier)
            else:
                self._local_modifier = vol
                if self.player:
                    self.player.volume = self.default_volume * self.modifier * self._fade_modifier * self._local_modifier

    def is_playing(self) -> bool:
        if hasattr(self, "player"):
            if self.player:
                return self.player.playing
        return False

class AudioManager:
    def __init__(self):
        """
        Управляет 3 основными каналами: music, sound, voice
        """
        self.fm: FilesManager = g.fm
        self.music = AudioChannel(g.sm, modifier=g.sm.Volume.get_music(), volume_type="music")
        self.sound = AudioChannel(g.sm, modifier=g.sm.Volume.get_sound(), volume_type="sound")
        self.voice = AudioChannel(g.sm, modifier=g.sm.Volume.get_voice(), volume_type="voice", default_volume=2.0)

    def play_music_gen(self, path: str, loop: bool = False, volume: float = 1.0, effect: Optional[str] = None, streaming: bool = True):
        """
        Отличается от play_music тем, что поддерживает эффекты
        :return: генератор
        """

        if path in self.fm.audios:
            path = self.fm.audios[path]

        match effect:
            case "FADE":
                def fadeout_music():
                    while self.music.fade_modifier < 1.0:
                        self.music.fade_modifier += 0.005
                        yield
                    self.music.fade_modifier = 1.0

                self.music.fade_modifier = 0.0
                self.music.play(path, loop=loop, local_volume=volume, streaming=streaming)
                return fadeout_music()

            case _:
                def music():
                    self.music.play(path, loop=loop, local_volume=volume, streaming=streaming)
                    yield
                return music()

    def play_music(self, path: str, loop: bool = False, volume: float = 1.0, streaming: bool = True) -> None:

        if path in self.fm.audios:
            path: sound.Sound = self.fm.audios[path]
        self.music.play(path, loop=loop, local_volume=volume, streaming=streaming)

    def play_sound_gen(self, path: str, loop: bool = False, volume: float = 1.0, effect: Optional[Literal["fade"]] = None):
        """
        Отличается от play_sound тем, что поддерживает эффекты
        :return: генератор
        """
        if path in self.fm.audios:
            path = self.fm.audios[path]

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

    def play_sound(self, path: str, loop: bool = False, volume: float = 1.0) -> None:

        if path in self.fm.audios:
            path = self.fm.audios[path]

        self.sound.play(path, loop=loop, local_volume=volume)

    def play_voice(self, path: Union[str, sound.Sound], loop=False) -> None:

        if path in self.fm.audios:
            path = self.fm.audios[path]

        self.voice.play(path, loop=loop, speed=random.randint(99, 101) / 100, streaming=False)

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
                    self.music.pause()
                    self.music.stop()
                    self.music.fade_modifier = 1.0
                return fadeout_music()
            case _:
                def music():
                    self.music.pause()
                    self.music.stop()
                    yield
                return music()

    def stop_music(self) -> None:
        self.music.pause()
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
                    self.sound.pause()
                    self.sound.stop()
                    self.sound.fade_modifier = 1.0

                return fadeout_sound()

            case _:
                def sound():
                    self.sound.pause()
                    self.sound.stop()
                    yield
                return sound()

    def stop_sound(self):
        self.sound.pause()
        self.sound.stop()

    def stop_voice(self):
        self.voice.stop()