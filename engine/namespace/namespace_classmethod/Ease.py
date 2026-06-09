import math


class Ease:
    @staticmethod
    def prepare_effect(name: str, t: float):
        return Ease.__dict__[name](t)

    # ---- Квадратичные (Quad) ----
    @staticmethod
    def ease_in_quad(t):
        return t * t

    @staticmethod
    def ease_out_quad(t):
        return t * (2 - t)

    @staticmethod
    def ease_in_out_quad(t):
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2

    # ---- Кубические (Cubic) ----
    @staticmethod
    def ease_in_cubic(t):
        return t * t * t

    @staticmethod
    def ease_out_cubic(t):
        return 1 - pow(1 - t, 3)

    @staticmethod
    def ease_in_out_cubic(t):
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

    # ---- Синусоидальные (Sine) ----
    @staticmethod
    def ease_in_sine(t):
        return 1 - math.cos((t * math.pi) / 2)

    @staticmethod
    def ease_out_sine(t):
        return math.sin((t * math.pi) / 2)

    @staticmethod
    def ease_in_out_sine(t):
        return -(math.cos(math.pi * t) - 1) / 2

    # ---- Экспоненциальные (Expo) ----
    @staticmethod
    def ease_in_expo(t):
        return 0 if t == 0 else pow(2, 10 * (t - 1))

    @staticmethod
    def ease_out_expo(t):
        return 1 if t == 1 else 1 - pow(2, -10 * t)

    @staticmethod
    def ease_in_out_expo(t):
        if t == 0 or t == 1:
            return t
        if t < 0.5:
            return pow(2, 20 * t - 10) / 2
        else:
            return (2 - pow(2, -20 * t + 10)) / 2

    # ---- Круговые (Circ) ----
    @staticmethod
    def ease_in_circ(t):
        return 1 - math.sqrt(1 - pow(t, 2))

    @staticmethod
    def ease_out_circ(t):
        return math.sqrt(1 - pow(t - 1, 2))

    @staticmethod
    def ease_in_out_circ(t):
        if t < 0.5:
            return (1 - math.sqrt(1 - pow(2 * t, 2))) / 2
        else:
            return (math.sqrt(1 - pow(-2 * t + 2, 2)) + 1) / 2

    # ---- Отскок (Bounce) ----
    @staticmethod
    def ease_out_bounce(t):
        n1 = 7.5625
        d1 = 2.75
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375

    @staticmethod
    def ease_in_bounce(t):
        def ease_out_bounce(t):
            n1 = 7.5625
            d1 = 2.75
            if t < 1 / d1:
                return n1 * t * t
            elif t < 2 / d1:
                t -= 1.5 / d1
                return n1 * t * t + 0.75
            elif t < 2.5 / d1:
                t -= 2.25 / d1
                return n1 * t * t + 0.9375
            else:
                t -= 2.625 / d1
                return n1 * t * t + 0.984375

        return 1 - ease_out_bounce(1 - t)

    @staticmethod
    def ease_in_out_bounce(t):
        def ease_out_bounce(t):
            n1 = 7.5625
            d1 = 2.75
            if t < 1 / d1:
                return n1 * t * t
            elif t < 2 / d1:
                t -= 1.5 / d1
                return n1 * t * t + 0.75
            elif t < 2.5 / d1:
                t -= 2.25 / d1
                return n1 * t * t + 0.9375
            else:
                t -= 2.625 / d1
                return n1 * t * t + 0.984375

        return (1 - ease_out_bounce(1 - t)) if t < 0.5 else ease_out_bounce(t)

    # ---- Эластик (Elastic) ----
    @staticmethod
    def ease_in_elastic(t):
        if t == 0 or t == 1:
            return t
        return -pow(2, 10 * (t - 1)) * math.sin((t - 1.075) * (2 * math.pi) / 0.3)

    @staticmethod
    def ease_out_elastic(t):
        if t == 0 or t == 1:
            return t
        return pow(2, -10 * t) * math.sin((t - 0.075) * (2 * math.pi) / 0.3) + 1

    @staticmethod
    def ease_in_out_elastic(t):
        if t == 0 or t == 1:
            return t
        if t < 0.5:
            return (
                -(
                    pow(2, 20 * t - 10)
                    * math.sin((20 * t - 11.125) * (2 * math.pi) / 4.5)
                )
                / 2
            )
        else:
            return (
                pow(2, -20 * t + 10)
                * math.sin((20 * t - 11.125) * (2 * math.pi) / 4.5)
                / 2
                + 1
            )

    # ---- Бэк (Back) - перебор с возвратом ----
    @staticmethod
    def ease_in_back(t):
        c1 = 1.70158
        return c1 * t * t * t - c1 * t * t

    @staticmethod
    def ease_out_back(t):
        c1 = 1.70158
        return 1 + (c1 + 1) * pow(t - 1, 3) + c1 * pow(t - 1, 2)

    @staticmethod
    def ease_in_out_back(t):
        c1 = 1.70158
        c2 = c1 * 1.525
        if t < 0.5:
            return (pow(2 * t, 2) * ((c2 + 1) * 2 * t - c2)) / 2
        else:
            return (pow(2 * t - 2, 2) * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2
