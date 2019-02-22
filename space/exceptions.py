# coding: utf-8

from .find import this_body

class SpaceExceptionMixIn:
    body_msg_template = 'There was an internal error, "{exception}."'
    body = None

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.body = this_body()
        self.body_msg = self.body_msg_template.format(exception=self)
        self.tell_player()

    def tell_player(self):
        if self.body is not None:
            self.body.tell(self.body_msg)

class SpaceTypeError(TypeError, SpaceExceptionMixIn):
    pass
