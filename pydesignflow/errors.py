
class FlowError(Exception):
    pass

class ResultRequired(FlowError):
    def __init__(self, target_id):
        self.target_id = target_id

    def __str__(self):
        return f"Result of target {self.target_id.block_id}.{self.target_id.task_id} is missing."
