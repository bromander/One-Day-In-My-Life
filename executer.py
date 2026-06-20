import subprocess
import sys


args = {
    "file_mode" : 2,
    "dirs" : ["./game/=game"],
    "files" : [],
    "console_mode" : 3,
    "admin" : False,
    "ico" : "Setuper/pineapple.ico",
    "modules" : [],
    "ena_plugins" : ["tk-inter"],
    "dis_plugins" : [],
    "exe_filename" : "OneDay",
    "jobs" : 8,
    "meta" : {"project_name" : None, "project_version" : None, "file_version" : None, "file_description" : None, "torg_mark" : False, "copyright" : None},
    "start" : False,
    "other" : []
}

while True:
    print("Здравствуйте! Этот скрипт предназначен для сборки вашего проекта при помощи Nuitka!")
    print("\nРекомендуемые параметры уже установлены, но вы можете их изменить!")
    print("Нажмите enter, чтобы пропустить.")
    print(
        """
    Изменять только в том случае, если вы уже знаете, что делаете!
        1: Режим компиляции
        2: Включённые директории
        3: Включённые файлы
        4: Режим консоли
        5: Запрос прав администратора при запуске (Только для Windows!)
        6: Иконка
        7: Включить модули
        8: Включить встроенные плагины
        9: Выключить встроенные плагины
        10: Название EXE-файла
        11: Кол-во потоков
        12: Метаданные
        13: Добавить свой аргумент
        14: Запустить игру после сборки
        """
    )

    inp = input("> ")

    if not inp:
        break
    else:
        print("\n")
        match inp:
            case "1":
                print(
                    "Выберете режим:"
                    "   1: accelerated (Сделать вашу программу быстрее, но не сделать её переносимой)\n"
                    "   2: standalone (Автономный режим)\n"
                    "   3: onefile (Однофайловый режим)\n"
                    "   4: app (Режим macOS-приложения)"
                )
                args["file_mode"] = int(input("> "))
            case "2":
                print(
                    "Перечислите нужные директории (ДИРЕКТОРИЯ_В_ПАПКУ=ДИРЕКТОРИЯ_В_СБОРКЕ):\n"
                    "Пример: ./game/=game ./hopes_and_dreams=game/hopes_and_dreams"
                )
                args["dirs"] = input("> ").split()
            case "3":
                print(
                    "Перечислите нужные файлы (ДИРЕКТОРИЯ_ФАЙЛА=ДИРЕКТОРИЯ_В_СБОРКЕ):\n"
                    "Пример: config.json=game/config.json wash_my_belly.txt=game/other/wash_my_belly.txt"
                )
                args["files"] = input("> ").split()
            case "4":
                print(
                    "Выберете режим:\n"
                    "   1: force (Открыть консоль)\n"
                    "   2: disable (Отключить консоль)\n"
                    "   3: attach (Консоль не создаётся, но если открыть игру через консоль, то будут видные все логи)\n"
                    "   4: hide (Консоль создаётся и сразу сворачивается)"
                )
                args["console_mode"] = int(input("> "))
            case "5":
                print(
                    "Выберете режим:\n"
                    "   1: Требовать\n"
                    "   2: Не требовать"
                )
                args["admin"] = int(input("> ")) == 1
            case "6":
                print("Введите путь к файлу (Только в формате .ico):")
                args["ico"] = (input("> "))
            case "7":
                print("Перечислите названия модулей, которых принудительно хотите добавить в сборку:")
                args["modules"] = input("> ").split()
            case "8":
                print("Перечислите названия плагинов, которых нужно включить:")
                args["ena_plugins"] = input("> ").split()
            case "9":
                print("Перечислите названия плагинов, которых нужно выключить:")
                args["dis_plugins"] = input("> ").split()
            case '10':
                print("Напишите название файла:")
                args["exe_filename"] = input("> ")
            case "11":
                print("Напишите кол-во потоков:")
                args["jobs"] = int(input("> "))
            case "12":
                while True:
                    print(
                        "Выберете мета-данные, которые ходите изменить:\n"
                        "   1: Имя проекта\n"
                        "   2: Версия проекта\n"
                        "   3: Версия исполняемого файла\n"
                        "   4: Описание файла\n"
                        "   5: Торговая марка\n"
                        "   6: Информация о авторских правах\n"
                    )
                    inp = input("> ")
                    match inp:
                        case "1":
                            print("Напишите имя проекта:")
                            args["meta"]["project_name"] = input("> ")
                        case "2":
                            print("Введите версию проекта:\n")
                            print("Пример: 1.0.0.0")
                            args["meta"]["project_version"] = input("> ")
                        case "3":
                            print("Введите версию файла:\n")
                            print("Пример: 1.2.3.4")
                            args["meta"]["file_version"] = input("> ")
                        case "4":
                            print("Введите описание файла:\n")
                            args["meta"]["file_description"] = input("> ")
                        case "5":
                            print("Введите торговую марку:")
                            args["meta"]["torg_mark"] = input("> ")
                        case "6":
                            print("Введите информацию о авторских правах:")
                            args["meta"]["copyright"] = input("> ")
                        case _:
                            print("Ошибка! Неизвестный аргумент")
                            continue
                    break
            case "13":
                print("Введите свой аргумент:")
                args["other"] = input("> ")
            case "14":
                print(
                    "Выберете режим:\n"
                    "   1: Запускать\n"
                    "   2: Не запускать"
                )
                args["start"] = int(input("> ")) == 1
            case "":
                break
            case _:
                print("Ошибка! Неизвестный аргумент")
                continue

        print('\n' * 10)
        continue


