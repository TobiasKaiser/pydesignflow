import pytest
from .. import Block, ResultId, Flow, action, Result, ResultRequired

class BlockA(Block):
    @action()
    def stepX(self, cwd):
        r = Result()
        r.my_key = "A.X res"
        return r

    @action(requires={'x':'.stepX'})
    def stepY(self, cwd, x):
        r = Result()
        r.my_key = f"A.Y res ({x.my_key})"
        return r

class BlockB(Block):
    """
    Test block reference by-ID.
    """

    @action(requires={'y':'=A1.stepY'})
    def stepZ(self, cwd, y):
        r = Result()
        r.my_key = f"B.Z res ({y.my_key})"
        return r

class BlockC(Block):
    """
    Tests block reference through dependency map.
    """

    @action(requires={'y':'a.stepY'})
    def stepZ(self, cwd, y):
        r = Result()
        r.my_key = f"B.Z res ({y.my_key})"
        return r


class BlockD(Block):
    """
    Like BlockA, but can be customized with argument parameter to __init__.
    """
    def __init__(self, argument, **kwargs):
        super().__init__(**kwargs)
        self.argument = argument

    @action()
    def stepX(self, cwd):
        r = Result()
        r.my_key = f"D[{self.argument}].X res"
        return r


class BlockE(Block):
    """
    Tests block reference through dependency map.
    """

    @action(requires={'x':'r.stepX'})
    def stepY(self, cwd, x):
        r = Result()
        r.my_key = f"E.Y res ({x.my_key})"
        return r

    @action(requires={'xr':'r.stepX', 'xg':'g.stepX', 'xb':'b.stepX'})
    def stepZ(self, cwd, xr, xg, xb):
        r = Result()
        r.my_key = f"E.Z res ({xr.my_key}, {xg.my_key}, {xb.my_key})"
        return r

def get_flow_session(build_dir):
    flow = Flow()
    flow['A1'] = BlockA()
    flow['A2'] = BlockA()
    flow['B1'] = BlockB() 
    flow['C1'] = BlockC(dependency_map={"a":"A1"}) 
    
    flow['D1'] = BlockD("red")
    flow['D2'] = BlockD("green") 
    flow['D3'] = BlockD("blue")
    flow['E1'] = BlockE(dependency_map={"r":"D1", "g":"D2", "b":"D3"}) 

    return flow.session_at(build_dir)

def test_a1_b1(tmp_path):
    sess = get_flow_session(tmp_path)
    
    plan = [
        ("A1", "stepX"),
        ("A1", "stepY"),
        ("B1", "stepZ"),
    ]

    for block_id, action_id in plan:
        sess.run_action(block_id, action_id)
        assert (sess.build_dir / block_id / action_id / 'result.json').exists()
    
    res = sess.get_result(ResultId('B1', 'stepZ')).my_key
    assert res == "B.Z res (A.Y res (A.X res))"

def test_a1_c1(tmp_path):
    sess = get_flow_session(tmp_path)
    
    plan = [
        ("A1", "stepX"),
        ("A1", "stepY"),
        ("C1", "stepZ"),
    ]

    for block_id, action_id in plan:
        sess.run_action(block_id, action_id)
        assert (sess.build_dir / block_id / action_id / 'result.json').exists()
    
    res = sess.get_result(ResultId('C1', 'stepZ')).my_key
    assert res == "B.Z res (A.Y res (A.X res))"


def test_d_e(tmp_path):
    sess = get_flow_session(tmp_path)
    
    plan = [
        ("D1", "stepX"),
        ("D2", "stepX"),
        ("D3", "stepX"),
        ("E1", "stepY"),
        ("E1", "stepZ"),
    ]

    for block_id, action_id in plan:
        sess.run_action(block_id, action_id)
        assert (sess.build_dir / block_id / action_id / 'result.json').exists()
    
    res = sess.get_result(ResultId('E1', 'stepY')).my_key
    assert res == "E.Y res (D[red].X res)"

    res = sess.get_result(ResultId('E1', 'stepZ')).my_key
    assert res == "E.Z res (D[red].X res, D[green].X res, D[blue].X res)"