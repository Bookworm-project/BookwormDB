'''
This is a stub exception to identify explicitly defined Bookworm Exception.

The intended usage is to raise the exception with a dict that has an error
message, and optionally a code that matches HTTP status codes. e.g.

    raise BookwormException({"message": "I'm a teapot" code:418})

or more tidy for longer messages:
    err = dict(message="I'm a teapot", code=418)
    raise BookwormException(err)

Code should be an int, not a string.
'''


class BookwormException(Exception):
    pass
