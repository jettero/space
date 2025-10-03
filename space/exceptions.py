# coding: utf-8

# NOTE: by convention, import this as E
# import space.exceptions as E # or,
# import      .exceptions as E


class SExceptionMixin:
    body_msg_template = 'There was an internal error, "{exception}."'
    body = None

    def __init__(self, *a, **kw):
        from .find import this_body

        super().__init__(*a, **kw)
        self.body = this_body()
        self.body_msg = self.body_msg_template.format(exception=self)
        self.tell_player()

    def tell_player(self):
        if self.body is not None:
            self.body.tell(self.body_msg)


class STypeError(TypeError, SExceptionMixin):
    pass


class UnfilledArgumentError(STypeError):
    pass


class ContainerError(Exception, SExceptionMixin):
    pass


class ContainerTypeError(ContainerError):
    pass


class CapacityError(ContainerError):
    pass


class ParseError(SyntaxError, SExceptionMixin):
    pass


class InternalParserError(Exception):
    pass


class TargetError(ParseError):
    pass
