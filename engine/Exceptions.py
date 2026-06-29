class LayerDoesNotExistError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class SpriteDoesNotExistError(Exception):
    def __init__(self, sprite_name, layer):
        self.message = f"Sprite {sprite_name} does not exist in layer {layer}!"
        super().__init__(self.message)


class SpriteIsNotLoadedError(Exception):
    def __init__(self, sprite_name, layer):
        self.message = f"Sprite {sprite_name} is not loaded on scene in layer {layer}!"
        super().__init__(self.message)


class PersistentDoesNotExistError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class VolumeDoesNotExistError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class SaveDoesNotExistError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class MainLabelNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class LabelNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ActionNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class AssetsNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class TextFormatTagError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)