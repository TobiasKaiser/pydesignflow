# SPDX-FileCopyrightText: 2026 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

import pytest

def get_flow():
    from .flow_example1 import flow
    return flow

def test_cli_build_task(tmp_path):
    """Test basic task execution via CLI."""
    flow = get_flow()
    flow.cli_main(['top.step1', '--build-dir', str(tmp_path)])
    assert (tmp_path / 'top' / 'step1' / 'result.json').exists()

def test_cli_build_with_dependencies(tmp_path):
    """Test building task with dependencies."""
    flow = get_flow()
    flow.cli_main(['top.step2', '--build-dir', str(tmp_path)])
    # Both step1 and step2 should have results
    assert (tmp_path / 'top' / 'step1' / 'result.json').exists()
    assert (tmp_path / 'top' / 'step2' / 'result.json').exists()

def test_cli_status_display(tmp_path, capsys):
    """Test status command displays block information."""
    flow = get_flow()
    flow.cli_main(['--build-dir', str(tmp_path)])
    captured = capsys.readouterr()
    assert 'top' in captured.out

def test_cli_dry_run(tmp_path, capsys):
    """Test --dry-run flag prints plan but doesn't execute."""
    flow = get_flow()
    flow.cli_main(['top.step1', '--build-dir', str(tmp_path), '--dry-run'])
    # Verify result was NOT created
    assert not (tmp_path / 'top' / 'step1' / 'result.json').exists()
    # But plan should have been printed
    captured = capsys.readouterr()
    assert 'PyDesignFlow Build Plan' in captured.out

def test_cli_clean(tmp_path):
    """Test --clean flag removes results for both task and block."""
    flow = get_flow()
    # Build multiple tasks
    flow.cli_main(['top.step2', '--build-dir', str(tmp_path)])
    assert (tmp_path / 'top' / 'step1' / 'result.json').exists()
    assert (tmp_path / 'top' / 'step2' / 'result.json').exists()

    # Clean single task
    flow.cli_main(['top.step1', '--build-dir', str(tmp_path), '--clean'])
    assert not (tmp_path / 'top' / 'step1' / 'result.json').exists()

    # Rebuild and clean entire block
    flow.cli_main(['top.step2', '--build-dir', str(tmp_path)])
    flow.cli_main(['top', '--build-dir', str(tmp_path), '--clean'])
    assert not (tmp_path / 'top' / 'step1' / 'result.json').exists()
    assert not (tmp_path / 'top' / 'step2' / 'result.json').exists()

def test_cli_invalid_targets(tmp_path):
    """Test error handling for non-existent blocks and tasks."""
    flow = get_flow()

    # Test invalid block
    with pytest.raises(SystemExit) as exc_info:
        flow.cli_main(['nonexistent.step1', '--build-dir', str(tmp_path)])
    assert "not found" in str(exc_info.value)

    # Test invalid task
    with pytest.raises(SystemExit) as exc_info:
        flow.cli_main(['top.nonexistent', '--build-dir', str(tmp_path)])
    assert "not found" in str(exc_info.value)

def test_cli_dot_notation(tmp_path):
    """Test block.task dot notation parsing."""
    flow = get_flow()
    flow.cli_main(['top.step1', '--build-dir', str(tmp_path)])
    assert (tmp_path / 'top' / 'step1' / 'result.json').exists()

def test_cli_no_blocks():
    """Test error handling when flow has no blocks."""
    from pydesignflow import Flow
    flow = Flow()
    with pytest.raises(SystemExit) as exc_info:
        flow.cli_main(['--help'])
    assert "No blocks defined" in str(exc_info.value)
