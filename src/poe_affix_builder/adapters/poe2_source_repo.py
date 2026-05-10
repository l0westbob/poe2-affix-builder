from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

POE2_REPO_URL = "https://github.com/repoe-fork/poe2.git"
POE2_REPO_BRANCH = "master"

RunCommand = Callable[..., subprocess.CompletedProcess[str]]
Emitter = Callable[[str], None]


def clone_poe2_repo(repo_dir: Path, *, run_command: RunCommand = subprocess.run) -> None:
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        run_command(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                POE2_REPO_BRANCH,
                "--filter=blob:none",
                "--sparse",
                POE2_REPO_URL,
                str(repo_dir),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        run_command(
            [
                "git",
                "-C",
                str(repo_dir),
                "sparse-checkout",
                "set",
                "--no-cone",
                "data/mods.json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("git is required to fetch the PoE2 source repository.") from exc
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or "").strip()
        message = details or str(exc)
        raise RuntimeError(f"Failed to clone PoE2 source repository: {message}") from exc


def _materialize_mods_json(repo_dir: Path, *, run_command: RunCommand = subprocess.run) -> None:
    try:
        run_command(
            [
                "git",
                "-C",
                str(repo_dir),
                "sparse-checkout",
                "reapply",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        run_command(
            [
                "git",
                "-C",
                str(repo_dir),
                "restore",
                "--source=HEAD",
                "--worktree",
                "--staged",
                "data/mods.json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("git is required to restore the PoE2 source repository checkout.") from exc
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or "").strip()
        message = details or str(exc)
        raise RuntimeError(f"Failed to restore PoE2 source repository checkout: {message}") from exc


def resolve_mods_json_path(
    source_dir: Path,
    *,
    emit: Emitter | None = None,
    run_command: RunCommand = subprocess.run,
) -> Path:
    mods_json_path = source_dir / "mods.json"
    if mods_json_path.exists():
        return mods_json_path

    if source_dir.name != "data":
        raise FileNotFoundError(
            f"mods.json not found at {mods_json_path}. "
            "Pass --source-dir pointing to a directory that contains mods.json."
        )

    repo_dir = source_dir.parent
    repo_git_dir = repo_dir / ".git"

    if not repo_git_dir.exists():
        if repo_dir.exists():
            raise RuntimeError(
                f"Expected a git repo at {repo_dir}, but found a non-repository directory. "
                f"Remove {repo_dir} and run again, or pass a different --source-dir."
            )
        if emit is not None:
            emit(f"[source] missing {mods_json_path}; cloning {POE2_REPO_URL} ({POE2_REPO_BRANCH}) into {repo_dir}")
        clone_poe2_repo(repo_dir, run_command=run_command)
        if emit is not None:
            emit(f"[source] clone complete: {repo_dir}")

    if not mods_json_path.exists():
        if emit is not None:
            emit(f"[source] restoring sparse checkout for {mods_json_path}")
        _materialize_mods_json(repo_dir, run_command=run_command)

    if not mods_json_path.exists():
        raise FileNotFoundError(f"mods.json not found at {mods_json_path} after source repo check.")
    return mods_json_path
