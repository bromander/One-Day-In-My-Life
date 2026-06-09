from typing import Literal, Optional
from .exceptions import ChannelDoesNotExistError


class Audio:
    def __init__(self, g) -> None:
        """
        Отвечает за работу с аудио
        """
        self.am = g.am
        self.actions = g.actions

    def play(
        self,
        channel: Literal["music", "sound"],
        file_name: str,
        volume: float = 1.0,
        loop: Optional[bool] = None,
        effect: Optional[Literal["fade"]] = None,
        stream: Literal[
            "consistently", "consistently_async", "together"
        ] = "consistently_async",
    ) -> None:
        """
        Запускает музыку
        :param channel: Канал ("music" / "sound")
        :param file_name: Название файла звука
        :param volume: Громкость
        :param loop: Если True, музыка будет играть циклично
        :param effect: Название эффекта
        :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится, consistently_async: Обновляет только первый генератор в списке, но игра не ждёт его окончания
        :raises ChannelDoesNotExistError: Если channel не существует
        """
        match channel:
            case "music":
                loop = True if loop is None else loop
                target = self.am.play_music_gen(file_name, loop, volume, effect)
                self.actions.active_generators.add_generator(
                    stream, target, "play_music"
                )
            case "sound":
                loop = False if loop is None else loop
                target = self.am.play_sound_gen(file_name, loop, volume, effect)
                self.actions.active_generators.add_generator(
                    stream, target, "play_sound"
                )
            case _:
                raise ChannelDoesNotExistError(f"Channel {channel} does not exist")

    def stop(
        self,
        channel: Literal["music", "sound"],
        effect: Optional[Literal["fade"]] = None,
        stream: Literal[
            "consistently", "consistently_async", "together"
        ] = "consistently_async",
    ) -> None:
        """
        Останавливает проигрывание канала
        :param channel: Канал ("music" / "sound")
        :param effect: Название эффекта
        :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится, consistently_async: Обновляет только первый генератор в списке, но игра не ждёт его окончания
        :raises ChannelDoesNotExistError: Если channel не существует
        """
        match channel:
            case "music":
                self.actions.active_generators.add_generator(
                    stream, self.am.stop_music_gen(effect), "stop_music"
                )
            case "sound":
                self.actions.active_generators.add_generator(
                    stream, self.am.stop_sound_gen(effect), "stop_sound"
                )
            case N:
                raise ChannelDoesNotExistError(f"Channel {N} does not exist")