command = [
    sys.executable,
    '-m', 'nuitka',
    f"--mode={["accelerated", "standalone", "onefile", "app"][args["file_mode"]-1]}",
    f'--windows-console-mode={["force", "disable", "attach", "hide"][args["console_mode"]-1]}',
    '--show-progress',
    '--assume-yes-for-downloads',
    f'--jobs={args["jobs"]}',
    '--noinclude-unittest-mode=nofollow',
    '--noinclude-pytest-mode=nofollow',
    '--nofollow-import-to=scipy',
    '--nofollow-import-to=numpy',
    '--nofollow-import-to=engine.tests',
    f'--windows-icon-from-ico={args["ico"]}',
    f'--output-filename={args["exe_filename"]}.exe'
]
for i in args["dirs"]:
    command.append(f"--include-data-dir={i}")

for i in args["files"]:
    command.append(f"--include-data-files={i}")

if args["admin"]:
    command.append("--windows-uac-admin")

for i in args["modules"]:
    command.append(f"--include-module={i}")

for i in args["ena_plugins"]:
    command.append(f"--enable-plugins={i}")

for i in args["dis_plugins"]:
    command.append(f"--disable-plugins={i}")

if args["meta"]["project_name"]:
    command.append(f"--product-name={args["meta"]["project_name"]}")

if args["meta"]["project_version"]:
    command.append(f"--product-version={args["meta"]["project_version"]}")

if args["meta"]["file_version"]:
    command.append(f"--file-version={args["meta"]["file_version"]}")

if args["meta"]["file_description"]:
    command.append(f"--file-description={args["meta"]["file_description"]}")

if args["meta"]["torg_mark"]:
    command.append(f"--trademark={args["meta"]["torg_mark"]}")

if args["meta"]["copyright"]:
    command.append(f"--copyright={args["meta"]["copyright"]}")

if args["start"]:
    command.append("--run")

for i in args["other"]:
    command.append(i)


command.append('start.py')

print("Запуск сборки Nuitka...")
print("Команда:", ' '.join(command))

try:
    # Запускаем процесс и ждём завершения
    result = subprocess.run(command, check=True, capture_output=False, text=True)
except subprocess.CalledProcessError as e:
    print(f"❌ Ошибка при сборке, код возврата: {e.returncode}")
    print("Вывод ошибки:", e.stderr if e.stderr else "(пусто)")