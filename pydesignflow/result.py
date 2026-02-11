# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import json
from datetime import datetime

class Result:
    """
    Container for task output data.

    Result objects store structured data returned by tasks. Each task can return at most
    one Result, which is serialized to JSON (result.json) in the task's output directory.
    Results from dependency tasks are passed as parameters to dependent tasks.

    Attributes can be assigned dynamically and support common Python types: str, bool, int,
    float, Path, datetime, as well as lists and dictionaries containing these types.

    Example of creating and returning a Result::

        result = Result()
        result.timing_met = True
        result.netlist = cwd / "output.v"
        result.area = 1234
        result.metrics = {'delay': 5.2, 'power': 0.8}
        return result

    Tasks can access the results of their dependencies, example::

        @task(requires={'syn': '.synthesize'})
        def place_route(self, cwd, syn):
            if syn.timing_met:
                print(f"Using netlist: {syn.netlist}")
                print(f"Area: {syn.area}")
    """
    supported_scalar_types = (
        str, bool, int, float, Path, datetime
    )

    def __init__(self):
        """Initialize an empty Result object."""
        self.__dict__["attrs"] = {}

    def check_value(self, value):
        if isinstance(value, (list, tuple)):
            for elem in value:
                self.check_value(elem)
        elif isinstance(value, dict):
            for k, v in value.items():
                if not isinstance(k, str):
                    raise ValueError(f"Attribute dict keys must be str.")
                self.check_value(v)
        elif not isinstance(value, self.supported_scalar_types):
            raise ValueError(f"Unsupported attribute type: {value}")

    def __setattr__(self, key, value):
        self.check_value(value)
        self.attrs[key]=value

    def __getattr__(self, key):
        return self.attrs[key]

    def json(self, sess, block_id, task_id) -> str:
        def default(obj):
            if isinstance(obj, Path):
                if sess.build_dir in obj.parents:
                    obj = obj.relative_to(sess.build_dir)
                return {"_type":"Path","value":str(obj)}
            elif isinstance(obj, datetime):
                return {"_type":"Time","value":obj.timestamp()}
            else:
                return super().default(obj)
                
        e = json.JSONEncoder(indent=2, default=default)
        return e.encode({
            "block_id":  block_id,
            "task_id": task_id,
            "data":      self.attrs,
        })

    @classmethod
    def from_json(self, sess, json_str):
        def object_hook(obj):
            if not "_type" in obj:
                return obj
            t = obj["_type"]
            if t == "Path":
                return sess.build_dir / Path(obj["value"])
            elif t == "Time":
                return datetime.fromtimestamp(obj["value"])

        result_json = json.loads(json_str, object_hook=object_hook)
        
        assert set(result_json.keys()) == set(("block_id", "task_id", "data"))

        block_id  = result_json["block_id"]
        task_id = result_json["task_id"]
        attrs     = result_json["data"]
        
        res = Result()
        for k, v in attrs.items():
            res.attrs[k] = v

        return block_id, task_id, res

    def __repr__(self):
        return f"<Result {self.attrs}>"

    def summary(self) -> str:
        """Returns textual summary of result for status table.

        Returns:
            str: e.g. "finished 10:17 in 13m"."""
        finished = self.time_finished
        if finished.date() == datetime.today().date():
            finished_str = f"{finished:%H:%M}"
        else:
            finished_str = f"{finished:%y-%m-%d}"
        duration_sec = (self.time_finished - self.time_started).total_seconds()
        duration_sec = int(duration_sec)
        if duration_sec > 60:
            duration_str = f"{int(duration_sec//60)}m"
        else:
            duration_str = f"{duration_sec%60}s"
        r=f"✓ {finished_str} in {duration_str}"
        return r
