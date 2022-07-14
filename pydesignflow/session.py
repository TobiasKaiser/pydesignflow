from .result import Result
from .errors import FlowError

class BuildSession:
    def __init__(self, flow, build_dir):
        self.flow = flow
        self.build_dir = build_dir
        self.results = None # (block_id, action_id) -> Result map
        self.reload_results()

    def run_action(self, block_id, action_id):
        block = self.flow.blocks[block_id]
        block.actions[action_id].run(self)
    
    def action_dir(self, block_id, action_id):
        return self.build_dir / block_id / action_id

    def write_result(self, block_id, action_id, json_str):
        fn = self.action_dir(block_id, action_id) / "result.json"
        with open(fn, "w") as f:
            f.write(json_str)

        loaded_block_id, loaded_action_id, loaded_result = Result.from_json(self, json_str)
        

        assert loaded_action_id == action_id
        assert loaded_block_id == block_id

        self.results[(block_id, action_id)] = loaded_result

    def reload_results(self):
        self.results = {}
        for fn in self.build_dir.glob("*/*/result.json"):
            with open(fn, "r") as f:
                json_str = f.read()
            block_id, action_id, res = Result.from_json(self, json_str)
            self.results[(block_id, action_id)] = res

    def get_result(self, result_id):
        try:
            return self.results[result_id]
        except KeyError:
            raise FlowError(f"Required result {result_id} not found.")