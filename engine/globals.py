import arcade.gui


class Globals:

    DEFAULT_IN_GAME_WINDOW_SIZE = (1920, 1080)

    WINDOW_TITLE = "ОДИН ДЕНЬ"
    GAME_NAME = "ОДИН ДЕНЬ из моей оБыЧнОй ЖиЗнИ с моей женой соседкой которая, возможно, демон или вампир :D"

    fm = None  # Files manager
    sm = None  # Saves manager
    am = None  # Audio manager
    scene = None  # Scene
    wwl = None  # Work with lore
    da = None  # Discord actor

    All_views = None

    ListCharacters = None

    attributes = None

    main = None

    FONT_NAME = "Kurale"
    STYLE_DEFAULT_BUTTON = {
        "normal": arcade.gui.UIFlatButton.UIStyle(
            font_size=16,
            font_name=(FONT_NAME,),
            font_color=arcade.color.BLACK,
            bg=(225, 184, 1, 255),
            border=(79, 67, 13, 255),
            border_width=5
        ),
        "hover": arcade.gui.UIFlatButton.UIStyle(
            font_size=16,
            font_name=(FONT_NAME,),
            font_color=arcade.color.BLACK,
            bg=(163, 134, 5, 255),
            border=(79, 67, 13, 255),
            border_width=5
        ),
        "press": arcade.gui.UIFlatButton.UIStyle(
            font_size=16,
            font_name=(FONT_NAME,),
            font_color=arcade.color.BLACK,
            bg=(191, 161, 25, 255),
            border=(79, 67, 13, 255),
            border_width=5
        ),
        "disabled": arcade.gui.UIFlatButton.UIStyle(
            font_size=16,
            font_name=(FONT_NAME,),
            font_color=arcade.color.LIGHT_STEEL_BLUE,
            bg=(66, 71, 77)
        )
    }