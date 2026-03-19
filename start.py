import os
import sys
import arcade
import random
import json
import engine
from engine.main import Views

WINDOW_TITLE = f"Game name"
engine.main.GAME_NAME = "Game Name"


def main():

    with open("game/other/splashes.json", "r", encoding="UTF-8") as splashes:
        splashes = json.load(splashes)
    splash = str(random.choice(splashes))
    if splash.startswith(">"):
        splash = splash.format(username=str(os.getenv("USERNAME") or os.getenv("USER")))[1:]

    window = arcade.Window(width=1024, height=786, title=f"{WINDOW_TITLE}: {splash}", resizable=False)
    game = Views.GameMenu()
    window.show_view(game)
    arcade.run()

if __name__ == "__main__":
    main()