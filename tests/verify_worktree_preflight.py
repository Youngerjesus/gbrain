#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "init_worktree.sh"


def run(cmd: list[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed: {cmd}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


class InitWorktreeTest(unittest.TestCase):
    def setUp(self) -> None:
        if not SCRIPT.exists():
            raise AssertionError(f"missing {SCRIPT.relative_to(ROOT)}")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name) / "repo"
        self.base.mkdir()
        run(["git", "init", "-b", "main"], cwd=self.base)
        run(["git", "config", "user.email", "test@example.com"], cwd=self.base)
        run(["git", "config", "user.name", "Test User"], cwd=self.base)
        (self.base / "scripts").mkdir()
        shutil.copy2(SCRIPT, self.base / "scripts" / "init_worktree.sh")
        os.chmod(self.base / "scripts" / "init_worktree.sh", 0o755)
        (self.base / "scripts" / "verify").write_text(
            "#!/usr/bin/env bash\nexit 0\n",
            encoding="utf-8",
        )
        os.chmod(self.base / "scripts" / "verify", 0o755)
        run(["git", "add", "scripts"], cwd=self.base)
        run(["git", "commit", "-m", "initial"], cwd=self.base)

    def call_script(self, target: Path, *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return run(
            [str(self.base / "scripts" / "init_worktree.sh"), str(target)],
            cwd=cwd or Path(self.tmp.name),
            check=False,
        )

    def test_rejects_main_worktree_as_task_target(self) -> None:
        result = self.call_script(self.base)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("main worktree", result.stderr)

    def test_accepts_isolated_task_worktree_from_external_cwd(self) -> None:
        target = Path(self.tmp.name) / "task-worktree"
        run(["git", "worktree", "add", "-b", "codex/task-worktree", str(target)], cwd=self.base)
        result = self.call_script(target, cwd=Path(self.tmp.name))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("worktree setup ok", result.stdout)

    def test_rejects_worktree_missing_required_verify_entrypoint(self) -> None:
        run(["git", "checkout", "-b", "without-verify"], cwd=self.base)
        (self.base / "scripts" / "verify").unlink()
        run(["git", "add", "-u", "scripts/verify"], cwd=self.base)
        run(["git", "commit", "-m", "remove verify"], cwd=self.base)
        run(["git", "checkout", "main"], cwd=self.base)
        target = Path(self.tmp.name) / "missing-verify-worktree"
        run(["git", "worktree", "add", str(target), "without-verify"], cwd=self.base)
        result = self.call_script(target)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("scripts/verify", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
