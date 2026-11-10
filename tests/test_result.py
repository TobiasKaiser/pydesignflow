# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

from pydesignflow import Flow, Block, task, Result, PickledValue, TargetId
from pathlib import Path
from datetime import datetime
import json
import pytest

class MyBlock(Block):
    @task()
    def syn(self, cwd):
        syn = Result()
        syn.str_attrib = "asdf"
        syn.dict_attrib = {'hello': 'world', 'number': 100, 'nested': [1, 2, 'test']}
        syn.int_attrib = 123
        syn.float_attrib = 11.22
        syn.bool_true = True
        syn.bool_false = False
        syn.path_test = cwd / Path("whats") / Path("up")
        syn.date_test = datetime(year=1900, month=1, day=1)
        return syn

def get_flow_session(build_dir):
    flow = Flow()
    flow['top'] = MyBlock()
    
    return flow.session_at(build_dir)

def test_json_file(tmp_path):
    sess = get_flow_session(tmp_path)

    sess.plan('top', 'syn').run()
    with open(sess.build_dir / 'top/syn/result.json') as f:
        json_str = f.read()
        block_id, task_id, result = Result.from_json(sess, json_str)

    assert block_id == 'top'
    assert task_id == 'syn'
    assert result.str_attrib == "asdf"
    assert result.dict_attrib == {'hello': 'world', 'number': 100, 'nested': [1, 2, 'test']}
    assert result.int_attrib == 123
    assert result.float_attrib == 11.22
    assert result.bool_true == True
    assert result.bool_false == False
    assert result.path_test == tmp_path / Path("top/syn/whats/up")
    assert result.date_test == datetime(year=1900, month=1, day=1)

class Payload:
    def __init__(self, value):
        self.value = value

class PickleBlock(Block):
    @task()
    def syn(self, cwd):
        syn = Result()
        syn.obj = Payload(42)
        syn.nested = {'set': {1, 2}, 'list': [Payload(1)]}
        syn.mutated = Payload(1)
        syn.mutated.value = 2
        syn.none_attrib = None
        syn.int_attrib = 123
        return syn

    @task(requires={'syn': '.syn'})
    def copy(self, cwd, syn):
        res = Result()
        res.nested = syn.nested
        return res

def get_pickle_session(build_dir, allow_unpickle):
    flow = Flow(allow_unpickle=allow_unpickle)
    flow['top'] = PickleBlock()
    return flow.session_at(build_dir)

def test_pickle_roundtrip(tmp_path):
    sess = get_pickle_session(tmp_path, allow_unpickle=True)
    sess.plan('top', 'syn').run()

    result_json = json.loads((sess.build_dir / 'top/syn/result.json').read_text())
    assert result_json['data']['obj']['_type'] == 'Pickle'
    assert result_json['data']['none_attrib'] is None

    sess = get_pickle_session(tmp_path, allow_unpickle=True)
    result = sess.get_result(TargetId('top', 'syn'))
    assert isinstance(result.obj, Payload)
    assert result.obj.value == 42
    assert result.nested['set'] == {1, 2}
    assert result.nested['list'][0].value == 1
    assert result.mutated.value == 2
    assert result.none_attrib is None
    assert result.int_attrib == 123

def test_pickle_placeholder(tmp_path):
    # Writing pickled values works without allow_unpickle.
    sess = get_pickle_session(tmp_path, allow_unpickle=False)
    sess.plan('top', 'syn').run()

    sess = get_pickle_session(tmp_path, allow_unpickle=False)
    result = sess.get_result(TargetId('top', 'syn'))
    assert result.int_attrib == 123
    with pytest.raises(ValueError, match="'obj'.*allow_unpickle=True"):
        result.obj
    assert isinstance(result.attrs['obj'], PickledValue)
    assert isinstance(result.nested['set'], PickledValue)

def test_pickle_placeholder_passed_on(tmp_path):
    # Placeholders are written back unchanged and can be unpickled later.
    sess = get_pickle_session(tmp_path, allow_unpickle=False)
    sess.plan('top', 'copy', build_dependencies='missing').run()

    sess = get_pickle_session(tmp_path, allow_unpickle=True)
    result = sess.get_result(TargetId('top', 'copy'))
    assert result.nested['set'] == {1, 2}
    assert result.nested['list'][0].value == 1

class BadBlock(Block):
    @task()
    def unpicklable(self, cwd):
        res = Result()
        res.metrics = {'fn': [1, lambda: None]}
        return res

    @task()
    def int_key(self, cwd):
        res = Result()
        res.metrics = {'inner': {1: 'a'}}
        return res

def test_unpicklable_value(tmp_path):
    flow = Flow()
    flow['top'] = BadBlock()
    sess = flow.session_at(tmp_path)
    with pytest.raises(ValueError, match=r"metrics\['fn'\]\[1\] of top.unpicklable could not be pickled"):
        sess.plan('top', 'unpicklable').run()
    assert not (tmp_path / 'top/unpicklable/result.json').exists()

def test_non_str_dict_key(tmp_path):
    flow = Flow()
    flow['top'] = BadBlock()
    sess = flow.session_at(tmp_path)
    with pytest.raises(ValueError, match=r"metrics\['inner'\] of top.int_key: dict keys must be str, got 1"):
        sess.plan('top', 'int_key').run()
