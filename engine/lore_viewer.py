import os
import re
import ast
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
                        p = re.split(r"[() ]", p)
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

    def parse_label_string(self, label_str, default_values, param_names):

        content = re.sub(r'^label\s+[^(]*\(\s*', '', label_str)
        content = re.sub(r'\s*\)\s*:\s*$', '', content)

        params_list = []
        current_param = ''
        in_quotes = False
        quote_char = ''
        bracket_count = 0

        for char in content:
            if char in ['"', "'"] and not in_quotes:
                in_quotes = True
                quote_char = char
                current_param += char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = ''
                current_param += char
            elif char == '(' and not in_quotes:
                bracket_count += 1
                current_param += char
            elif char == ')' and not in_quotes:
                bracket_count -= 1
                current_param += char
            elif char == ',' and not in_quotes and bracket_count == 0:
                params_list.append(current_param.strip())
                current_param = ''
            else:
                current_param += char

        if current_param.strip():
            params_list.append(current_param.strip())

        params = {}
        position = 0

        for param_str in params_list:
            named_match = re.match(r'(\w+)\s*=\s*(.+)', param_str)

            if named_match:
                key, value = named_match.groups()
                value = value.strip()

                if (value.startswith('"') and value.endswith('"')) or \
                        (value.startswith("'") and value.endswith("'")):
                    params[key] = value[1:-1]
                elif value == 'True':
                    params[key] = True
                elif value == 'False':
                    params[key] = False
                elif value.replace('.', '').replace('-', '').isdigit():
                    params[key] = float(value) if '.' in value else int(value)
                else:
                    params[key] = value
            else:
                value = param_str.strip()

                if (value.startswith('"') and value.endswith('"')) or \
                        (value.startswith("'") and value.endswith("'")):
                    param_value = value[1:-1]
                elif value == 'True':
                    param_value = True
                elif value == 'False':
                    param_value = False
                elif value.replace('.', '').replace('-', '').isdigit():
                    param_value = float(value) if '.' in value else int(value)
                else:
                    param_value = value

                if position < len(param_names):
                    param_name = param_names[position]
                    if param_name not in params:
                        params[param_name] = param_value

                position += 1

        result = default_values.copy()
        result.update(params)

        return result

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

                    default_values = {
                        'name': '',
                        'description': '',
                        'duration': 1.0,
                        'show_splash': False
                    }
                    param_names = ['name', 'description', 'duration', 'show_splash']
                    data = self.parse_label_string(i.strip(" "), default_values, param_names)
                    label.append({"action": "SHOW_SPLASH", "data": data})

                    continue

                case n if i.strip().startswith("talk("):
                    label.append({"action": "EXECUTE", "data": i, "super" : "SAY"}) # Добавляем super, чтобы отличить от остальных EXECUTE

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

                        code_blocks = self._split_python_code(data)
                        for block in code_blocks:
                            if block.strip():
                                label.append({"action": "EXECUTE", "data": block})
                    else:
                        print(f"Не найдена команда: {i.strip()}")
        return label

    def _split_python_code(self, code):
        """Разбивает Python код на отдельные top-level блоки"""
        blocks = []
        lines = code.splitlines()

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [code]

        for node in tree.body:
            start_line = node.lineno - 1
            end_line = getattr(node, 'end_lineno', start_line)

            block_lines = lines[start_line:end_line]
            if block_lines:
                block = '\n'.join(block_lines)
                blocks.append(block)

        return blocks

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