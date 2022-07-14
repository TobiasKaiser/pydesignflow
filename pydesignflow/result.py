from pathlib import Path
import json

class Result:
    supported_scalar_types = (
        Path, str
    )

    def __init__(self):
        self.__dict__["attrs"] = {}

    def check_value(self, value):
        if isinstance(value, (list, tuple)):
            for elem in list:
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

    def json(self, sess, block_id, action_id) -> str:
        def default(obj):
            if isinstance(obj, Path):
                if sess.build_dir in obj.parents:
                    obj = obj.relative_to(sess.build_dir)
                return {"_type":"Path","value":str(obj)}
            else:
                return super().default(obj)
                
        e = json.JSONEncoder(indent=2, default=default)
        return e.encode({
            "block_id":  block_id,
            "action_id": action_id,
            "data":      self.attrs,
        })

    @classmethod
    def from_json(self, sess, json_str):
        def object_hook(obj):
            if not "_type" in obj:
                return obj
            t = obj["_type"]
            if t == "Path":
                return build_dir / Path(obj["value"])

        result_json = json.loads(json_str, object_hook=object_hook)
        
        assert set(result_json.keys()) == set(("block_id", "action_id", "data"))

        block_id  = result_json["block_id"]
        action_id = result_json["action_id"]
        attrs     = result_json["data"]
        
        res = Result()
        for k, v in attrs.items():
            res.attrs[k] = v

        return block_id, action_id, res

    def __repr__(self):
        return f"<Result {self.attrs}>"
