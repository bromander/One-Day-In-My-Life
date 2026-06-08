import uuid
from typing import Optional, Literal, List
import types


class ListActiveGenerators:
    def __init__(self):
        """
        Отвечает за управление всеми генераторами
        """
        self.active_generators_consistently: List[tuple[str, types.GeneratorType]] = []
        self.active_generators_consistently_async: List[
            tuple[str, types.GeneratorType]
        ] = []
        self.active_generators_together: List[tuple[str, types.GeneratorType]] = []
        self.dt_accumulator = 0.0
        self._talk_description = "talk"  # Константа для описания

    def _process_dt(self, raw_dt: float) -> Optional[float]:
        if raw_dt is None or raw_dt <= 0:
            return None

        self.dt_accumulator += raw_dt
        if self.dt_accumulator < 0.001:
            return None

        effective_dt = self.dt_accumulator
        self.dt_accumulator = 0.0
        return min(effective_dt, 0.1)

    def _remove_talk_generators(self):
        self.active_generators_consistently = [
            item
            for item in self.active_generators_consistently
            if item[0] != self._talk_description
        ]

    def add_generator(
        self,
        stream: Literal["together", "consistently", "consistently_async"],
        gen: types.GeneratorType,
        descr: str,
    ) -> None:
        """
        Добавляет генератор
        :param stream: Метод обновления. Together: Обновление всех генераторов разом, Consistently: Обновляет только первый генератор в списке, пока он не завершится, consistently_async: Обновляет только первый генератор в списке, но игра не ждёт его окончания
        :param gen: Объект-генератор
        :param descr: Название генератора
        """
        if descr == self._talk_description:
            self._remove_talk_generators()

        match stream:
            case "consistently":
                target_list = self.active_generators_consistently
            case "consistently_async":
                target_list = self.active_generators_consistently_async
            case _:
                target_list = self.active_generators_together

        descr = f"{descr}_{uuid.uuid4()}"

        target_list.append((descr, gen))

    def _process_generator(
        self, gen_tuple: tuple[str, types.GeneratorType], delta_time: float
    ) -> bool:

        _, generator = gen_tuple

        try:
            generator.send(delta_time)
        except StopIteration:
            return True
        except TypeError: # Если next() не вызывалось перед передачей генератора в функцию
            try:
                next(generator)
            except StopIteration:
                return True
        return False

    def _update_together(self, delta_time: float) -> None:
        if not self.active_generators_together:
            return

        remaining = []
        for gen_tuple in self.active_generators_together:
            if not self._process_generator(gen_tuple, delta_time):
                remaining.append(gen_tuple)

        self.active_generators_together = remaining

    def _update_consistently(self, delta_time: float) -> None:
        if not self.active_generators_consistently:
            return

        first_gen = self.active_generators_consistently[0]

        if self._process_generator(first_gen, delta_time):
            self.active_generators_consistently.pop(0)

    def _update_consistently_async(self, delta_time: float) -> None:
        if not self.active_generators_consistently_async:
            return

        first_gen = self.active_generators_consistently_async[0]

        if self._process_generator(first_gen, delta_time):
            self.active_generators_consistently_async.pop(0)

    def update(self, delta_time: float) -> None:
        """
        Обновляет генераторы
        :param delta_time: Промежуток между кадрами
        """
        processed_dt = self._process_dt(delta_time)
        if processed_dt is None:
            return

        self._update_together(processed_dt)
        self._update_consistently(processed_dt)
        self._update_consistently_async(processed_dt)

    def clear(self) -> None:
        """
        удаляет все добавленные генераторы
        :return:
        """
        self.dt_accumulator = 0.0
        self.active_generators_together.clear()
        self.active_generators_consistently.clear()
        self.active_generators_consistently_async.clear()
