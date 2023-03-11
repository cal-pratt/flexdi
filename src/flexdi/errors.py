class FlexError(Exception):
    pass


class CycleError(FlexError):
    pass


class UntypedError(FlexError):
    pass


class ImplicitBindingError(FlexError):
    pass
