from .. import Block, task, Flow, Result

class ExampleBlock(Block):
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

    @task(requires={'s1':'.step1'}, always_rebuild=True)
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

    @task(requires={'s5':'.step5', 's6':'.step6', 's8':'.step8'}, always_rebuild=True)
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
    flow['top'] = ExampleBlock()

    return flow.session_at(build_dir)
