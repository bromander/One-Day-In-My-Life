import os
import sys
import arcade
import random
import json
sys.path.insert(0, os.path.dirname(__file__))
import engine
from engine.main import GameMenu, init_file

WINDOW_TITLE = f"Game name"

def main():

    init_file()

    with open("game/other/splashes.json", "r", encoding="UTF-8") as splashes:
        splashes = json.load(splashes)
    splash = str(random.choice(splashes))
    if splash.startswith(">"):
        splash = splash.format(username=str(os.getenv("USERNAME") or os.getenv("USER")))[1:]

    window = arcade.Window(width=1024, height=786, title=f"{WINDOW_TITLE}: {splash}", resizable=False)
    game = GameMenu()
    window.show_view(game)
    arcade.run()

if __name__ == "__main__":
    main()