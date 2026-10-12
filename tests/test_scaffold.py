"""Smoke tests for the initial project scaffold."""

import pandas as pd

import run


def test_default_run_prints_all_stages(capsys, monkeypatch) -> None:
    """The default command lists every pipeline stage in order."""
    source = pd.DataFrame({"value": [1]})

    def fake_audit(raw_path):
        assert raw_path is source

    def fake_panel(raw_path):
        assert raw_path is source
        print("panel")

    monkeypatch.setattr(run, "build_audit", fake_audit)
    monkeypatch.setattr(run, "run_panel", fake_panel)
    monkeypatch.setattr(run, "build_parser", lambda: _SyntheticParser(source))
    assert run.main([]) == 0
    assert capsys.readouterr().out.splitlines() == list(run.STAGES)


class _SyntheticParser:
    def __init__(self, source):
        self.source = source

    def parse_args(self, argv):
        return type("Args", (), {"command": None, "unit": None, "date": None,
                                  "raw_path": self.source})()
