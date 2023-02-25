class FlexError(Exception):
    pass


class CycleError(FlexError):
    pass


class SetupError(FlexError):
    pass


class UntypedError(FlexError):
    pass
