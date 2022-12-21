import pytest
from pydesignflow import TargetId, ResultRequired

def get_flow_session(build_dir):
    from .flow_example1 import flow
    return flow.session_at(build_dir)

def test_deplist_step2(tmp_path):
    sess = get_flow_session(tmp_path)
    task_id = 'step2'
    l=sess.plan('top', task_id, build_dependencies='missing').target_sequence
    assert l == [
        TargetId('top', "step1"),
        TargetId('top', "step2"),
    ]

def test_deplist_step2_dont_rebuild(tmp_path):
    sess = get_flow_session(tmp_path)
    task_id = 'step2'
    sess.plan('top', 'step1').run()
    l=sess.plan('top', task_id, build_dependencies='missing').target_sequence
    assert l == [
        TargetId('top', "step2"),
    ]

def test_deplist_step2_do_rebuild(tmp_path):
    sess = get_flow_session(tmp_path)
    task_id = 'step2'
    sess.plan('top', 'step1').run()
    l=sess.plan('top', task_id, build_dependencies='all').target_sequence
    assert l == [
        TargetId('top', "step1"),
        TargetId('top', "step2"),
    ]

def test_deplist_step5(tmp_path):
    sess = get_flow_session(tmp_path)
    task_id = 'step5'
    l=sess.plan('top', task_id, build_dependencies='missing').target_sequence
    assert l == [
        TargetId('top', "step1"),
        TargetId('top', "step2"),
        TargetId('top', "step3"),
        TargetId('top', "step5"),
    ]

def test_deplist_step7(tmp_path):
    sess = get_flow_session(tmp_path)
    task_id = 'step7'
    l=sess.plan('top', task_id, build_dependencies='missing').target_sequence
    assert l == [
        TargetId('top', "step1"),
        TargetId('top', "step2"),
        TargetId('top', "step4"),
        TargetId('top', "step7"),
    ]

def test_deplist_step7_dont_rebuild(tmp_path):
    sess = get_flow_session(tmp_path)
    task_id = 'step7'
    sess.plan('top', 'step1').run()
    sess.plan('top', 'step4').run()
    l=sess.plan('top', task_id, build_dependencies='missing').target_sequence
    assert l == [
        TargetId('top', "step2"),
        TargetId('top', "step4"), # step4 must be rebuilt, because it is tagged as always_rebuild
        TargetId('top', "step7"),
    ]

def test_deplist_step7_force_rebuild(tmp_path):
    sess = get_flow_session(tmp_path)
    task_id = 'step7'
    sess.plan('top', 'step1').run()
    sess.plan('top', 'step4').run()
    l=sess.plan('top', task_id, build_dependencies='all').target_sequence
    assert l == [
        TargetId('top', "step1"),
        TargetId('top', "step2"),
        TargetId('top', "step4"),
        TargetId('top', "step7"),
    ]

def test_deplist_step9(tmp_path):
    sess = get_flow_session(tmp_path)
    task_id = 'step9'
    l=sess.plan('top', task_id, build_dependencies='missing').target_sequence
    assert l == [
        TargetId('top', "step1"),
        TargetId('top', "step2"),
        TargetId('top', "step3"),
        TargetId('top', "step5"),
        TargetId('top', "step4"),
        TargetId('top', "step6"),
        TargetId('top', "step8"),
        TargetId('top', "step9"),
    ]