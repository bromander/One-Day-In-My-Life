from arcade import get_window


class Screen:
    def __init__(self, g):
        self.g = g

    def call_view(self, view_name: str):
        def call():
            window = get_window()
            self.g.main.waiting_autoskip.off()
            view = getattr(self.g.GameViews, view_name)()
            window.show_view(view)
            yield

        self.g.actions.active_generators.add_generator(
            "consistently", call(), "call_screen"
        )
