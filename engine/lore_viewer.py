import os
import time
import re


class Wwl:

    def __init__(self):

        def find_files(extension: str):
            results = {}
            current_path = os.getcwd()
            parent_path = os.path.dirname(current_path)
            start_path = parent_path

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

    def _get_lore(self):
        start_label = None
        for e, i in self.files.items():
            if self.label in i['content']:
                start_label = e

        label = []
        index = 0
        files = self.files[start_label]["content"][self.label].split("\n")
        while len(files) > index:
            index += 1
            i = files[index-1].strip()
            match i:

                case n if i.startswith("<"):
                    dial = re.split(r"[<>]", i)
                    dial = [x for x in dial if x]

                    text = "".join(dial[1:])[1:].strip("\"")

                    label.append({"action" : "SAY", "character" : str(dial[0]), "args" : text})

                case n if i.startswith("PLAY"):
                    dial = i.split(" ")
                    dial = dial + [None]*(6 - len(dial)) # 6 - макс кол-во аргументов

                    if dial[4] == "False":
                        dial.pop(4)
                        dial.insert(4, False)
                    elif dial[4] == "True":
                        dial.pop(4)
                        dial.insert(4, True)
                    else:
                        dial.pop(4)
                        if dial[1] == "MUSIC":
                            dial.insert(4, True)
                        else:
                            dial.insert(4, False)

                    if not isinstance(dial[5], (str, type(None))):
                        dial.insert(5, None)

                    label.append({"action": dial[0], "play_what" : dial[1], "path" : dial[2], "volume" : dial[3], "loop": dial[4],  "effect": dial[5], "args": dial[6:]})

                case n if i.startswith("STOP"):
                    dial = i.split(" ")
                    dial = dial + [None]*(6 - len(dial)) # 6 - макс кол-во аргументов
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
                    if len(dial) < 2:
                        dial.append(1)
                    label.append({"action": "FADE", "type": dial[0], "time": float(dial[1])})

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

                case n if i.startswith("MENU"):
                    dial = []
                    for o in i[4:].split(","):
                        dial = dial + [match.group(0) for match in re.finditer(r'"[^"]+"|\S+', o)]
                    data = {}
                    for i in dial:
                        if i.startswith("\"") or i.endswith("\""):
                            data[i.strip("\"")] = None
                            LAST = i.strip("\"")
                            continue
                        else:
                            data[LAST] = str(i)
                    label.append({"action": "MENU", "data": data})

                case n if i.startswith("END"):
                    label.append({"action": "END"})

                case n if i.startswith("#"):
                    continue


                case n if i.startswith("$"):
                    label.append({"action": "EXECUTE", "data" : i.strip("$ ")})

                case n if i.startswith("PYTHON"):
                    data = ""
                    while True:
                        i = files[index][8:]
                        data = f"{data}\n{i}"
                        index += 1
                        if files[index].strip() == "}":
                            break

                    label.append({"action": "EXECUTE", "data": data})

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