class RecordNotFoundException(Exception):
    def __init__(self, *args, details=None):
        super().__init__(*args)
        self.details = details


class ValidationException(Exception):
    def __init__(self, *args, details=None):
        super().__init__(*args)
        self.details = details
