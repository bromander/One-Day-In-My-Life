import os
import time
import re


class Wwl:

    def __init__(self):

        def find_files(extension: str):
            results = {}
            start_path = os.getcwd()

            for root, dirs, files in os.walk(start_path):
                for file in files:
                    if file.lower().endswith(extension.lower()):
                        full_path = os.path.join(root, file)
                        results[file] = {"path" : full_path.replace("\\", "/"), "content" : None}
            return results

        self.files = find_files(".arl")

        for e, i in self.files.items():
            with open(i["path"], "r", encoding="UTF-8") as f:
                self.files[e]["content"] = f.read()

        self.pose = 0
        self.label = "label main"
        self.lore = self._get_lore()

    def _get_lore(self):
        start_label = None
        for e, i in self.files.items():
            if self.label in i['content']:
                start_label = e

        label = []
        for i in self.files[start_label]["content"].split("\n"):
            i = str(i).replace("    ", "")
            match i:
                case "label main":
                    continue

                case n if i.startswith("<"):
                    dial = re.split(r"[<>]", i)
                    dial = [x for x in dial if x]

                    text = "".join(dial[1:])[1:]

                    label.append({"action" : "SAY", "character" : str(dial[0]), "args" : text})

                case n if i.startswith("PLAY"):
                    dial = i.split(" ")
                    label.append({"action": dial[0], "play_what" : dial[1], "args" : dial[2:]})

                case n if i.startswith("STOP"):
                    dial = i.split(" ")
                    if len(dial) < 3:
                        dial.insert(2, None)
                    label.append({"action": dial[0], "what": dial[1], "effect": dial[2], "args": dial[3:]})

                case n if i.startswith("SHOW"):
                    dial = i.split(" ")
                    character = dial[1]
                    sprite = ""
                    at = "center"
                    for e, i in enumerate(dial[1:]):
                        if i == "at":
                            at = " ".join(dial[e+2:])
                            break
                        else:
                            if sprite:
                                sprite = sprite + " " + i
                            else:
                                sprite = i
                    label.append({"action": dial[0], "character" : character, "sprite" : sprite, "at" : at})

                case n if i.startswith("HIDE"):
                    dial = i.split(" ")
                    label.append({"action": dial[0], "character": dial[1], "args": dial[2:]})

                case n if i.startswith("MOVE"):
                    dial = i.split(" ")
                    label.append({"action": dial[0], "character": dial[1], "pos": (int(dial[2]), int(dial[3])), "speed": int(dial[4]), "args": dial[5:]})

                case n if i.startswith("FADE"):
                    dial = i.split(" ")
                    label.append({"action": "FADE", "dat": dial[0]})

                case n if i.startswith("SCENE"):
                    dial = i.split(" ")
                    if len(dial) < 3:
                        dial.insert(2, 1)
                    if len(dial) < 4:
                        dial.insert(3, None)
                    label.append({"action": dial[0], "filename" : dial[1], "scale": dial[2], "args": dial[3:]})

                case n if i.startswith("WAIT"):
                    dial = i.split(" ")
                    label.append({"action": dial[0], "time": float(dial[1])})

                case n if i.startswith("JUMP"):

                    label.append({"action": "JUMP", "label"  : i.split(' ')[1]})

                case n if i.startswith("END"):
                    label.append({"action": "END"})

        return label

    def get_thing(self, pos:int = 1, edit_main: bool = True):
        if len(self._get_lore())-1 < self.pose:
            self.pose = 0
            return None
        lore = self._get_lore()[self.pose]
        if edit_main:
            self.pose += pos
        return lore


if __name__ == "__main__":
    wwl = Wwl()
    print(wwl._get_lore())