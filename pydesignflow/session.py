import shutil
import tabulate
import re

from .result import Result
from .errors import FlowError, ResultRequired
from .target import TargetId

tabulate.PRESERVE_WHITESPACE = True

def compact_docstr(docstr: str, maxlen=30, ellipsis="...") -> str:
    """
    Removes newlines and indentation from docstring and cuts off excess text
    if maxlen characters are exceeded.
    """
    if not docstr:
        return ""
    docstr = re.sub("[ \t\n]+", " ", docstr)
    if len(docstr) > maxlen:
        docstr = docstr[:maxlen-len(ellipsis)] + ellipsis
    return docstr

class BuildSession:

    def __init__(self, flow, build_dir):
        self.flow = flow
        self.build_dir = build_dir
        self.results = None # (block_id, task_id) -> Result map
        self.reload_results()

    def plan_run(self, block_id, task_id, build_requirements=None) -> list[TargetId]:
        assert build_requirements in (None, "missing", "all")
        requested_tid = TargetId(block_id, task_id)
        rebuild = (build_requirements == "all")
        deplist = self.dependency_list(requested_tid, rebuild)
        if not build_requirements:
            # If build_requirements is None, we do not want to build anything
            # other than always_rebuild targets and the requested target.
            for dep_tid in deplist:
                if dep_tid == requested_tid:
                    continue
                target = self.flow.target(dep_tid)
                if target.always_rebuild:
                    continue
                raise ResultRequired(dep_tid)
        return deplist

    def print_plan(self, plan: list[TargetId]):
        print("Planned execution:")
        table = [['Idx', 'Block', 'Task']]
        for idx, dep in enumerate(plan):
            table.append([idx, dep.block_id, dep.task_id])
        print(tabulate.tabulate(table, headers="firstrow", tablefmt="simple"))
        print()

    def run(self, block_id, task_id, build_requirements=None, dry_run=False, verbose=False):
        """
        Args:
            build_requirements: None, "missing" or "all"
        """
        plan = self.plan_run(block_id, task_id, build_requirements)
        
        if verbose:
            self.print_plan(plan)

        if dry_run:
            return

        for tid in plan:
            if verbose:
                print(f"Running target {tid.block_id}.{tid.task_id}.")
            target = self.flow.target(tid)
            target.run(self)
            if verbose:
                print(f"Target {tid.block_id}.{tid.task_id} completed.")
                print()


    run_target = run # For compatibility - remove this at some point.

    def dependency_list(self, tid: TargetId, rebuild:bool) -> list[TargetId]:
        """
        Returns list of dependencies of target tid, including tid.
        Performs topological sorting by depth-first search.
        Args:
            tid: target_id. Will not be included in output list.
            rebuild: Set to True to rebuild targets that are already present.
        """
        # See https://guides.codepath.com/compsci/Topological-Sort

        topo_order = []
        visited = set()
        def dfs(tid):
            visited.add(tid)
            target =  self.flow.target(tid)
            for neighbor_tid in target.missing_requires(self, rebuild=rebuild):
                if not (neighbor_tid in visited):
                    dfs(neighbor_tid)
            topo_order.append(tid)
        dfs(tid)
        return topo_order
    
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
        yield [block_id, "", compact_docstr(block.__doc__)]
        for task_id in block.tasks:
            tid = TargetId(block_id, task_id)
            target = self.flow.target(tid)
            if tid in self.results:
                res=self.get_result(tid)
                status=res.summary()
            else:
                expected_dir = self.build_dir / block_id / task_id
                if expected_dir.exists():
                    status="dir without result -> running or failed"
                else:
                    status="not found"
            yield [f"  {task_id}",  status, compact_docstr(target.__doc__)]
        
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
        
        header = [["Target", "Status", "Help"]]
        table = header + status_list        
        return tabulate.tabulate(table, headers="firstrow", tablefmt="simple")