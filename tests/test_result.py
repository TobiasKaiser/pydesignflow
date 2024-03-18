# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

from pydesignflow import Flow, Block, task, Result
from pathlib import Path
from datetime import datetime
import json

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