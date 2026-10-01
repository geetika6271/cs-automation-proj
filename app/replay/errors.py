class ReplayError(Exception):

    def __init__(self, step_id: str, message: str,expected=None,observed=None):

        super().__init__(message)
        self.step_id = step_id
        self.expected = expected
        self.observed = observed


class BusinessOutcomeError(ReplayError):

    def __init__(self,step_id: str, code: str,message: str):
        super().__init__(step_id=step_id,message=message )
        self.code = code


class RecoverableReplayError(ReplayError):
    pass