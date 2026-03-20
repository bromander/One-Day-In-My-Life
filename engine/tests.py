import unittest
import os
import time
import random
from mimesis import Person, File, Text
from mimesis.locales import Locale
from arcade import Sprite
from scipy.io.wavfile import write
from uuid import uuid4
from pathlib import Path
from PIL import Image
import numpy as np
from tqdm import tqdm

from .files_manager import FilesManager
from .list_generator import ListActiveGenerators
from .waiter import Waiter
from .scene import Scene

person = Person(locale=Locale.RU)
file_pr = File()
text_pr = Text(locale=Locale.RU)


class TestFilesManager(unittest.TestCase):

    def test_init_images(self):
        self.maxDiff = None

        paths = {
            "images": "./test_datas/images",
            "music": "./test_datas/music",
            "sounds": "./test_datas/sounds"
        }
        for i in os.listdir(paths["images"]):
            os.remove(paths["images"] + "/" + str(i))

        for i in tqdm(range(100), "Создание изображений"):
            arr = np.random.randint(0, 256,
                                    size=(random.randint(1, 1000), random.randint(1, 1000), random.randint(3, 4)),
                                    dtype=np.uint8)
            im = Image.fromarray(arr).convert("RGB")
            path = paths["images"] + "/" + str(uuid4()) + "." + str(random.choice(["jpg", "jpeg", "png"]))
            im.save(path)

        fm = FilesManager(paths)

        self.assertListEqual(list(fm.textures_paths.keys()),
                             os.listdir(paths["images"]),
                             f"Ошибка при загрузке изображений!"
                             )

        del fm

        for i in os.listdir(paths["images"]):
            os.remove(paths["images"] + "/" + str(i))

    def test_init_music(self):
        self.maxDiff = None

        paths = {
            "images": "./test_datas/images",
            "music": "./test_datas/music",
            "sounds": "./test_datas/sounds"
        }
        for i in os.listdir(paths["music"]):
            os.remove(paths["music"] + "/" + str(i))

        for i in tqdm(range(100), "Создание длинных музыкальных файлов"):
            noise = np.random.normal(0, 0.2, 44100 * random.randint(30, 60))
            noise_int = (noise * 32767).astype(np.int16)
            path = paths["music"] + "/" + str(uuid4()) + "." + str(random.choice(["wav"]))
            write(path, 44100, noise_int)

        fm = FilesManager(paths)

        self.assertListEqual(list(fm.audio_paths.keys()),
                             os.listdir(paths["music"]),
                             f"Ошибка при загрузке музыки!")

        del fm

        for i in os.listdir(paths["music"]):
            os.remove(paths["music"] + "/" + str(i))

    def test_init_sound(self):
        self.maxDiff = None

        paths = {
            "images": "./test_datas/images",
            "music": "./test_datas/music",
            "sounds": "./test_datas/sounds"
        }
        for i in os.listdir(paths["sounds"]):
            os.remove(paths["sounds"] + "/" + str(i))

        for i in tqdm(range(100), "Создание коротких музыкальных файлов"):
            noise = np.random.normal(0, 0.2, 44100 * random.randint(1, 10))
            noise_int = (noise * 32767).astype(np.int16)
            path = paths["sounds"] + "/" + str(uuid4()) + "." + str(random.choice(["wav"]))
            write(path, 44100, noise_int)

        fm = FilesManager(paths)

        self.assertListEqual(list(fm.audio_paths.keys()),
                             os.listdir(paths["sounds"]),
                             f"Ошибка при загрузке звуков!")

        del fm

        for i in os.listdir(paths["sounds"]):
            os.remove(paths["sounds"] + "/" + str(i))

    def test_load_assets(self):
        self.maxDiff = None

        paths = {
            "images": "./test_datas/images",
            "music": "./test_datas/music",
            "sounds": "./test_datas/sounds"
        }

        # ------------- IMAGES

        for i in os.listdir(paths["images"]):
            os.remove(paths["images"] + "/" + str(i))

        for i in tqdm(range(50), "Создание изображений"):
            arr = np.random.randint(0, 256,
                                    size=(random.randint(1, 1000), random.randint(1, 1000), random.randint(3, 4)),
                                    dtype=np.uint8)
            im = Image.fromarray(arr).convert("RGB")
            path = paths["images"] + "/" + str(uuid4()) + "." + str(random.choice(["jpg", "jpeg", "png"]))
            im.save(path)

        # ------------- SOUNDS

        for i in os.listdir(paths["sounds"]):
            os.remove(paths["sounds"] + "/" + str(i))

        for i in tqdm(range(50), "Создание коротких музыкальных файлов"):
            noise = np.random.normal(0, 0.2, 44100 * random.randint(1, 10))
            noise_int = (noise * 32767).astype(np.int16)
            path = paths["sounds"] + "/" + str(uuid4()) + "." + str(random.choice(["wav"]))
            write(path, 44100, noise_int)

        # ------------- MUSIC

        for i in os.listdir(paths["music"]):
            os.remove(paths["music"] + "/" + str(i))

        for i in tqdm(range(50), "Создание длинных музыкальных файлов"):
            noise = np.random.normal(0, 0.2, 44100 * random.randint(30, 60))
            noise_int = (noise * 32767).astype(np.int16)
            path = paths["music"] + "/" + str(uuid4()) + "." + str(random.choice(["wav"]))
            write(path, 44100, noise_int)

        # -------------


        fm = FilesManager(paths)

        for i in tqdm(paths, "Загрузка паков ассетов"):
            fm.audios.clear()
            fm.textures.clear()

            target = fm.load_assets(os.listdir(paths[i]), person.name())

            while target.is_alive():
                pass

            if i == "images":
                self.assertListEqual(list(fm.textures.keys()), os.listdir(paths[i]))
            else:
                self.assertListEqual(list(fm.audios.keys()), os.listdir(paths[i]))


        del fm


        for i in os.listdir(paths["sounds"]):
            os.remove(paths["sounds"] + "/" + str(i))
        for i in os.listdir(paths["music"]):
            os.remove(paths["music"] + "/" + str(i))
        for i in os.listdir(paths["images"]):
            os.remove(paths["images"] + "/" + str(i))

