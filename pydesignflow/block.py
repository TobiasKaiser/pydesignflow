from pathlib import Path
import json

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
            print(block_id, action_id, res)
            self.results[(block_id, action_id)] = res

    def get(self, block_id, action_id):
        return self.results[(block_id, action_id)]

class Action:
    def __init__(self, func, requires):
        self.func = func
        self.requires = requires

    def resolve_require(self, require, block_id_self, dependency_map):
        require_split = require.split(".")
        if len(require_split) == 1:
            # requirement within block
            action_id = require_split[0]
            block_id = block_id_self
            return (block_id, action_id)
        elif len(require_split) == 2:
            block_refstr = require_split[0]
            block_id = dependency_map[block_refstr]
            action_id = require_split[1]
            return (block_id, action_id)
        else:
            raise ValueError(f"Dependency spec \"{require}\" has more than one '.'")

    def resolve_requires(self, block_id, dependency_map):
        """
        Returns map of str to (block_id, action_id).
        """
        res = {}
        for k, v in self.requires.items():
            res[k] = self.resolve_require(v, block_id, dependency_map)
        return res

    def dependency_kwargs(self, block_id, dependency_map, build_dir):
        rescol = ResultCollection()
        rescol.load_all_results(build_dir)

        kwargs = {}
        for key, (block_id, action_id) in self.resolve_requires(block_id, dependency_map).items():
            kwargs[key] = rescol.get(block_id, action_id)
        return kwargs

    def run(self, block, build_dir, block_id, action_id, dependency_map):
        cwd = build_dir / block_id / action_id

        cwd.mkdir(parents=True, exist_ok=True)

        kwargs = self.dependency_kwargs(block_id, dependency_map, build_dir)
        print(kwargs)

        res = self.func(block, cwd, **kwargs)
        if res != None:
            res.write_json(block_id, action_id, cwd / "result.json", build_dir)
        


def action(requires={}):
    return lambda func: Action(func, requires)

class Block():
    def __init__(self, dependency_map={}):
        self.actions={}
        self.auto_register_actions()
        self.dependency_map=dependency_map # Maps block reference strings to block IDs

    def auto_register_actions(self):
        """
        Registers all Action objects in the .actions dictionary.

        Alternately, a similar automatic detection can be implemented using a
        metaclass and __prepare__ (see source code).
        """
        for key in dir(self):
            val = getattr(self, key)
            if isinstance(val, Action):
                self.actions[key] = val

    def populate_subparser(self, subparser):
        subparser.add_argument("action", choices=self.actions.keys())
        subparser.set_defaults(func=self.run_action)

    def run_action(self, args, build_dir):
        block_id = args.block
        action_id = args.action
        self.actions[action_id].run(self, build_dir, block_id, action_id, self.dependency_map)