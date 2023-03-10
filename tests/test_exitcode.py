import pytest
import subprocess
from pydesignflow import Flow, Block, task, Result

class MyBlock(Block):
    @task()
    def subprocess_error(self, cwd):
        subprocess.check_call(["sh", "-c", "exit 1"])

def get_flow():
    flow = Flow()
    flow['b'] = MyBlock()
    return flow


#def get_flow_session(build_dir):
#    flow = Flow()
#    flow['b'] = TestB()
#    return flow.session_at(build_dir)

def test_subprocess_exitcode(tmp_path):
    flow = get_flow()
    with pytest.raises(SystemExit):
        flow.cli_main(['b.subprocess_error', '--build-dir', str(tmp_path)])