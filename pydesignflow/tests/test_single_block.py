import pytest
from .. import Block, TargetId, Flow, task, Result, ResultRequired

class MyBlock(Block):
    @task()
    def step_without_result(self, cwd):
        pass

    @task()
    def step1(self, cwd):
        r = Result()
        r.my_key = "step1 res"
        return r

    @task(requires={'s1':'.step1'})
    def step2(self, cwd, s1):
        r = Result()
        r.my_key = f"step2 res ({s1.my_key})"
        return r

    @task(requires={'s2':'.step2'})
    def step3(self, cwd, s2):
        r = Result()
        r.my_key = f"step3 res ({s2.my_key})"
        return r

    @task(requires={'s1':'.step1'})
    def step4(self, cwd, s1):
        r = Result()
        r.my_key = f"step4 res ({s1.my_key})"
        return r

    @task(requires={'s3':'.step3'})
    def step5(self, cwd, s3):
        r = Result()
        r.my_key = f"step5 res ({s3.my_key})"
        return r

    @task(requires={'s5':'.step5', 's3':'.step3', 's4':'.step4'})
    def step6(self, cwd, s5, s3, s4):
        r = Result()
        r.my_key = f"step6 res ({s5.my_key}, {s3.my_key}, {s4.my_key})"
        return r

    @task(requires={'s2':'.step2', 's4':'.step4'})
    def step7(self, cwd, s2, s4):
        r = Result()
        r.my_key = f"step7 res ({s2.my_key}, {s4.my_key})"
        return r

    @task()
    def step8(self, cwd):
        r = Result()
        r.my_key = f"step8 res"
        return r

    @task(requires={'s5':'.step5', 's6':'.step6', 's8':'.step8'})
    def step9(self, cwd, s5, s6, s8):
        r = Result()
        r.my_key = f"step9 res ({s5.my_key}, {s6.my_key}, {s8.my_key})"
        return r

    @task(requires={'s9':'.step9'})
    def step10(self, cwd, s9):
        r = Result()
        r.my_key = f"step10 res ({s9.my_key})"
        return r


def get_flow_session(build_dir):
    flow = Flow()
    flow['top'] = MyBlock()

    return flow.session_at(build_dir)

def test_step1_creates_result(tmp_path):
    sess = get_flow_session(tmp_path)
    task_id = 'step1'
    sess.run_task('top', task_id)
    assert (sess.build_dir / 'top' / task_id / 'result.json').exists()

def test_step_without_result(tmp_path):
    sess = get_flow_session(tmp_path)
    task_id = 'step_without_result'
    sess.run_task('top', task_id)
    # In an earlier version, tasks without a result would not create a result.json file.
    assert (sess.build_dir / 'top' / task_id / 'result.json').exists()

def test_step1_step2(tmp_path):
    sess = get_flow_session(tmp_path)
    sess.run_task('top', 'step1')
    sess.run_task('top', 'step2')
    assert (sess.build_dir / 'top' / 'step1' / 'result.json').exists()
    assert (sess.build_dir / 'top' / 'step2' / 'result.json').exists()

def test_step123(tmp_path):
    sess = get_flow_session(tmp_path)
    for i in range(1, 1+3):
        task_id = f'step{i}'
        sess.run_task('top', task_id)
        assert (sess.build_dir / 'top' / task_id / 'result.json').exists()
    
def test_run_all(tmp_path):
    sess = get_flow_session(tmp_path)
    for i in range(1, 1+10):
        task_id = f'step{i}'
        sess.run_task('top', task_id)
        assert (sess.build_dir / 'top' / task_id / 'result.json').exists()
    
    res3_expect = "step3 res (step2 res (step1 res))"
    res6_expect = f"step6 res (step5 res ({res3_expect}), {res3_expect}, step4 res (step1 res))"
    res10_expect = f'step10 res (step9 res (step5 res ({res3_expect}), {res6_expect}, step8 res))'

    res10 = sess.get_result(TargetId('top', 'step10'))
    assert res10.my_key == res10_expect



def test_missing_require(tmp_path):
    sess = get_flow_session(tmp_path)
    with pytest.raises(ResultRequired) as e:
        sess.run_task('top', 'step2')
    assert e.value.result_id == TargetId('top', 'step1')
