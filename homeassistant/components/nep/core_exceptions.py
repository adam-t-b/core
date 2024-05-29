"""Exceptions."""


class InvalidGatewayException(Exception):
    """API exception occurred when fail to find gateway."""

    def __init__(self, message=None):
        if not message:
            self.message = "Gateway Error"
        else:
            self.message = message
        super().__init__(self.message)
