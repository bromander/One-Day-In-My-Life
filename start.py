import pyglet
pyglet.options['audio'] = ('openal', 'directsound', 'silent') # устанавливаем менее потокозависимые драйвера

import os
import arcade
import random
import json
import engine
from engine.main import Views
import warnings

from engine.globals import g

#python -m nuitka --standalone --include-data-dir=./game/=game --windows-console-mode=attach --show-progress --assume-yes-for-downloads --jobs=6 --noinclude-unittest-mode=nofollow --noinclude-pytest-mode=nofollow --nofollow-import-to=scipy --nofollow-import-to=numpy --nofollow-import-to=engine.tests  --windows-icon-from-ico=Setuper/pineapple.ico --output-filename=OneDay.exe start.py


def main():
    warnings.filterwarnings("ignore", category=SyntaxWarning)

    with open("game/other/splashes.json", "r", encoding="UTF-8") as splashes:
        splashes = json.load(splashes)
    splash = str(random.choice(splashes))
    if splash.startswith(">"):
        splash = splash.format(username=str(os.getenv("USERNAME") or os.getenv("USER")))[1:]

    window = Views.MainWindow(width=1024, height=786, title=f"{g.WINDOW_TITLE}: {splash}")
    game = Views.GameMenu()
    window.show_view(game)
    arcade.run()

if __name__ == "__main__":
    #profiler = cProfile.Profile()
    #profiler.enable()  # Начинаем сбор данных
    main()  # Запускаем игру
    #profiler.disable()  # Останавливаем сбор

    # Анализируем и выводим результаты
    #stats = pstats.Stats(profiler)
    #stats.strip_dirs()  # Убираем лишние пути к файлам
    #stats.sort_stats('cumulative')  # Сортируем по общему времени (cumulative time)
    #stats.print_stats(10)