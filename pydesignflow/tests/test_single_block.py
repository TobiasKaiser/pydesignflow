from .. import Block, Flow, action, Result

class MyBlock(Block):
    @action()
    def step1(self, cwd):
        step1 = Result()
        step1.my_key = "step1 res"
        return step1

    @action()
    def step_without_result(self, cwd):
        pass

    @action(requires={'s1':'.step1'})
    def step2(self, cwd, s1):
        step2 = Result()
        step2.my_key = f"step2 res ({s1.my_key})"
        return step2

    @action(requires={'s2':'.step2'})
    def step3(self, cwd, s2):
        step3 = Result()
        step3.my_key = f"step3 res ({s2.my_key})"
        return step3

    @action(requires={'s3':'.step3'})
    def step4(self, cwd):
        step4 = Result()
        step4.my_key = f"step4 res ({s3.my_key})"
        return step4

def get_flow_session(build_dir):
    flow = Flow()
    flow['top'] = MyBlock()

    return flow.session_at(build_dir)

def test_step1_creates_result(tmp_path):
    sess = get_flow_session(tmp_path)
    action_id = 'step1'
    sess.run_action('top', action_id)
    assert (sess.build_dir / 'top' / action_id / 'result.json').exists()

def test_step_without_result(tmp_path):
    sess = get_flow_session(tmp_path)
    action_id = 'step_without_result'
    sess.run_action('top', action_id)
    assert not (sess.build_dir / 'top' / action_id / 'result.json').exists()

def test_step1_step2(tmp_path):
    sess = get_flow_session(tmp_path)
    sess.run_action('top', 'step1')
    sess.run_action('top', 'step2')
    assert (sess.build_dir / 'top' / 'step1' / 'result.json').exists()
    assert (sess.build_dir / 'top' / 'step2' / 'result.json').exists()
