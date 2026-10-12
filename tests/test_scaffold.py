"""Smoke tests for the initial project scaffold."""

import run


def test_default_run_prints_all_stages(capsys) -> None:
    """The default command lists every pipeline stage in order."""
    assert run.main([]) == 0
    assert capsys.readouterr().out.splitlines() == list(run.STAGES)
