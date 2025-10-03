# coding: utf-8


def text_message(fmt, *a, **kw):
    return TextMessage(fmt, *a, **kw)


class Message:
    def __init__(self, *a, **kw):
        self.a = a
        self.kw = kw

    def render_text(self, color=True):
        raise NotImplementedError()

    def __str__(self):
        return self.render_text()

    def __repr__(self):
        return f"{self.__class__.__name__}({str(self)})"


class TextMessage(Message):
    def __init__(self, fmt, *a, **kw):
        super().__init__(*a, **kw)
        self.fmt = fmt

    def render_text(self, color=True):
        return self.fmt.format(*self.a, **self.kw)


class MapMessage(Message):
    def __init__(self, a_map):
        super().__init__()
        self.map = a_map

    def render_text(self, color=True):
        from ..map.util import LineSeg
        from ..find import this_body

        def dist(pos1, pos2):
            return LineSeg(pos1, pos2).distance

        tb = this_body()
        txt = self.map.colorized_text_drawing if color else self.map.text_drawing
        tbp = tb.location.pos
        dob = sorted([(dist(tbp, o.location.pos), o) for o in self.map.objects], key=lambda x: x[0])
        dob = [(f"{o[0]:0.1f}", o[1]) for o in dob if o[1] is not tb]
        if dob:
            mdob = max([len(o[0]) for o in dob])
            for dist, o in dob:
                txt += f"\n{dist:>{mdob}} [{o.abbr}] {o.long}"
        return txt
