class ActionNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ChannelDoesNotExistError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
