"""Analysis application failures, independent of FastAPI."""


class AnalysisError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)
