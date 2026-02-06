
# Параметры

0. **self.scene**
	Объект класса [arcade.Scene()](https://api.arcade.academy/en/stable/api_docs/api/sprite_scenes.html#arcade.Scene)

1. **self.cursor_texture**
	Путь к текстуре  курсора

2. **self.background_color**
	[Цвет](https://api.arcade.academy/en/stable/api_docs/arcade.color.html) фона

3.  **self.characters_sprites**
	Словарь со спрайтами, что в данный момент отображаются на сцене
	\[Название  спрайта : [arcade.Sprite](https://api.arcade.academy/en/stable/api_docs/api/sprites.html#arcade.Sprite) объект\]

4. self.menu_manager
	Объект класса [UIManager](https://api.arcade.academy/en/stable/api_docs/api/gui.html#arcade.gui.UIManager)
	Предназначен для отображения меню выбора де




```python
class GameView(arcade.View):  
  
    def __init__(self):  
        super().__init__()  
        global am, wwl  
        am = AudioManager()  
        wwl = Wwl()  
  
        self.scene = arcade.Scene()  
  
        self.cursor_texture = arcade.Sprite("images/gui/cursor.png", 0.2)  
  
        self.background_color = arcade.color.WHITE  
  
        self.dialog_window = None  
        self.dialog_text_batch = Batch()  
        self.dialog_texts: list = []  
        self.cname_text: Optional[arcade.Text] = None  
  
        self.characters_sprites: dict[str : arcade.Sprite] = {}  
  
        self.scene.add_sprite_list("bg")  
        self.scene.add_sprite_list("characters")  
        self.scene.add_sprite_list("fade")  
        self.scene.add_sprite_list("gui")  
  
        self.menu_manager = agui.UIManager()  
        self.menu_manager.disable()  
        self.menu_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)  
  
        self.is_mouse_pressed = False  
  
        self.last_text = " "  
  
        def create_dialog_window():  
            texture = arcade.load_texture("images/gui/dialog_window.png")  
  
            self.dialog_window = arcade.Sprite(  
                texture,  
                scale=6 * min(self.width / WINDOW_WIDTH, self.height / WINDOW_HEIGHT),  
                center_x=self.width * 0.5,  
                center_y=self.height * 0.13  
            )  
            self.scene.add_sprite("gui", self.dialog_window)  
  
        def create_dialog_fade():  
            texture = arcade.load_texture("images/gui/blackscreen.png")  
  
            fade = arcade.Sprite(  
                texture,  
                scale=50,  
                center_x=self.width * 0.5,  
                center_y=self.height * 0.5  
            )  
            fade.alpha = 0  
            self.scene.add_sprite("fade", fade)  
  
        create_dialog_fade()  
        create_dialog_window()  
  
        self.start_trigger: bool = True  
  
        self.talk_manager()  
  
    def format_text(self, text: str):  
        global NAMESPACE  
        pattern = r'((?<!\\)\[[^\]]*(?:(?<!\\)\][^\[]*)*?(?<!\\)\])'  
        text = re.split(pattern, str(text))  
        for e, i in enumerate(text):  
            if i.startswith("[") and i.endswith("]"):  
                text[e] = NAMESPACE.get(i.strip("[]"), "NONE")  
        text = "".join(text).replace("\\\\", "\\")  
        return text  
  
    def talk_manager(self):  
  
        if not wait_trigger:  
            now = wwl.get_thing()  
            print(now)  
            res = self.talk(now)  
  
            match res:  
                case "NEXT":  
                    self.talk_manager()  
                case "REPEAT":  
                    #self.talk(now)  
                    return None  
                case "END":  
                    return None  
                case "END_text":  
                    return None  
                case "CHANEL":  
                    self.window.set_fullscreen(False)  
                    self.window.size = (1024, 786)  
                    game = GameMenu(False)  
                    self.window.show_view(game)  
  
  
  
    def talk(self, now):  
        global dialog_text_text, cname_text_text  
        global wait_trigger  
  
        while True:  
  
            if now is None:  
                return None  
  
            match now['action']:  
  
                case "SAY":  
                    self.dialog_texts = []  
  
                    self.start_trigger = False  
                    pon = lc.get_character(now["character"]).talk(self.format_text(now["args"]))  
  
                    return "END_text"  
  
                case "PLAY":  
                    match now["play_what"]:  
                        case "MUSIC":  
                            if len(now["args"]) < 2:  
                                now["args"].append(1)  
                            if len(now["args"]) < 3:  
                                now["args"].append(True)  
  
                            am.play_music(f"music/{now["args"][0]}", bool(now["args"][2]), float(now["args"][1]))  
  
                        case "SOUND":  
                            if len(now["args"]) < 2:  
                                now["args"].append(1)  
                            if len(now["args"]) < 3:  
                                now["args"].append(False)  
  
                            am.play_sound(f"sounds/{now["args"][0]}", bool(now["args"][2]), float(now["args"][1]))  
                    return "NEXT"  
  
                case "STOP":  
                    match now["what"]:  
                        case "MUSIC":  
                            if now["effect"] is not None:  
                                am.stop_music(now["effect"])  
                            else:  
                                am.stop_music()  
                        case "SOUND":  
                            if now["effect"] is not None:  
                                am.stop_sound(now["effect"])  
                            else:  
                                am.stop_sound()  
                    return "NEXT"  
  
                case "SHOW":  
                    sprite = lc.get_character(now["character"]).show(str(now["sprite"]))  
                    if 'at' in now:  
                        sprite.center_y = sprite.height / 2  
                        match now['at']:  
                            case "center":  
                                sprite.center_x = self.width // 2  
                            case "left":  
                                sprite.center_x = (self.width // 2) * 0.4  
                            case "right":  
                                sprite.center_x = (self.width // 2) * 1.6  
                    else:  
                        if now["character"] in self.characters_sprites:  
                            sprite.position = self.characters_sprites[now["character"]].position  
  
                    if now["character"] in self.characters_sprites:  
                        self.characters_sprites[now["character"]].remove_from_sprite_lists()  
                    self.characters_sprites[now["character"]] = sprite  
                    self.scene.add_sprite("characters", self.characters_sprites[now["character"]])  
                    return "NEXT"  
  
                case "HIDE":  
                    self.characters_sprites[now["character"]].remove_from_sprite_lists()  
                    del self.characters_sprites[now["character"]]  
                    return "NEXT"  
  
                case "MOVE":  
                    self.Move.move_towards(self.characters_sprites[now["character"]], now["pos"][0], now["pos"][1], now["speed"])  
                    return "NEXT"  
  
                case "SCENE":  
                    self.scene["bg"].clear()  
  
                    for i in self.characters_sprites.values():  
                        i.remove_from_sprite_lists()  
                    texture = arcade.load_texture(f"images/scenes/{now['filename']}")  
                    self.dialog_window = arcade.Sprite(  
                        texture,  
                        scale=float(now['scale']),  
                        center_x=self.width * 0.5,  
                        center_y=self.height * 0.5  
                    )  
                    self.scene.add_sprite("bg", self.dialog_window)  
                    return "NEXT"  
  
                case "FADE":  
                    match now["type"]:  
                        case "FADEIN":  
                            def editing_alpha():  
                                global wait_trigger  
                                wait_trigger = True  
                                start_time = time.time()  
                                duration = now["time"]  
  
                                while True:  
  
                                    elapsed = time.time() - start_time  
  
                                    if elapsed >= duration:  
                                        self.scene["fade"][0].alpha = 255  
                                        break  
  
                                    progress = elapsed / duration  
                                    alpha = int(progress * 255)  
  
                                    if not wait_trigger:  
                                        wait_trigger = True  
  
                                    self.scene["fade"][0].alpha = alpha  
  
                                    time.sleep(0.01)  
  
                                wait_trigger = False  
                            threading.Thread(target=editing_alpha).start()  
                        case "FADEOUT":  
                            def editing_alpha():  
                                start_time = time.time()  
                                duration = now["time"]  
  
                                while True:  
  
                                    elapsed = time.time() - start_time  
                                    if elapsed >= duration:  
                                        alpha = 0  
                                        return None  
  
                                    progress = elapsed / duration  
                                    alpha = 255 - int(progress * 255)  
  
                                    self.scene["fade"][0].alpha = alpha  
  
                                    time.sleep(0.01)  
  
                            threading.Thread(target=editing_alpha).start()  
                    return "NEXT"  
  
                case "JUMP":  
  
                    wwl.pose = 0  
                    wwl.label = now["label"]  
  
                    return "NEXT"  
  
                case "MENU":  
                    global dialog_text_text, cname_text_text  
  
                    dialog_text_text = [" "]  
                    cname_text_text = ""  
  
                    self.show_menu(now['data'])  
                    wait_trigger = True  
  
                    return "END"  
  
                case "WAIT":  
  
                    def _waiter():  
                        global wait_trigger  
  
                        wait_trigger = True  
                        time.sleep(now["time"])  
                        wait_trigger = False  
  
                    threading.Thread(target=_waiter).start()  
                    return "NEXT"  
  
                case "END":  
  
                    wwl.label = main  
                    wwl.pose = 0  
  
                    dialog_text_text = [" "]  
                    cname_text_text = ""  
                    return "CHANEL"  
  
  
                case "EXECUTE":  
                    global NAMESPACE  
                    exec(now["data"], NAMESPACE)  
                    return "NEXT"  
  
                case _:  
                    return None  
  
    def on_draw(self):  
        """  
        Render the screen.        """  
        if not self.start_trigger:  
            self.clear()  
            self.scene.draw()  
            self.create_main_windows()  
            self.dialog_text_batch.draw()  
            self.menu_manager.draw()  
            arcade.draw_sprite(self.cursor_texture)  
  
    def show_menu(self, data):  
  
        def jump(label: str):  
            global wait_trigger  
            wwl.pose = 0  
            wwl.label = label  
            self.menu_manager.clear()  
            self.menu_v_box = arcade.gui.widgets.layout.UIBoxLayout(space_between=20)  
            wait_trigger = False  
            self.talk_manager()  
  
        for k, v in data.items():  
            button = agui.widgets.buttons.UIFlatButton(  
                text=k,  
                width=200  
            )  
            button.on_click = lambda event, label=v: jump(label)  
            self.menu_v_box.add(button)  
  
        ui_anchor_layout = arcade.gui.widgets.layout.UIAnchorLayout()  
        ui_anchor_layout.add(child=self.menu_v_box, anchor_x="center_x", anchor_y="center_y")  
  
        self.menu_manager.add(ui_anchor_layout)  
  
  
    def on_update(self, delta_time):  
        """  
        All the logic to move, and the game logic goes here.        Normally, you'll call update() on the sprite lists that        need it.        """        self.scene.update(delta_time)  
        self.menu_manager.enable()  
  
    def on_key_press(self, key, modifiers):  
        if key == arcade.key.SPACE or key == arcade.key.ENTER or key == arcade.key.ENTER:  
            self.talk_manager()  
  
    def on_mouse_release(self, x, y, button, modifiers):  
        self.is_mouse_pressed = False  
        if int(button) == 1:  
            self.talk_manager()  
  
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool | None:  
        self.is_mouse_pressed = True  
  
    def create_main_windows(self):  
  
        def create_dialog_text():  
  
            def split_by_length(text, max_length):  
                if len(text) <= max_length:  
                    return [text]  
  
                parts = []  
                words = text.split(" ")  
                current_line = []  
  
                for word in words:  
                    if len(word) > max_length:  
                        if current_line:  
                            parts.append(" ".join(current_line))  
                            current_line = []  
  
                        for i in range(0, len(word), max_length):  
                            parts.append(word[i:i + max_length])  
                    else:  
                        test_line = " ".join(current_line + [word])  
                        if len(test_line) <= max_length:  
                            current_line.append(word)  
                        else:  
                            if current_line:  
                                parts.append(" ".join(current_line))  
                            current_line = [word]  
  
                if current_line:  
                    parts.append(" ".join(current_line))  
  
                return parts  
  
  
            for i, line in enumerate(dialog_text_text):  
                for e, sline in enumerate(split_by_length(line, 60)):  
                    if text_anchor == "left":  
                        t = arcade.Text(  
                            text=sline,  
                            x=self.width * 0.18,  
                            y=(self.height * 0.2) - (i+e) * (30 + 10),  
                            font_size=30,  
                            color=dialog_text_colour,  
                            batch=self.dialog_text_batch,  
                            font_name="Kurale",  
                            anchor_x=text_anchor  
                        )  
                    elif text_anchor == "center":  
                        t = arcade.Text(  
                            text=sline,  
                            x=self.width // 2,  
                            y=(self.height * 0.2) - (i + e) * (30 + 10),  
                            font_size=30,  
                            color=dialog_text_colour,  
                            batch=self.dialog_text_batch,  
                            font_name="Kurale",  
                            anchor_x=text_anchor  
                        )  
                    elif text_anchor == "right":  
                        t = arcade.Text(  
                            text=sline,  
                            x=self.width * 0.82,  
                            y=(self.height * 0.2) - (i + e) * (30 + 10),  
                            font_size=30,  
                            color=dialog_text_colour,  
                            batch=self.dialog_text_batch,  
                            font_name="Kurale",  
                            anchor_x=text_anchor  
                        )  
  
                    self.dialog_text_batch.draw()  
  
        def create_cname_text():  
            self.cname_text = arcade.Text(  
                cname_text_text,  
                x=self.width * 0.19,  
                y=self.height * 0.255,  
                font_size=40,  
                multiline=True,  
                width=1150,  
                color=cname_text_colour,  
                font_name="Kurale"  
            )  
            self.cname_text.draw()  
  
        create_dialog_text()  
        create_cname_text()  
  
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> EVENT_HANDLE_STATE:  
        self.cursor_texture.position = (x, y)  
        self.window.set_mouse_visible(False)  
  
    def on_close(self):  
        self.window.set_fullscreen(False)  
        self.window.size = (1024, 786)  
        game = GameMenu()  
        self.window.show_view(game)  
  
    class Move():  
        @staticmethod  
        def move_towards(sprite, target_x, target_y, speed):  
  
            def move():  
                while True:  
                    dx = target_x - sprite.center_x  
                    dy = target_y - sprite.center_y  
                    distance = (dx ** 2 + dy ** 2) ** 0.5  
                    if distance > speed:  
                        sprite.center_x += dx / distance * speed  
                        sprite.center_y += dy / distance * speed  
                    else:  
                        sprite.center_x = target_x  
                        sprite.center_y = target_y  
                    time.sleep(0.01)  
                    if distance <= 0:  
                        break  
  
            threading.Thread(target=move).start()
```