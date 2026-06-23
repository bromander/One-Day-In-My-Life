
from pypresence import Presence
from pypresence.exceptions import DiscordNotFound, PipeClosed, InvalidPipe
from pypresence.types import ActivityType, StatusDisplayType
from threading import Thread
from typing import Optional
import json
import time


class Discord_act:
    def __init__(self):
        with open("game/game_data.json") as data:
            self.discord_application_ID = json.load(data)["discord_application_ID"]

        self.RPC = Presence(self.discord_application_ID)
        self.connected = False

        self.stop_thread_flag = False

        self.thread: Optional[Thread] = None

        self.start_time = time.time()

        self._connect()

    def _connect(self, details: str = "", state: str = "В главном меню"):

        def con():
            try:
                self.RPC.connect()
                if details:
                    self.RPC.update(
                        status_display_type=StatusDisplayType.NAME,
                        activity_type=ActivityType.PLAYING,
                        details=details,
                        state=state,
                        start=self.start_time,
                    )
                else:
                    self.RPC.update(
                        status_display_type=StatusDisplayType.NAME,
                        activity_type=ActivityType.PLAYING,
                        state=state,
                        start=self.start_time,
                    )

            except DiscordNotFound:
                self.connected = False

            except InvalidPipe:
                self.connected = False

            except ValueError:
                self.connected = False

            else:
                self.connected = True

        Thread(target=con).start()

    def update(self, name: str, description: str):
        try:
            if self.connected:
                if name != ")" and description:
                    self.RPC.update(
                        status_display_type=StatusDisplayType.NAME,
                        details=name,
                        state=description,
                        start=self.start_time,
                    )
                elif not description:
                    self.RPC.update(
                        status_display_type=StatusDisplayType.NAME,
                        details=name,
                        start=self.start_time,
                    )
                else:
                    self.RPC.update(
                        status_display_type=StatusDisplayType.NAME,
                        state=description,
                        start=self.start_time,
                    )
            else:
                raise PipeClosed
        except PipeClosed:
            self.connected = False
        else:
            self.connected = True
