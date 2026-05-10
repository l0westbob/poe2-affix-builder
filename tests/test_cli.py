from __future__ import annotations

import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from poe_affix_builder.cli import _clone_poe2_repo, _resolve_mods_json_path, main
from poe_affix_builder.domain.models import BuildResult


class CliSourceRepoTests(unittest.TestCase):
    def test_resolve_mods_path_when_mods_exists(self):
        with tempfile.TemporaryDirectory() as td:
            source_dir = Path(td) / "poe2" / "data"
            source_dir.mkdir(parents=True, exist_ok=True)
            mods_json_path = source_dir / "mods.json"
            mods_json_path.write_text("{}", encoding="utf-8")
            resolved = _resolve_mods_json_path(source_dir)
            self.assertEqual(resolved, mods_json_path)

    def test_resolve_mods_path_clones_when_repo_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_dir = root / "poe2" / "data"
            repo_dir = root / "poe2"
            emitted: list[str] = []

            def _fake_run(cmd, **kwargs):
                _ = kwargs
                if cmd[1] == "clone":
                    (repo_dir / ".git").mkdir(parents=True, exist_ok=True)
                    source_dir.mkdir(parents=True, exist_ok=True)
                    (source_dir / "mods.json").write_text("{}", encoding="utf-8")
                return subprocess.CompletedProcess(args=cmd, returncode=0)

            resolved = _resolve_mods_json_path(source_dir, emit=emitted.append, run_command=_fake_run)

            self.assertEqual(resolved, source_dir / "mods.json")
            self.assertEqual(len(emitted), 2)
            self.assertIn("clone complete", emitted[1])

    def test_resolve_mods_path_non_standard_source_dir_raises(self):
        with tempfile.TemporaryDirectory() as td:
            source_dir = Path(td) / "custom-source"
            source_dir.mkdir(parents=True, exist_ok=True)
            with self.assertRaises(FileNotFoundError):
                _resolve_mods_json_path(source_dir)

    def test_resolve_mods_path_existing_non_repo_dir_raises(self):
        with tempfile.TemporaryDirectory() as td:
            source_dir = Path(td) / "poe2" / "data"
            source_dir.parent.mkdir(parents=True, exist_ok=True)
            with self.assertRaises(RuntimeError):
                _resolve_mods_json_path(source_dir)

    def test_resolve_mods_path_repo_exists_but_mods_missing_raises(self):
        with tempfile.TemporaryDirectory() as td:
            source_dir = Path(td) / "poe2" / "data"
            repo_dir = source_dir.parent
            (repo_dir / ".git").mkdir(parents=True, exist_ok=True)
            with self.assertRaises(FileNotFoundError):
                _resolve_mods_json_path(source_dir)

    def test_clone_poe2_repo_wraps_git_error(self):
        with tempfile.TemporaryDirectory() as td:
            repo_dir = Path(td) / "poe2"

            def _raise(*args, **kwargs):
                _ = args, kwargs
                raise subprocess.CalledProcessError(returncode=1, cmd=["git", "clone"], stderr="fatal: clone failed")

            with self.assertRaises(RuntimeError) as err:
                _clone_poe2_repo(repo_dir, run_command=_raise)
            self.assertIn("Failed to clone PoE2 source repository", str(err.exception))

    def test_clone_poe2_repo_uses_sparse_checkout_for_mods_json(self):
        with tempfile.TemporaryDirectory() as td:
            repo_dir = Path(td) / "poe2"
            calls: list[list[str]] = []

            def _record_call(cmd, **kwargs):
                _ = kwargs
                calls.append(cmd)
                return subprocess.CompletedProcess(args=cmd, returncode=0)

            _clone_poe2_repo(repo_dir, run_command=_record_call)

            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0][0:2], ["git", "clone"])
            self.assertIn("--sparse", calls[0])
            self.assertIn("--filter=blob:none", calls[0])
            self.assertEqual(calls[1][0:4], ["git", "-C", str(repo_dir), "sparse-checkout"])
            self.assertEqual(calls[1][-2:], ["--no-cone", "data/mods.json"])


class CliCommandTests(unittest.TestCase):
    def test_build_message_uses_advisory_wording(self):
        fake_result = BuildResult(
            items_written=1,
            affixes_written=2,
            tiers_written=3,
            unresolved_tiers=(),
            mapping_warnings={"Amulets": [{}]},
        )
        out = io.StringIO()
        with (
            patch("poe_affix_builder.cli._resolve_mods_json_path", return_value=Path("mods.json")),
            patch("poe_affix_builder.cli.build_affixes", return_value=fake_result),
            patch("sys.argv", ["poe-affix-build", "build"]),
            patch("sys.stdout", out),
        ):
            rc = main()
        self.assertEqual(rc, 0)
        self.assertIn("Coverage advisories: 1", out.getvalue())

    def test_validate_message_uses_advisory_wording(self):
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as td:
            report_path = Path(td) / "validation.json"
            with (
                patch("poe_affix_builder.cli._resolve_mods_json_path", return_value=Path("mods.json")),
                patch("poe_affix_builder.cli.validate_mapping", return_value={"items": 1, "items_with_warnings": 0, "warnings": {}}),
                patch("sys.argv", ["poe-affix-build", "validate-mapping", "--out", str(report_path)]),
                patch("sys.stdout", out),
            ):
                rc = main()
        self.assertEqual(rc, 0)
        self.assertIn("validation advisory report", out.getvalue())


if __name__ == "__main__":
    unittest.main()