class TestActiveGenerators(unittest.TestCase):

    def test_generator_CONSISTENTLY(self):

        lg = ListActiveGenerators()

        numbers = []

        for i in range(100):
            def generator(numbers):
                for i in range(100):
                    numbers.append(i)
                    yield i

            gen = generator(numbers)

            lg.add_generator("consistently", gen, "TEST")

        for i in range(100000):
            lg.update(1/random.randint(10, 120))

        self.assertListEqual(numbers, [i for i in range(100)]*100)

    def test_generator_TOGETHER(self):

        lg = ListActiveGenerators()

        numbers = []

        for i in range(100):
            def generator(numbers):
                for i in range(100):
                    numbers.append(i)
                    yield i

            gen = generator(numbers)

            lg.add_generator("together", gen, "TEST")

        for i in range(10000):
            lg.update(1/random.randint(10, 120))

        self.assertListEqual(numbers, [i for i in range(100) for _ in range(100)])

    def test_generator_TALK(self):

        lg = ListActiveGenerators()

        numbers = []

        for i in range(100):
            def generator(numbers):
                for i in range(100):
                    numbers.append(i)
                    yield i

            gen = generator(numbers)

            lg.add_generator("consistently", gen, lg._talk_description)

            for i in range(10):
                lg.update(1 / random.randint(10, 120))

        self.assertListEqual(numbers, [i for i in range(10)] * 100)

class TestWorkWithLore(unittest.TestCase):

    def random_lore_generator(self):
        pass

class TestWaiter(unittest.TestCase):

    def test_state(self):
        params = [random.choice([True, False]) for i in range(100)]
        waiters = [Waiter(i) for i in params]
        for i in tqdm(waiters, "Инвертированная проверка переключаетля"):
            i.switch()
        params_repl = [not i for i in params]

        self.assertListEqual([i.state for i in waiters], params_repl)

    def test_on(self):
        params = [random.choice([True, False]) for i in range(100)]
        waiters = [Waiter(i) for i in params]
        for i in tqdm(waiters, "Проверка включения переключателя"):
            i.on()

        self.assertListEqual([i.state for i in waiters], [True for i in range(100)])

    def test_off(self):
        params = [random.choice([True, False]) for i in range(100)]
        waiters = [Waiter(i) for i in params]
        for i in tqdm(waiters, "Проверка выключения переключателя"):
            i.off()

        self.assertListEqual([i.state for i in waiters], [False for i in range(100)])

class TestScene(unittest.TestCase):

    def test_add_sprite(self):
        self.maxDiff = None

        paths = {
            "images": "./test_datas/images",
            "music": "./test_datas/music",
            "sounds": "./test_datas/sounds"
        }
        for i in os.listdir(paths["images"]):
            os.remove(paths["images"] + "/" + str(i))

        for i in tqdm(range(50), "Создание изображений"):
            arr = np.random.randint(0, 256,
                                    size=(random.randint(1, 1000), random.randint(1, 1000), random.randint(3, 4)),
                                    dtype=np.uint8)
            im = Image.fromarray(arr).convert("RGB")
            path = paths["images"] + "/" + str(uuid4()) + "." + str(random.choice(["jpg", "jpeg", "png"]))
            im.save(path)

        print("Загрузка спрайтов...")
        fm = FilesManager(paths)

        scene = Scene(fm)

        target = fm.load_assets(os.listdir(paths["images"]), person.name())

        while target.is_alive():
            pass

        for i in tqdm(os.listdir(paths["images"]), "Добавление спрайтов"):
            texture = scene.get_texture(i)
            self.assertIsNotNone(texture, f"Текстура {i} is None!")

            sprite = Sprite(texture)

            layer = random.choice(["bg", "sprites", "gui", "fade"])

            scene.add_sprite(layer, str(texture.file_path.name), sprite)

            self.assertIn(str(texture.file_path.name), scene[layer])
            self.assertIs(scene[layer][str(texture.file_path.name)], sprite)

        for i in os.listdir(paths["images"]):
            os.remove(paths["images"] + "/" + str(i))