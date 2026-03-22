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

        self._connect_loop()

    def _connect_loop(self, details: str = "В главном меню", state: str = ""):
        def idk():
            while True:
                if self.stop_thread_flag:
                    return None

                try:
                    self.RPC.connect()

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

                except InvalidPipe:
                    self.connected = False

                except ValueError:
                    self.connected = False

                else:
                    self.connected = True

                finally:
                    for i in range(10):
                        if self.stop_thread_flag:
                            return None
                        time.sleep(1)

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
            else:
                raise PipeClosed
        except PipeClosed:
            self.connected = False
        else:
            self.connected = True
