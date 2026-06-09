class Persistent:
    def __init__(self, g):
        """
        Отвечает за работу с переменными, которые сохраняются между сессиями
        """
        super().__setattr__("sm", g.sm)

    def __setattr__(self, name, value):
        if "sm" not in self.__dict__:
            super().__setattr__(name, value)
        elif name == "sm":
            super().__setattr__(name, value)
        else:
            self.sm.Persistent.set_persistent(name, value)
            super().__setattr__(name, value)

    def __getattribute__(self, item):
        if item.startswith("__") and item.endswith("__") or item == "sm":
            return object.__getattribute__(self, item)

        return self.sm.Persistent.get_persistent(item)

    def __delattr__(self, item):
        self.sm.Persistent.del_persistent(item)
        object.__delattr__(self, item)
