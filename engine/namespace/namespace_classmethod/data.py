import datetime
import time
from typing import Optional


class Data:
    """
    Предоставляет доступ к основным классам движка
    """

    def __init__(self, namespace, g):
        self.session_id = g.main.session_id
        self.height = g.main.height
        self.width = g.main.width
        self.Window = g.main.window
        self.namespace = namespace
        self.Game_view = g.main
        self.ListCharacters = g.ListCharacters
        self.lm = g.lm
        self.AudioManager = g.am
        self.g = g

        self.mix = {
            "Сладкие блинчики": (
                frozenset(["milk.png", "eggs.png", "puki.png", "pineapple.png"]),
                "cooking_bliny",
            ),  # молоко+яйца+мука+ананас
            "Омлет": (
                frozenset(["milk.png", "eggs.png"]),
                "cooking_omlet",
            ),  # Молоко и яица
            "Салат": (frozenset(["tomatoes.png"]), "cooking_salad"),  # Помедорчеки
            # "Пирог" : (frozenset(["milk.png", "eggs.png", "puki.png"]), "blinyyy") # Яица, молоко  и пуки
        }

    def clear_gens(self):
        for i in range(1000):
            self.g.actions.update(1)
        self.g.actions.active_generators.clear()

    def format_time_seconds(self):
        seconds = time.time()

        dt = datetime.datetime.fromtimestamp(seconds)

        days = {
            0: "понедельник",
            1: "вторник",
            2: "среда",
            3: "четверг",
            4: "пятница",
            5: "суббота",
            6: "воскресенье",
        }

        months = {
            1: "января",
            2: "февраля",
            3: "марта",
            4: "апреля",
            5: "мая",
            6: "июня",
            7: "июля",
            8: "августа",
            9: "сентября",
            10: "октября",
            11: "ноября",
            12: "декабря",
        }

        weekday = days[dt.weekday()]
        day = dt.day
        month = months[dt.month]

        return weekday, day, month

    def create_stamp(self):
        def stamp():
            yield

        self.Game_view.actions.active_generators.add_generator(
            "continuous", stamp(), "stamp"
        )

    def trig_dialogue_window(self, state: Optional[bool]):
        if state:
            self.Game_view.show_dialogue_bg_trigger = state
        else:
            self.Game_view.show_dialogue_bg_trigger = (
                not self.Game_view.show_dialogue_bg_trigger
            )

    def get_food_root(self) -> list[tuple]:
        chosen = [i for i in self.namespace["Define"].collected_items.keys()]
        available = []
        for name, fset in self.mix.items():
            if set(fset[0]).issubset(set(chosen)):
                available.append((name, fset[1]))
        return available
