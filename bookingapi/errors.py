class BookingError(Exception):
    """Expected failure. `message` is shown to the user."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status
