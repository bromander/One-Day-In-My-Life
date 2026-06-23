from hawk_python_sdk import Hawk
import hawk_python_sdk.core as hawk_core
from .tk_error_inform import show_error
import json
import traceback
import sys
import os
import requests

from .globals import g
from .logger import get_logger

logger = get_logger(__name__)


class ErrorsCaptor:
    def __init__(self):
        self.hawk = self._get_hawk()

    def _has_internet(self, timeout=3):
        try:
            requests.get("https://www.google.com", timeout=timeout)
            return True
        except requests.RequestException:
            return False

    @staticmethod
    def get_save_path():
        if os.name == "nt":  # Windows
            # Используем %APPDATA% (C:\Users\Имя\AppData\Roaming\Название_игры)
            app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
            save_dir = os.path.join(app_data, g.GAME_SAVES_FOLDER_NAME)
        else:
            # Linux/Mac
            save_dir = os.path.join(
                os.path.expanduser("~"), ".local", "share", g.GAME_SAVES_FOLDER_NAME
            )

        os.makedirs(save_dir, exist_ok=True)
        return save_dir

    def _get_hawk(self):
        def _safe_get_near_filelines(filepath, line, margin=10):
            with open(filepath, encoding="UTF-8") as file:
                content = file.readlines()
                content = [x.rstrip() for x in content]

            error_line_in_array = line - 1
            start = max(0, error_line_in_array - margin)

            end = min(len(content), error_line_in_array + margin + 1)

            lines = content[start:end]

            pon = [
                {"line": array_line + 1, "content": lines[array_line - start]}
                for array_line in range(start, end)
            ]

            return pon

        hawk_core.Hawk.get_near_filelines = staticmethod(_safe_get_near_filelines)

        with open("./game/game_data.json", "r", encoding="UTF-8") as f:
            f = json.load(f)
            key = f["hawk_integration_API"]
        hawk = Hawk(key)
        return hawk

    def notice_crash(self, e: Exception):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        logger.critical(text)
        show_error(exc_type, g.sm.Volume.telemetry)

        save_folder = self.get_save_path()

        file = os.path.join(save_folder, "latest_full.log")

        def get_full_logs():
            with open(file, "r", encoding="UTF-8") as logs:
                logs = logs.read()
            return [i for i in logs.split("\n")]

        custom_data = {"logs": str(get_full_logs())}

        if g.sm.Volume.telemetry and self._has_internet():
            self.hawk.send(e, context=custom_data)
        else:
            logger.error(
                "Не получилось отправить лог! Отсутствует подключение к интернету или отключена телеметрия..."
            )