
transform meme_face:
    alpha 0.0
    linear 0.25 alpha 1.0
    pause 0.15
    linear 0.25 alpha 0.0

label interlude:
    scene bg school blackboard
    $ renpy.music.play("music/mike_zone.ogg", fadein=2, relative_volume=0.1, fadeout=3)
    with slow_fade
    $ renpy.notify("Играет:\nVolume Adjustment (DELTARUNE Chapter 3+4 Soundtrack) - Toby Fox")

    $ renpy.sound.play("sfx/school_bell.mp3", relative_volume=0.05, fadeout=2)
    $ renpy.pause(delay = 2, hard=True)

    show aj happy:
        yalign 1.0
        xpos 0.3
    with dissolve
    aj "Иииииииии это конец занятий!"
    "*счастливый шум*"

    show aj 1
    aj "НО-НО-НО, кто дал вам разрешение шуметь?! Сели по местам, быстро!"
    show aj
    aj "У меня для вас объявление. Как все нормальные ученики знают, завтра {b}в десять утра{/b} проходит фестиваль, и вы можете помочь с приготовлениями c утра пораньше, если у вас есть совесть и капля здравого смысла. Считайте это за внеплановый субботник."
    aj "Теперь по правилам. К посторонним не лезть, имущество заведения не портить, быть образцовыми представителями своей-"
    narr_ro "Джек задумчиво окинул взглядом скучающий класс, которому не было никакого дела до речи учителя. Все хотели просто поскорее разбежаться по своим делам. Джеку и самому очень хотелось поскорее уйти, только вот... куда?"
    hide aj with dissolve
    narr_ro "Есть ли в этом странном месте какая-то альтернативная версия его дома? \nМожет, общага? Или что-нибудь наподобие этого?"
    narr_ro "Не ночевать же прямо в классе. Правда?.. ПРАВДА ЖЕ???"
    narr_ro "Вскоре всех распустили. Прежде, чем класс опустел, Джек успел поймать за руку одного из учеников."
    scene bg school class
    show glj1 2
    $ renpy.music.stop(fadeout=2)
    with fade
    j "Извини, я на секунду отвлеку, куда сейчас все расходятся?"
    glj1 "А, ну... \nКто куда, наверное... \nУ всех свои дела..."
    show glj1 1
    glj1 "Я в общагу забегу, скину вещи и пойду к своим."

    screen meme_face_lol:
        add "sprites/surprised_blackmemedudepon_zasrunchik.jpg" at meme_face yalign 1.0 xalign 0.2 zoom 0.3
    show screen meme_face_lol

    j "О..!"
    hide screen meme_face_lol
    j "Слушай, можешь и мне указать путь к общаге? Я тут, эм... \nТолько первый день."

    glj1 "Конечно!"
    scene bg black_screen with slow_fade