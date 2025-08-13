class ForbiddenActionError(Exception):
    """Exception raised for forbidden actions."""
    
    def __init__(self, message="This action is forbidden."):
        self.message = message
        super().__init__(self.message)