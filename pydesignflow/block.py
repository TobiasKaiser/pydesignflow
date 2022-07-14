from pathlib import Path
import json
import re

from .errors import FlowError
from collections import namedtuple

ResultId = namedtuple('ResultId', ('block_id', 'action_id'))

class Result:
    def __init__(self):
        self.__dict__["attrs"] = {}


    def __setattr__(self, key, value):
        #if key == "attrs":
        #    object.__setattr__(self, key, value)
        self.attrs[key]=value
        #print(f"result {key}={value}")

    def __getattr__(self, key):
        return self.attrs[key]

    def write_json(self, block_id, action_id, filename, build_dir):
        def default(obj):
            if isinstance(obj, Path):
                if build_dir in obj.parents:
                    obj = obj.relative_to(build_dir)
                return {"_type":"Path","value":str(obj)}
            else:
                return super().default(obj)
                
        s = json.JSONEncoder(indent=2, default=default).encode({
            "block_id":block_id,
            "action_id":action_id,
            "data":self.attrs,
        })
        with open(filename, "w") as f:
            f.write(s)

    @classmethod
    def from_json(self, filename, build_dir):
        def object_hook(obj):
            if not "_type" in obj:
                return obj
            t = obj["_type"]
            if t == "Path":
                return build_dir / Path(obj["value"])

        with open(filename, "r") as f:
            result_json = json.load(f, object_hook=object_hook)
        block_id = result_json["block_id"]
        action_id = result_json["action_id"]
        
        res = Result()
        for k, v in result_json["data"].items():
            res.attrs[k] = v

        return block_id, action_id, res

    def __repr__(self):
        return f"<Result {self.attrs}>"

class  ResultCollection:
    def __init__(self):
        self.results = {} # (block_id, action_id) -> Result map

    def load_all_results(self, build_dir):
        for fn in build_dir.glob("*/*/result.json"):
            block_id, action_id, res = Result.from_json(fn, build_dir)
            #print(block_id, action_id, res)
            self.results[(block_id, action_id)] = res

    def get(self, result_id):
        try:
            return self.results[result_id]
        except KeyError:
            raise FlowError(f"Required result {result_id} not found.")

def parse_requirement_spec(spec):
    m = re.match(r"((=)?([a-zA-Z0-9_]+))?\.([a-zA-Z0-9_]+)", spec)
    if not m:
        raise ValueError(f"Malformed requirement spec \"{spec}\".")
    action_id = m.group(4)
    is_direct_ref = bool(m.group(2))
    block_ref = m.group(3)

    return is_direct_ref, block_ref, action_id

class Action:
    def __init__(self, func, requires):
        self.func = func
        self.requires = requires
        self.block = None
        self.id = None
        self._registered = False

    def register(self, block, action_id):
        """
        Called by Block
        """
        if self._registered:
            raise FlowError(f"Attempt to register {self} multiple times.")
        self.block = block
        self.id = action_id

    def parse_requires(self):
        for k, v in self.requires.items():
            is_direct_ref, block_ref, action_id = parse_requirement_spec(v)
            yield k, is_direct_ref, block_ref, action_id
        
    def resolve_requires(self, block_id_self):
        for key, is_direct_ref, block_ref, action_id in self.parse_requires():
            if is_direct_ref:
                block_id = block_ref
            elif block_ref:
                block_id = self.block.dependency_map[block_ref]
            else:
                block_id = block_id_self

            yield key, ResultId(block_id, action_id)    

    def dependency_kwargs(self, block_id_self, build_dir):
        rescol = ResultCollection()
        rescol.load_all_results(build_dir)

        kwargs = {}
        for key, result_id in self.resolve_requires(block_id_self):
            kwargs[key] = rescol.get(result_id)
        return kwargs

    def run(self, build_dir):
        cwd = build_dir / self.block.id / self.id 

        cwd.mkdir(parents=True, exist_ok=True)

        kwargs = self.dependency_kwargs(self.block.id, build_dir)

        res = self.func(self.block, cwd, **kwargs)
        if res != None:
            res.write_json(self.block.id, self.id, cwd / "result.json", build_dir)
        

def action(requires={}):
    return lambda func: Action(func, requires)

class Block():
    def __init__(self, dependency_map={}):
        """
        Args:
            dependecy_map: Dict mapping  block reference strings to block IDs.
                Keys of this dictionary must exactly match the blocks referenced.
        """
        self.actions={}
        self.block_references = set()
        self.auto_register_actions()
        self.id = None
        self._registered = False

        if set(dependency_map.keys()) != self.get_all_block_refs():
            raise ValueError(f"dependency_map must declare exactly "
                f"the following block references: {self.block_references}")

        self.dependency_map=dependency_map

    def register(self, flow, block_id):
        """
        Called by Flow
        """
        if self._registered:
            raise FlowError(f"Attempt to register {self} multiple times.")
        self.id = block_id
        self.flow = flow
        self._registered = True

    def auto_register_actions(self):
        """
        Registers all Action objects in the .actions dictionary.

        Alternately, a similar automatic detection can be implemented using a
        metaclass and __prepare__.
        """
        for key in dir(self):
            val = getattr(self, key)
            if isinstance(val, Action):
                # Bidirectional reference:
                val.register(self, key)
                self.actions[key] = val

    def get_all_block_refs(self):
        block_refs = set()
        for action in self.actions.values():
            for _, is_direct_ref, block_ref, _ in action.parse_requires():
                if not is_direct_ref and block_ref:
                    block_refs.add(block_ref)
        return block_refs

    #def populate_subparser(self, subparser):
    #    subparser.add_argument("action", choices=self.actions.keys())
    #    subparser.set_defaults(func=self.run_action)
    
    #def run_action(self, args, build_dir):
    #    block_id = args.block
    #    action_id = args.action
    #    self.actions[action_id].run(self, build_dir, block_id, action_id, self.dependency_map)