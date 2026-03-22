from pypresence import Presence
from pypresence.exceptions import DiscordNotFound, PipeClosed
from pypresence.types import ActivityType, StatusDisplayType
from threading import Thread
import json
import time

class Discord_act:
    def __init__(self):
        with open("game/game_data.JSON") as data:
            self.discord_application_ID = json.load(data)["discord_application_ID"]

        self.RPC = Presence(self.discord_application_ID)
        self.connected = False

        self.thread = None

        self._connect_loop()

    def _connect_loop(self, details: str = "В главном меню", state: str = ""):
        def idk():
            while True:
                try:
                    self.RPC.connect()
                    self.connected = True

                    if state:
                        self.RPC.update(
                            status_display_type=StatusDisplayType.NAME,
                            activity_type=ActivityType.PLAYING,
                            details=details,
                            state=state,
                            start=time.time()
                        )
                    else:
                        self.RPC.update(
                            status_display_type=StatusDisplayType.NAME,
                            activity_type=ActivityType.PLAYING,
                            details=details,
                            start=time.time()
                        )

                except DiscordNotFound:
                    self.connected = False

                else:
                    return None

                finally:
                    time.sleep(15)

        self.thread = Thread(target=idk)
        self.thread.start()

    def update(self, name: str, description: str):

        try:
            if self.connected:
                if name:
                    self.RPC.update(
                        status_display_type=StatusDisplayType.NAME,
                        activity_type=ActivityType.PLAYING,
                        details=name
                    )
                if description:
                    self.RPC.update(
                        status_display_type=StatusDisplayType.NAME,
                        activity_type=ActivityType.PLAYING,
                        state=description
                    )
        except PipeClosed:
            self.connected = False
        else:
            self.connected = True
