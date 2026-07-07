import pyglet

pyglet.options["audio"] = (
    "openal",
    "directsound",
    "silent",
)  # устанавливаем менее потокозависимые драйвера

# C:\Users\roma\PycharmProjects\JopaJam5SecretGame\.venv\Scripts\python.exe -m nuitka --mode=standalone --windows-console-mode=attach --show-progress --assume-yes-for-downloads --jobs=8 --noinclude-unittest-mode=nofollow --noinclude-pytest-mode=nofollow --nofollow-import-to=scipy --nofollow-import-to=numpy --nofollow-import-to=engine.tests --windows-icon-from-ico=Setuper/pineapple.ico --output-filename=OneDay.exe --noinclude-data-files=game/*.jpyc --include-data-dir=./game/=game --enable-plugins=tk-inter start.py

import time
import platform
import os
import arcade
import random
import json
from engine.main import Views, init_file
from engine.errors_captor import ErrorsCaptor
import warnings

from engine.globals import g
from engine.logger import get_logger

logger = get_logger(__name__)


def main():

    start_message = f"""
        {os.getcwd()}
        {time.ctime(time.time())}
        game: {g.GAME_NAME}
        os: {platform.system()}
        os_release: {platform.release()}
        os_version: {platform.version()}
        architecture: {platform.machine()}
        processor: {platform.processor()}
        full_platform: {platform.platform()}
    """
    logger.info(start_message)

    warnings.filterwarnings("ignore", category=SyntaxWarning)

    with open("game/other/splashes.json", "r", encoding="UTF-8") as splashes:
        splashes = json.load(splashes)
    splash = str(random.choice(splashes))
    if splash.startswith(">"):
        splash = splash.format(
            username=str(os.getenv("USERNAME") or os.getenv("USER"))
        )[1:]

    init_file()

    window = Views.MainWindow(
        width=1024, height=786, title=f"{g.WINDOW_TITLE}: {splash}"
    )
    game = Views.GameMenu()
    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    # profiler = cProfile.Profile()
    # profiler.enable()  # Начинаем сбор данных

    try:
        main()  # Запускаем игру
    except KeyboardInterrupt:
        pass
    except Exception as e:
        ErrorsCaptor().notice_crash(e)

    # profiler.disable()  # Останавливаем сбор

    # Анализируем и выводим результаты
    # stats = pstats.Stats(profiler)
    # stats.strip_dirs()  # Убираем лишние пути к файлам
    # stats.sort_stats('cumulative')  # Сортируем по общему времени (cumulative time)
    # stats.print_stats(10)
