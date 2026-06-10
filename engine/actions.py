from .list_generator import ListActiveGenerators


class Actions:
    def __init__(self) -> None:
        """
        Хранит в себе некоторые функции-генераторы.
        Отвечает за обновление всех генераторов
        """
        self.active_generators = ListActiveGenerators()

    def update(self, delta_time: float) -> None:
        self.active_generators.update(delta_time)
