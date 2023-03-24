import shutil
import tabulate
import re
from typing import Literal

from .result import Result
from .errors import FlowError, ResultRequired
from .target import TargetId
from .ansiterm import ANSITerm

tabulate.PRESERVE_WHITESPACE = True

def compact_docstr(docstr: str, maxlen=40, ellipsis="...") -> str:
    """
    Removes newlines and indentation from docstring and cuts off excess text
    if maxlen characters are exceeded.
    """
    if not docstr:
        return ""
    docstr = re.sub("[ \t\n]+", " ", docstr)
    docstr = docstr.strip() # Remove leading and trailing spaces.
    if len(docstr) > maxlen:
        docstr = docstr[:maxlen-len(ellipsis)] + ellipsis
    return docstr

class BuildPlan:
    def __init__(self, sess, main_target: TargetId, target_sequence: list[TargetId]):
        self.sess = sess
        self.target_sequence = target_sequence
        self.main_target = main_target

    def missing_targets(self) -> bool:
        """
        Returns True if BuildPlan contains targets that are not the main_target
        and are not marked as always rebuild.
        """
        def is_missing(tid):
            if tid == self.main_target:
                return False
            target = self.sess.flow.target(tid)
            if target.always_rebuild:
                return False
            return True

        return list(filter(is_missing, self.target_sequence))

    def __repr__(self):
        status_list = [f" ‣ {tid.block_id}.{tid.task_id}" for tid in self.target_sequence] 
        return "\n".join(status_list)

    def run(self):
        style = ANSITerm.FgBrightBlue
        reset = ANSITerm.Reset
        for tid in self.target_sequence:
            print(f"{style}[PyDesignFlow]{reset} Running target {tid.block_id}.{tid.task_id}.")
            target = self.sess.flow.target(tid)
            target.run(self.sess)
            print(f"{style}[PyDesignFlow]{reset} Finished target {tid.block_id}.{tid.task_id}.")


class BuildSession:

    def __init__(self, flow, build_dir):
        self.flow = flow
        self.build_dir = build_dir
        self.results = None # (block_id, task_id) -> Result map
        self.reload_results()

    def plan(self, block_id, task_id, build_dependencies:Literal[None, 'missing', 'all']=None) -> BuildPlan:
        """
        Args:
            build_dependencies: None, "missing" or "all"
        """
        assert build_dependencies in (None, "missing", "all")
        requested_tid = TargetId(block_id, task_id)
        rebuild = (build_dependencies == "all")
        target_list = self._dependency_list(requested_tid, rebuild)
        plan = BuildPlan(self, requested_tid, target_list)
        missing = plan.missing_targets()
        if (not build_dependencies) and len(missing) > 0:
            raise ResultRequired(missing[0])
        return plan

    def _dependency_list(self, tid: TargetId, rebuild:bool) -> list[TargetId]:
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

        self.results[TargetId(block_id, task_id)] = loaded_result

    def reload_results(self):
        self.results = {}
        for fn in self.build_dir.glob("*/*/result.json"):
            with open(fn, "r") as f:
                json_str = f.read()
            block_id, task_id, res = Result.from_json(self, json_str)
            self.results[TargetId(block_id, task_id)] = res

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

    def status_block(self, block_id:str, show_hidden:bool=True, show_targets:bool=False):
        block = self.flow[block_id]
        yield [ANSITerm.FgBlue+block_id+ANSITerm.Reset, "",
            ANSITerm.FgBlue+compact_docstr(block.__doc__)+ANSITerm.Reset]
        for task_id, task in block.tasks.items():
            tid = TargetId(block_id, task_id)
            target = self.flow.target(tid)
            if tid in self.results:
                if (not show_hidden) and task.hidden and task.always_rebuild:
                    continue
                res=self.get_result(tid)
                status=res.summary()
                status = ANSITerm.FgGreen + status + ANSITerm.Reset
            else:
                if not show_targets:
                    continue
                expected_dir = self.build_dir / block_id / task_id
                if expected_dir.exists():
                    status =  ANSITerm.FgYellow + "incomplete" + ANSITerm.Reset
                else:
                    if (not show_hidden) and task.hidden:
                        continue
                    status = ""
                    #status = ANSITerm.FgRed + "not found" + ANSITerm.Reset
            yield [f"  .{task_id}",  status, compact_docstr(target.__doc__)]
        
    def status(self, block_id:str, show_hidden:bool) -> str:
        """
        Args:
            block_id: Display only status for requested block. If block_id is
                None, status of all blocks will be listed.
        """
        if block_id:
            status_list = list(self.status_block(block_id, show_hidden=True, show_targets=True))
        else:
            status_list = []
            for block_id in self.flow:
                status_list += list(self.status_block(block_id, show_targets=show_hidden, show_hidden=False))
        
        header = [["Target", "Status", "Help"]]
        table = header + status_list
        return tabulate.tabulate(table, headers="firstrow", tablefmt="simple")