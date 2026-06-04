class Define:
    def __init__(self):
        """
        Отвечает за работку с переменными, которые сохраняются со всеми сохранениями
        """
        super().__setattr__("defines", {})

    def __setattr__(self, name, value):
        if name == "defines":
            super().__setattr__(name, value)
        else:
            defines = super().__getattribute__("defines")
            defines[name] = value

    def __getattribute__(self, name):
        if name == "defines":
            return super().__getattribute__(name)
        try:
            return super().__getattribute__(name)
        except AttributeError:
            defines = super().__getattribute__("defines")
            if name in defines:
                return defines[name]
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

    def __delattr__(self, name):
        if name == "defines":
            super().__delattr__(name)
        else:
            defines = super().__getattribute__("defines")
            if name in defines:
                del defines[name]
            else:
                try:
                    super().__delattr__(name)
                except AttributeError:
                    pass

    def get_all_variables(self):
        """Возвращает все пользовательские переменные"""
        return (
            self.defines.copy()
        )  # Возвращаем копию, чтобы избежать случайных изменений