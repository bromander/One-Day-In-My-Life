from typing import Literal

class Lore:
    def __init__(self, g) -> None:
        """
        Обеспечивает работу с перемещением по сюжету сценария
        """
        self.g = g

    def jump(self, label: str, position: int = 0) -> None:
        """
        Меняет текущий лейбл
        :param label: Название лейбла
        :param position: На какой строке сценария
        """
        self.g.lm.jump(label, position)

    def set_part(
            self,
            name: str,
            description: str,
            show_splash: bool = False,
            speed: float = 1.0,
            stream: Literal[
                "consistently", "consistently_async", "together"
            ] = "together",
    ) -> None:
        """
        Позволяет указать то, в какой точке сюжета находится игрок.
        Ещё, позволяет запустить сплеш.
        По умолчанию, всегда вызывается в начале каждого лейбла
        :param name: Название текущей главы/части игры
        :param description: Описание
        :param show_splash: Если True, то при переключении на лейбл будет показан сплеш
        :param speed: Скорость появления сплеша и его пропадания (пропадает со скоростью в два раза меньше speed)
        :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится, consistently_async: Обновляет только первый генератор в списке, но игра не ждёт его окончания
        """

        self.g.main.session_data["description"] = description
        self.g.main.session_data["name"] = name
        self.g.da.update(name, description)

        if show_splash:
            self.g.actions.start_action(
                "show_splash",
                {"name": name, "description": description, "duration": speed},
                stream,
            )