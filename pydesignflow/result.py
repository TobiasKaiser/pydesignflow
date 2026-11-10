# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import json
from datetime import datetime
import pickle
import base64

class Result:
    """
    Container for task output data.

    Result objects store structured data returned by tasks. Each task can return at most
    one Result, which is serialized to JSON (result.json) in the task's output directory.
    Results from dependency tasks are passed as parameters to dependent tasks.

    Attributes can be assigned dynamically. The common Python types str, bool, int, float,
    None, Path and datetime, as well as lists and dictionaries containing these types, are
    stored as JSON. Values of any other type are stored via pickle. Pickled values are
    only unpickled if the Flow was created with allow_unpickle=True, otherwise they are
    loaded as PickledValue placeholders.

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
    def __init__(self):
        """Initialize an empty Result object."""
        self.__dict__["attrs"] = {}

    def __setattr__(self, key, value):
        self.attrs[key]=value

    def __getattr__(self, key):
        value = self.attrs[key]
        if isinstance(value, PickledValue):
            raise ValueError(f"Result attribute '{key}' contains pickled data, "
                "but unpickling is disabled. Pass allow_unpickle=True to Flow "
                "to load it.")
        return value

    def json(self, sess, block_id, task_id) -> str:
        # Values are checked during serialization instead of on assignment.
        # This way, each value is pickled only once, and changes made to a
        # value after its assignment are included in result.json.
        def encode(value, path):
            if isinstance(value, (str, bool, int, float, type(None))):
                return value
            elif isinstance(value, Path):
                if sess.build_dir in value.parents:
                    value = value.relative_to(sess.build_dir)
                return {"_type":"Path","value":str(value)}
            elif isinstance(value, datetime):
                return {"_type":"Time","value":value.timestamp()}
            elif isinstance(value, (list, tuple)):
                return [encode(v, f"{path}[{i}]") for i, v in enumerate(value)]
            elif isinstance(value, dict):
                ret = {}
                for k, v in value.items():
                    if not isinstance(k, str):
                        raise ValueError(f"Result attribute {path} of "
                            f"{block_id}.{task_id}: dict keys must be str, "
                            f"got {k!r}.")
                    ret[k] = encode(v, f"{path}[{k!r}]")
                return ret
            elif isinstance(value, PickledValue):
                # Not unpickled when loaded, pass on unchanged.
                return {"_type":"Pickle","value":value.data}
            else:
                try:
                    data = pickle.dumps(value)
                except Exception as e:
                    raise ValueError(f"Result attribute {path} of "
                        f"{block_id}.{task_id} could not be pickled: {e}") from e
                return {"_type":"Pickle","value":base64.b64encode(data).decode("ascii")}

        return json.dumps({
            "block_id":  block_id,
            "task_id": task_id,
            "data":      {k: encode(v, k) for k, v in self.attrs.items()},
        }, indent=2)

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
            elif t == "Pickle":
                # Unpickling can execute arbitrary code, therefore it must be
                # enabled explicitly.
                if sess.flow.allow_unpickle:
                    return pickle.loads(base64.b64decode(obj["value"]))
                else:
                    return PickledValue(obj["value"])

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

class PickledValue:
    """
    Placeholder for a pickled Result value that was not unpickled, because
    the Flow was created with allow_unpickle=False.

    Accessing a Result attribute that holds a PickledValue raises a ValueError.
    PickledValues nested inside lists or dicts are returned as they are.
    """

    def __init__(self, data: str):
        #: Base64-encoded pickle data.
        self.data = data

    def __repr__(self):
        return "<PickledValue (unpickling disabled)>"
