import os
import argparse
import arcade
import random
import json
import engine
from engine.main import Views
import warnings
# python -m nuitka --standalone --include-data-dir=./game/=game --windows-console-mode=attach --show-progress --assume-yes-for-downloads --include-module=scipy.io.wavfile --jobs=6 --noinclude-unittest-mode=nofollow --noinclude-pytest-mode=nofollow --nofollow-import-to=scipy --nofollow-import-to=numpy --nofollow-import-to=engine.tests --noinclude-data-files=./game/saves.JSON start.py
WINDOW_TITLE = "ОДИН ДЕНЬ"
engine.main.GAME_NAME = "ОДИН ДЕНЬ из моей оБыЧнОй ЖиЗнИ с моей женой соседкой которая, возможно, демон или вампир :D"


def main():
    warnings.filterwarnings("ignore", category=SyntaxWarning)

    with open("game/other/splashes.json", "r", encoding="UTF-8") as splashes:
        splashes = json.load(splashes)
    splash = str(random.choice(splashes))
    if splash.startswith(">"):
        splash = splash.format(username=str(os.getenv("USERNAME") or os.getenv("USER")))[1:]

    window = Views.MainWindow(width=1024, height=786, title=f"{WINDOW_TITLE}: {splash}", resizable=False)
    game = Views.GameMenu()
    window.show_view(game)
    arcade.run()

if __name__ == "__main__":
    main()