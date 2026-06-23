import logging
import math
import os
from typing import BinaryIO

import pyglet
from pyglet.media import Source


if os.environ.get("ARCADE_SOUND_BACKENDS"):
    pyglet.options.audio = tuple(v.strip() for v in os.environ["ARCADE_SOUND_BACKENDS"].split(","))
else:
    pyglet.options.audio = ("openal", "xaudio2", "directsound", "pulse", "silent")

import pyglet.media as media

logger = logging.getLogger("arcade")

class Sound_modif:
    """
    Тот же самый arcade.Sound, но в который можно загрузить байты файла, а не путь к этому файлу
    """

    def __init__(self, file_bytes: BinaryIO, file_name, streaming: bool = False):
        self.file_name: str = ""

        self.file_name = str(file_name)

        self.source: Source = media.load(self.file_name, file_bytes,  streaming=streaming)
        file_bytes.close()
        """
        The :py:class:`pyglet.media.Source` object that holds the audio data.
        """

        if self.source.duration is None:
            raise ValueError(
                "Audio duration must be known when loaded, but this audio source returned `None`"
            )

        self.min_distance = (
            100000000  # setting the players to this allows for 2D panning with 3D audio
        )

    def play(
        self,
        volume: float = 1.0,
        pan: float = 0.0,
        loop: bool = False,
        speed: float = 1.0,
    ) -> media.Player:
        """Try to play this :py:class:`Sound` and return a |pyglet Player|.

        .. important:: A :py:class:`Sound` with ``streaming=True`` loses features!

                       Neither ``loop`` nor simultaneous playbacks will work. See
                       :py:class:`Sound` and :ref:`sound-loading-modes`.

        Args:
            volume: Volume (``0.0`` is silent, ``1.0`` is loudest).
            pan: Left / right channel balance (``-1`` is left,  ``0.0`` is
                center, and ``1.0`` is right).
            loop: ``True`` attempts to restart playback after finishing.
            speed: Change the speed (and pitch) of the sound. Default speed is
                ``1.0``.
        Returns:
            A |pyglet Player| for this playback.
        """
        if isinstance(self.source, media.StreamingSource) and self.source.is_player_source:
            raise RuntimeError(
                "Tried to play a streaming source more than once."
                " Streaming sources should only be played in one instance."
                " If you need more use a Static source."
            )

        player: media.Player = media.Player()
        player.volume = volume
        player.position = (
            pan,
            0.0,
            math.sqrt(1 - math.pow(pan, 2)),
        )  # used to mimic panning with 3D audio

        # Note that the underlying attribute is pitch but "speed" is used
        # because it describes the behavior better (see #1198)
        player.pitch = speed

        player.loop = loop
        player.queue(self.source)
        player.play()
        media.Source._players.append(player)

        def _on_player_eos():
            # Some race condition within Pyglet can cause the player to be removed
            # from this list before we get to it, so we try and catch the ValueError
            # raised by the removal if it's already been removed.
            try:
                media.Source._players.remove(player)
            except ValueError:
                pass
            # There is a closure on player. To get the refcount to 0,
            # we need to delete this function.
            player.on_player_eos = None  # type: ignore  # pending https://github.com/pyglet/pyglet/issues/845

        player.on_player_eos = _on_player_eos  # type: ignore
        return player

    def stop(self, player: media.Player) -> None:
        """Stop and :py:meth:`~pyglet.media.player.Player.delete` ``player``.

        All references to it in the internal table for
        :py:class:`pyglet.media.Source` will be deleted.

        Args:
            player: A pyglet |pyglet Player| from :func:`play_sound`
                or :py:meth:`Sound.play`.
        """
        player.pause()
        player.delete()
        if player in media.Source._players:
            media.Source._players.remove(player)

    def get_length(self) -> float:
        """Get length of the loaded audio in seconds"""
        # We validate that duration is known when loading the source
        return self.source.duration  # type: ignore

    def is_complete(self, player: media.Player) -> bool:
        """``True`` if the sound is done playing."""
        # We validate that duration is known when loading the source
        return player.time >= self.source.duration  # type: ignore

    def is_playing(self, player: media.Player) -> bool:
        """``True`` if ``player`` is currently playing, otherwise ``False``.

        Args:
            player: A |pyglet Player| from :func:`play_sound` or
                :py:meth:`Sound.play`.

        Returns:
            ``True`` if the passed pyglet player is playing.
        """
        return player.playing

    def get_volume(self, player: media.Player) -> float:
        """Get the current volume.

        Args:
            player: A |pyglet Player| from :func:`play_sound` or
                :py:meth:`Sound.play`.
        Returns:
            A volume between ``0.0`` (silent) and ``1.0`` (full volume).
        """
        return player.volume  # type: ignore  # pending https://github.com/pyglet/pyglet/issues/847

    def set_volume(self, volume: float, player: media.Player) -> None:
        """Set the volume of a sound as it is playing.

        Args:
            volume: Floating point volume. 0 is silent, 1 is full.
            player: A |pyglet Player| from :func:`play_sound` or
                :py:meth:`Sound.play`.
        """
        player.volume = volume

    def get_stream_position(self, player: media.Player) -> float:
        """Return where we are in the stream. This will reset back to
        zero when it is done playing.

        Args:
            player: A |pyglet Player| from :func:`play_sound` or
                 :py:meth:`Sound.play`.
        """
        return player.time