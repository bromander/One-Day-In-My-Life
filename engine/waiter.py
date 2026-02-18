
class Waiter:
    def __init__(self, default=False):
        self.state = default

    def __bool__(self) -> bool:
        return self.state

    def on(self) -> None:
        self.state = True

    def off(self) -> None:
        self.state = False