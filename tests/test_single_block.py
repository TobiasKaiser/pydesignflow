import pytest
from pydesignflow import TargetId, ResultRequired

def get_flow_session(build_dir):
    from .flow_example1 import flow
    return flow.session_at(build_dir)

def test_step1_creates_result(tmp_path):
    sess = get_flow_session(tmp_path)
    task_id = 'step1'
    sess.plan('top', task_id).run()
    assert (sess.build_dir / 'top' / task_id / 'result.json').exists()

def test_step_without_result(tmp_path):
    sess = get_flow_session(tmp_path)
    task_id = 'step_without_result'
    sess.plan('top', task_id).run()
    # In an earlier version, tasks without a result would not create a result.json file.
    assert (sess.build_dir / 'top' / task_id / 'result.json').exists()

def test_step1_step2(tmp_path):
    sess = get_flow_session(tmp_path)
    sess.plan('top', 'step1').run()
    sess.plan('top', 'step2').run()
    assert (sess.build_dir / 'top' / 'step1' / 'result.json').exists()
    assert (sess.build_dir / 'top' / 'step2' / 'result.json').exists()

def test_step123(tmp_path):
    sess = get_flow_session(tmp_path)
    for i in range(1, 1+3):
        task_id = f'step{i}'
        sess.plan('top', task_id).run()
        assert (sess.build_dir / 'top' / task_id / 'result.json').exists()
    
def test_run_all(tmp_path):
    sess = get_flow_session(tmp_path)
    for i in range(1, 1+10):
        task_id = f'step{i}'
        sess.plan('top', task_id).run()
        assert (sess.build_dir / 'top' / task_id / 'result.json').exists()
    
    res3_expect = "step3 res (step2 res (step1 res))"
    res6_expect = f"step6 res (step5 res ({res3_expect}), {res3_expect}, step4 res (step1 res))"
    res10_expect = f'step10 res (step9 res (step5 res ({res3_expect}), {res6_expect}, step8 res))'

    res10 = sess.get_result(TargetId('top', 'step10'))
    assert res10.my_key == res10_expect


def test_missing_require(tmp_path):
    sess = get_flow_session(tmp_path)
    with pytest.raises(ResultRequired) as e:
        sess.plan('top', 'step2').run()
    assert e.value.target_id == TargetId('top', 'step1')
