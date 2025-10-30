# coding: utf-8

# NOTE: by convention, import this as E
# import space.exceptions as E # or,
# import      .exceptions as E


class SExceptionMixin:
    body_msg_template = 'There was an internal error, "{exception}."'
    body = None

    def __init__(self, *a, **kw):
        # pylint: disable=import-outside-toplevel
        # we lazy import to avoid circular impot issues. It's ok if
        # SExceptionMixin is slower for it. we only use it when something's
        # broken anyway.
        from .find import this_body

        super().__init__(*a, **kw)
        self.body = this_body()
        self.body_msg = self.body_msg_template.format(exception=self)
        self.tell_player()

    def tell_player(self):
        if self.body is not None:
            self.body.tell(self.body_msg)


class STypeError(SExceptionMixin, TypeError):
    pass


class UnfilledArgumentError(STypeError):
    pass


class ContainerError(SExceptionMixin, Exception):
    pass


class ContainerTypeError(ContainerError):
    pass


class LivingSlotSetupError(SExceptionMixin, Exception):
    pass


class ContainerCapacityError(ContainerError):
    pass


class ParseError(SExceptionMixin, SyntaxError):
    pass


class InternalParserError(ParseError):
    pass


class TargetError(ParseError):
    pass


class InvalidDamageType(SExceptionMixin, ValueError):
    pass


class MapError(Exception):
    pass


class BadDirection(SExceptionMixin, MapError, ValueError):
    pass


class UselessDirection(SExceptionMixin, MapError, ValueError):
    pass
