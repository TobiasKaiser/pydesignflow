from .result import Result
from .errors import FlowError, ResultRequired
import shutil
from .block import TargetId
import tabulate
tabulate.PRESERVE_WHITESPACE = True

class BuildSession:

    def __init__(self, flow, build_dir):
        self.flow = flow
        self.build_dir = build_dir
        self.results = None # (block_id, task_id) -> Result map
        self.reload_results()

    def run_task(self, block_id, task_id, build_requirements=None):
        """
        Args:
            build_requirements: None, "missing" or "all"
        """
        task = self.flow.task(TargetId(block_id, task_id))
        task.run(self)
    
    def task_dir(self, block_id, task_id):
        return self.build_dir / block_id / task_id

    def write_result(self, block_id, task_id, json_str):
        fn = self.task_dir(block_id, task_id) / "result.json"
        with open(fn, "w") as f:
            f.write(json_str)

        loaded_block_id, loaded_task_id, loaded_result = Result.from_json(self, json_str)
        

        assert loaded_task_id == task_id
        assert loaded_block_id == block_id

        self.results[(block_id, task_id)] = loaded_result

    def reload_results(self):
        self.results = {}
        for fn in self.build_dir.glob("*/*/result.json"):
            with open(fn, "r") as f:
                json_str = f.read()
            block_id, task_id, res = Result.from_json(self, json_str)
            self.results[(block_id, task_id)] = res

    def get_result(self, result_id):
        try:
            return self.results[result_id]
        except KeyError:
            raise ResultRequired(result_id)

    def clean(self, block_id:str=None, task_id:str=None):
        """
        If block_id and task_id are given, only the specified result is deleted.
        If only block_id is given, results of all tasks of that block are deleted.
        If neither block_id nor task_id are given, all results of all block are deleted. 
        """
        for i in block_id, task_id:
            # Very primitive sanity check:
            if not i:
                continue
            assert i.find("..") < 0
            assert i.find("/") < 0

        if block_id and task_id:
            shutil.rmtree(self.build_dir / block_id / task_id, ignore_errors=True)
        elif block_id:
            shutil.rmtree(self.build_dir / block_id, ignore_errors=True)
        else:
            assert not task_id
            # Remote all results
            shutil.rmtree(self.build_dir, ignore_errors=True)
        self.reload_results()

    def status_block(self, block_id:str):
        block = self.flow[block_id]
        for task_id in block.tasks:
            result_id = TargetId(block_id, task_id)
            try:
                r=self.get_result(result_id)
                yield block_id, task_id, r.summary()
            except ResultRequired:
                yield block_id, task_id, "not found"

    def format_status(self, status_list):
        table = [["Target", "Status"]]
        block_id_last = None
        for block_id, task_id, status in status_list:
            if block_id_last != block_id:
                table.append([block_id, ""])
                block_id_last = block_id
            table.append([f"  {task_id}", status])
        return tabulate.tabulate(table, headers="firstrow", tablefmt="simple", colalign="r")


    def status(self, block_id:str=None) -> str:
        """
        Args:
            block_id: Display only status for requested block. If block_id is
                None, status of all blocks will be listed.
        """
        if block_id:
            status_list = list(self.status_block(block_id))
        else:
            status_list = []
            for block_id in self.flow:
                status_list += list(self.status_block(block_id))
        return self.format_status(status_list)