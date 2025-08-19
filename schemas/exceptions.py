class InvalidPermissionsError(Exception):
    """Exception raised for invalid or not enough permissions to perform an action"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class TimeValidationError(Exception):
    """Exception raised for invalid time passed in input."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class BusinessRulesValidationError(Exception):
    """Exception raised in case of business logic violation."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class RegistrationError(Exception):
    """Eception rasied in case of an error during the registration"""

    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(self.message)