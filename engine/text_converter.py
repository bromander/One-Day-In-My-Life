import re
from typing import Union


class Parser:
    def __init__(self):
        self.SPLIT_PATTERN = re.compile(r'\{([^}]+)\}')

        self.SELF_CLOSING_TAGS = ("w", "r")
        self.NOT_SELF_CLOSING_TAGS = ("b", "i", "u", "s", "color", "size")

    def parse(self, text: Union[str, list[str]]) -> list[dict]:
        parts = text
        if isinstance(text, str):
            parts = re.split(self.SPLIT_PATTERN, text)

        result = []
        active_tags = []  # упорядоченный стек открытых тегов
        buffer = ""

        def flush():
            nonlocal buffer
            if buffer:
                tag = ''.join(active_tags) if active_tags else None
                result.append({"tag": tag, "text": buffer})
                buffer = ""

        for i, part in enumerate(parts):
            if i % 2 == 0:
                buffer += part
            else:
                content = part

                if content.startswith('/'):
                    tag_name = content[1:]
                    if tag_name in self.NOT_SELF_CLOSING_TAGS:
                        if tag_name in active_tags:
                            flush()
                            while active_tags and active_tags[-1] != tag_name:
                                active_tags.pop()
                            if active_tags and active_tags[-1] == tag_name:
                                active_tags.pop()
                        else:
                            active_tags.append(tag_name)
                            flush()
                            active_tags.pop()
                            for item in result[:-1]:
                                if item['tag'] is None:
                                    item['tag'] = tag_name
                                else:
                                    item['tag'] = tag_name + item['tag']
                    else:
                        buffer += "{" + content + "}"

                else:
                    if '=' in content and content.startswith(self.SELF_CLOSING_TAGS):
                        buffer += "{" + content + "}"
                    else:
                        if content in self.NOT_SELF_CLOSING_TAGS:
                            flush()
                            active_tags.append(content)
                        else:
                            buffer += "{" + content + "}"
        flush()
        return result


if "__main__" == __name__:
    ret = Parser().parse(
        "Обожаю {b}первое апреля~{/b} {i}воистину самая остроумная шутка от мира людей{/i}, подумайте только – целую дату посвятить розыгрышам и хохмам, а потом развернуть её в мировом масштабе. Смех, да и только!"
    )
    print(ret)