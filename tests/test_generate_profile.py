"""scripts/generate_profile.py must keep running as the models change."""

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_generate_profile_runs(tmp_path):
    out = tmp_path / "evi-vocabulary.ttl"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate_profile.py"), str(out)],
        check=True, cwd=ROOT,
    )
    ttl = out.read_text()
    assert "evi:Dataset" in ttl
    assert "evi:Computation" in ttl
