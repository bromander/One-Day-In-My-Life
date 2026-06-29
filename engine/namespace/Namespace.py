from typing import Literal
import time

from .namespace_classmethod import *

class Namespace:
    def __init__(self, g) -> None:
        """
        Отвечает за работу со всеми функциями, используемыми в сценариях.
        """

        self.g = g
        self.Game_view = g.main
        self.ListCharacters = g.ListCharacters
        self.AudioManager = g.am
        self.SavesManager = g.sm

        self.NAMESPACE = {
            "Data": Data(self, g),
            "Persistent": Persistent(g),
            "Define": Define(),
            "Scene": Scene(g),
            "Screen": Screen(g),
            "Audio": Audio(g),
            "Lore": Lore(g),
            "SpriteEffects": SpriteEffects(g),
            "wait": self.wait,
            "talk": self.talk,
            "end": self.end,
        }
        self.returning = None

    def __getitem__(self, item):
        return self.NAMESPACE[item]

    def execute(self, command: str) -> str:
        """
        Выполняет код в своём окружении
        :param command: Строка с кодом
        """
        try:
            exec(command, self.NAMESPACE)
        except SyntaxError as e:
            raise SyntaxError(
                f"{e}:\n{'\n    '.join([str(num) + ' ' + str(i) for num, i in enumerate(str(command).split('\n'))])}"
            )

        old_ret = self.returning
        self.returning = None
        return old_ret

    def get(self, key: str, default: any = None) -> any:
        return self.NAMESPACE.get(key, default)

    def wait(
        self,
        duration: float,
        stream: Literal[
            "consistently", "consistently_async", "together"
        ] = "consistently",
    ):
        """
        Заставляет игру... Ждать
        """

        def _wait(duration):
            start_time = time.time()

            while time.time() - start_time < duration:
                yield

        self.g.actions.active_generators.add_generator(stream, _wait(duration), "wait")

    def end(self):
        self.g.lm.jump(self.g.DEFAULT_START_LABEL, 0)
        self.g.main.chanel()

    def talk(self, character: str, text: str):

        gen = self.g.ListCharacters[character].talk(text)

        self.g.actions.active_generators.add_generator("consistently", gen, "talk")
        self.returning = "END_text"
