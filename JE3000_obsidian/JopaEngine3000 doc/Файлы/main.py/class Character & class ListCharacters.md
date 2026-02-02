
# class Character

## Параметры:

1. `name` : `str`
	Имя персонажа

2. `char_id`: `Optional[str] = None`
	Идентификатор персонажа. Используется для автоматического нахождения его спрайтов и звуков в файлах

3. `colour`:  `str = ""`
	Цвет текста речи персонажа

4. `name_colour`: `str = ""`
	Цвет имени персонажа

5. `c_scale`: `float = 1.0`
	Размер спрайта персонажа

6. `text_anch`: `str = "left"`
	Расположение текста на экране.
	Бывает: `"left"`, `"center"`, `"right"`

7. `lps`: `int = 60`
	"letters per second" (буквы в секунду). Обозначает скорость появления букв на экране.

## Функции

talk:
	Вызывает появление речи персонажа на экране.
show:
	Проявляет  спрайт персонажа на экране


``` python
class Character():  
    active_threads = []  
  
    def __init__(self, name: str, char_id: Optional[str] = None, colour: str = "", name_colour: str = "", c_scale: float = 1.0, text_anch: str = "left", lps: int = 60):   
        def hex_to_rgb(hex_color: str):  
            if hex_color:  
                hex_color = hex_color.lstrip("#")  
                if len(hex_color) not in (6, 8):  
                    raise ValueError("Hex должен быть в формате RRGGBB")  
  
                r = int(hex_color[0:2], 16)  
                g = int(hex_color[2:4], 16)  
                b = int(hex_color[4:6], 16)  
                if len(hex_color) == 8:  
                    a = int(hex_color[6:8], 16)  
                    return (r, g, b, a)  
                return (r, g, b)  
            else:  
                return arcade.color.WHITE  
  
        def find_files(extension: list):  
            results = {}  
            start_path = f"./images/characters/{char_id}"  
  
            for i in extension:  
                for root, dirs, files in os.walk(start_path):  
                    for file in files:  
                        if file.lower().endswith(i.lower()):  
                            full_path = os.path.join(root, file)  
                            results[file.split(".")[0]] = arcade.Sprite(full_path.replace("\\", "/"))  
  
            return results  
  
  
        self.c_name = name  
        self.colour = hex_to_rgb(colour)  
        self.name_colour = hex_to_rgb(name_colour)  
        self.c_scale = c_scale  
        self.lps = lps  
  
        self.action = None  
        self.last_text = " "  
  
        self.char_id = char_id  
  
        if self.char_id is not None:  
            self.sprites = find_files([".png", ".jpg", ".jpeg", ".PNG", ".JPEG"])  
  
        self.text_anch = text_anch  
  
  
    def talk(self, text: str):  
        global dialog_text_colour, cname_text_colour  
        global dialog_text_text, cname_text_text  
        global text_anchor  
  
        def replace_char_by_index(text, index, new_char):  
            if index < 0 or index >= len(text):  
                return text  
            return text[:index] + new_char + text[index + 1:]  
  
  
        dialog_text_text_alt = [" "]  
        string_index_alt = 0  
        _text_alt = []  
        for char in re.findall(r'\\n |\{[^}]*\}|\S|\s', text):  
            char = str(char)  
  
            if char == r"\n ":  
                string_index_alt += 1  
                _text_alt = []  
                continue  
  
            if not char.startswith("{") and not str(char).endswith("}"):  
                if char != r"\n ":  
                    if char != " ":  
                        _text_alt.append(" ")  
                    else:  
                        _text_alt.append(" ")  
                    if len(dialog_text_text_alt)-1 != string_index_alt:  
                        dialog_text_text_alt.insert(string_index_alt, "".join(_text_alt))  
                    else:  
                        dialog_text_text_alt[string_index_alt] = "".join(_text_alt)  
  
  
        text_anchor = self.text_anch  
  
        am.stop_voice()  
  
        dialog_text_colour = self.colour  
        cname_text_colour = self.name_colour  
  
        self.action = None  
  
        for stop_event, thread in Character.active_threads:  
            stop_event.set()  
            thread.join()  
  
        dialog_text_text = dialog_text_text_alt.copy()  
        cname_text_text = ""  
  
  
        stop_event = threading.Event()  
  
        def _talk():  
            global dialog_text_text, cname_text_text  
            string_index = 0  
            fast = False  
  
            self.action = "talk"  
  
            while True:  
                i = -1  
                if not wait_trigger:  
                    self.last_text = text  
  
                    _text = []  
                    index = 0  
                    for char in re.findall(r'\\n |\{[^}]*\}|\S|\s', text):  
                        i += 1  
                        char = str(char)  
  
                        if char == r"\n ":  
                            string_index += 1  
                            i = -1  
                            _text = []  
                            continue  
  
                        cname_text_text = self.c_name  
  
                        if stop_event.is_set():  
                            self.action = None  
                            return False  
                        if not char.startswith("{") and not str(char).endswith("}"):  
                            if char != r"\n ":  
                                _text.append(char)  
                                dialog_text_text[string_index] = replace_char_by_index(dialog_text_text[string_index], i, char)  
  
                        index += 1  
  
                        def talk_sound():  
                            def _get_random_sound_path():  
                                files = [f"./sounds/character_voice/{self.char_id}/{f}" for f in  
                                         os.listdir(f"./sounds/character_voice/{self.char_id}") if  
                                         os.path.isfile(os.path.join(f"./sounds/character_voice/{self.char_id}", f))]  
                                return random.choice(files)  
  
                            am.play_voice(_get_random_sound_path())  
                            return None  
  
                        if ((index % 3 == 0 and char not in (",", ".", "!", "&", "?")) or index == 1) and self.char_id is not None:  
                            threading.Thread(target=talk_sound).start()  
  
                        if char == ".":  
                            if not fast:  
                                time.sleep(0.1)  
                        elif char == ",":  
                            if not fast:  
                                time.sleep(0.05)  
                        elif char.startswith("{") and str(char).endswith("}"):  
                            char = char[1:][:-1]  
  
                            if char.startswith("w"):  
                                i -= 1  
                                time.sleep(float(char.split("=")[-1]))  
                            if char.startswith("f"):  
                                i -= 1  
                                fast = True  
  
                        if stop_event.is_set():  
                            self.action = None  
                            return False  
                        if not fast:  
                            time.sleep(1 / self.lps)  
                    self.action = None  
                    return False                else:  
                    if not fast:  
                        time.sleep(1 / self.lps)  
                    continue  
  
        thread = threading.Thread(target=_talk)  
        Character.active_threads = [(stop_event, thread)]  
        thread.start()  
  
  
    def show(self, sprite: str, scale: Optional[int] = None) -> arcade.Sprite:  
        if scale is None:  
            scale = self.c_scale  
        now_sprite = self.sprites[sprite]  
        now_sprite.scale = scale  
        return now_sprite
```


# class ListCharacters

## self.characters
Представляет из себя словарь {"идентификатор персонажа" : Объект класса `Character`}
Идентификатор персонажа должен совпадать с char_id.
Введя идентификатор, пользователь может ссылаться на персонажа ^bb2890

## Функция `get_character`:
	Возвращает объект `Character` из `self.characters`

``` python
class ListCharacters:  
    def __init__(self):  
        self.characters = {  
            "j" : Character("Джопа", char_id="j", name_colour="#D2691E", colour="#CD853F"),  
            "aj": Character("АнтиДжек", char_id="aj", name_colour="#3f87cd", c_scale=0.5, colour="#2167C4"),  
            "sj": Character("ГлупоДжек", char_id="sj", name_colour="#D1D0CF", c_scale=0.5, colour="#D4D4D4"),  
            "narr" : Character(" ", None, text_anch="center")  
        }  
    def get_character(self, char_id: str):  
        return self.characters[char_id]
```