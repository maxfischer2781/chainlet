@staticmethod
def throw_method(type, value=None, traceback=None):  # pylint: disable=redefined-builtin
    """Throw an exception in this element"""
    raise type(value).with_traceback(traceback)
