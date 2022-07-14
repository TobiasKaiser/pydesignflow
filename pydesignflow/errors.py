
class FlowError(Exception):
    pass

class ResultRequired(FlowError):
    def __init__(self, result_id):
        self.result_id = result_id

    def __str__(self):
        return f"Result required, but not present: {self.result_id}"
