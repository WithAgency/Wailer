class WailerException(Exception):
    """Generic error"""


class WailerSmsException(WailerException):
    """Something went wrong while sending a SMS"""


class WailerTemplateException(WailerException):
    """Something went wrong while rendering a template"""
