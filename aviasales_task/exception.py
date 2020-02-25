class AviasalesTaskException(Exception):
    """Base exception"""


class AviasalesTaskValueError(ValueError, AviasalesTaskException):
    ...
