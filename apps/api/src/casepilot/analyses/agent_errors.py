"""Safe, stable failures for the V1 Agent component."""


class AgentError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)
