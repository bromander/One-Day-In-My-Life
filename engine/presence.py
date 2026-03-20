from pypresence import Presence
from pypresence.exceptions import DiscordNotFound
from pypresence.types import ActivityType, StatusDisplayType
import json
import time

class Discord_act:
    def __init__(self):
        with open("game/game_data.JSON") as data:
            self.discord_application_ID = json.load(data)["discord_application_ID"]

        self.RPC = Presence(self.discord_application_ID)
        self.connected = False

        try:
            self.RPC.connect()
            self.connected = True
            self.RPC.update(
                status_display_type=StatusDisplayType.NAME,
                activity_type=ActivityType.PLAYING,
                details="В главном меню",
                start=time.time()
            )

        except DiscordNotFound:
            pass

    def update(self, name: str, description: str):

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
