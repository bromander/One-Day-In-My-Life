
class ActionNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class ChannelDoesNotExistError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class LayerDoesNotExistError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class SpriteDoesNotExistError(Exception):
    def __init__(self, message):
        self.message = message
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