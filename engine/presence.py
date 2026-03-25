from pypresence import Presence
from pypresence.exceptions import DiscordNotFound, PipeClosed, InvalidPipe
from pypresence.types import ActivityType, StatusDisplayType
from threading import Thread
from typing import Optional, Literal, Tuple, Union
import json
import time

class Discord_act:
    def __init__(self):
        with open("game/game_data.JSON") as data:
            self.discord_application_ID = json.load(data)["discord_application_ID"]

        self.RPC = Presence(self.discord_application_ID)
        self.connected = False

        self.stop_thread_flag = False

        self.thread: Optional[Thread] = None

        self._connect()

    def _connect(self, details: str = "", state: str = "В главном меню"):

        try:
            self.RPC.connect()
            if details:
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
                    state=state,
                    start=time.time()
                )

        except DiscordNotFound:
            self.connected = False

        except InvalidPipe:
            self.connected = False

        except ValueError:
            self.connected = False

        else:
            self.connected = True

    def update(self, name: str, description: str):

        try:
            if self.connected:
                if name and description:
                    self.RPC.update(
                        status_display_type=StatusDisplayType.NAME,
                        activity_type=ActivityType.PLAYING,
                        details=name,
                        state=description
                    )
                elif not description:
                    self.RPC.update(
                        status_display_type=StatusDisplayType.NAME,
                        activity_type=ActivityType.PLAYING,
                        details=name
                    )
                if not name:
                    self.RPC.update(
                        status_display_type=StatusDisplayType.NAME,
                        activity_type=ActivityType.PLAYING,
                        state=description
                    )
            else:
                raise PipeClosed
        except PipeClosed:
            self.connected = False
        else:
            self.connected = True
