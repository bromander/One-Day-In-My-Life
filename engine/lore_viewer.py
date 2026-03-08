import os
import re
from typing import Optional


class Wwl:

    def __init__(self):
        """
        Отвечает за обработку сценариев
        """

        def find_files(extension: str):
            results = {}
            start_path = f"{os.getcwd()}\\game"

            for root, dirs, files in os.walk(start_path):
                for file in files:
                    if file.lower().endswith(extension.lower()):
                        full_path = os.path.join(root, file)
                        results[file] = {"path": full_path.replace("\\", "/"), "content": {}}
            return results

        self.files = find_files(".jpy")

        for e, i in self.files.items():
            with open(i["path"], "r", encoding="UTF-8") as f:
                f = f.read()
                for o, p in enumerate(f.split("\n")):
                    p = p.strip("\n ")
                    if p.startswith("label"):
                        p =  p.split(" ")
                        self.files[e]["content"][p[1]] = "\n".join(f.split("\n")[o:])

        self.pose = 0
        self.label = "main"
        self.lore = self._get_lore()

        def replace_lines_starting_with_tag(text):
            lines = text.splitlines()
            result_lines = []

            for line in lines:
                leading_spaces = re.match(r'^(\s*)', line).group(1)

                if line.lstrip().startswith('<'):
                    line = line.replace("<>", "<narr>")
                    dial = re.split(r"[<>]", str(line.lstrip()))
                    dial = [x for x in dial if x]
                    new_line = leading_spaces + f"talk(\"{dial[0]}\", {dial[1]})"
                    result_lines.append(new_line)
                else:
                    result_lines.append(line)

            return '\n'.join(result_lines)

        for i in self.files:
            for o in self.files[i]["content"]:
                self.files[i]["content"][o] = replace_lines_starting_with_tag(self.files[i]["content"][o])


    def _get_lore(self):
        start_label = None
        for e, i in self.files.items():
            if self.label in i['content']:
                start_label = e

        label = []
        index = 0
        files = self.files[start_label]["content"][self.label].strip().split("\n")
        while len(files) > index:
            index += 1
            i = files[index-1].strip()
            match i:

                case n if i.startswith("<"):
                    dial = re.split(r"[<>]", i)
                    dial = [x for x in dial if x]

                    text = "".join(dial[1:])[1:].strip("\"")

                    label.append({"action" : "SAY", "character" : str(dial[0]), "args" : text})

                case n if i.strip().startswith("label"):
                    continue

                case n if i.strip().startswith("talk("):
                    label.append({"action": "EXECUTE", "data": i})

                case _:
                    if not i.strip().startswith("label"):
                        data = i + "\n"

                        while index < len(files):
                            next_line = files[index].strip()

                            if (next_line.startswith("<") or
                                    next_line.startswith("$") or
                                    next_line.startswith("{") or
                                    next_line.startswith("talk(") or
                                    next_line.startswith("label")):
                                break

                            data += files[index][4:] + "\n"
                            index += 1
                        label.append({"action": "EXECUTE", "data": data})
                    else:
                        print(f"Не найдена команда: {i.strip()}")

        return label

    def get_thing(self, pos_offset: Optional[int] = None, edit_main: bool = True):
        """
        Возвращает готовую инструкцию действий на текущее положение в сценарии
        :param edit_main: Если False, текущее положение в сценарии не изменится
        """
        if edit_main:
            self.pose += pos_offset if pos_offset is not None else 0
            if len(self._get_lore()) - 1 < self.pose:
                self.pose = 0
                return None
            lore = self._get_lore()[self.pose]
            self.pose += 1
            return lore
        else:
            lore = self._get_lore()[self.pose if pos_offset is None else self.pose + pos_offset]
            return lore


if __name__ == "__main__":
    wwl = Wwl()
    print(wwl._get_lore())