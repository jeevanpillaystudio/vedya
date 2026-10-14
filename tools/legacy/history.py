"""Files from this repository's git history, written out as they were at a commit.

The Fusion 360 scripts are read from history by commit, not from the tree, so the pin
keeps working once they leave it. A clone made with `--depth 1` lacks the commits; fetch
full history first (`git fetch --unshallow`, or `fetch-depth: 0` in CI).
"""

import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path, PurePosixPath

__all__ = ["REPOSITORY", "files", "materialise", "resolve"]

REPOSITORY = Path(__file__).resolve().parents[2]
"""The root of the repository whose history is read."""


def resolve(commit: str) -> str:
    """The full hash of `commit`. Raises `LookupError` if this clone's history lacks it."""
    result = subprocess.run(
        ["git", "-C", str(REPOSITORY), "rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}"],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise LookupError(
            f"commit {commit} is not in this clone's history; fetch it with `git fetch --unshallow`"
        )
    return result.stdout.strip()


def files(commit: str, *paths: str) -> list[str]:
    """Every file at `commit` that is one of `paths` or lies under one of them.

    Paths are written from the repository's root with `/`, as git writes them. Raises
    `FileNotFoundError` for a path that names nothing at `commit`.
    """
    found: list[str] = []
    for path in paths:
        listed = _git("ls-tree", "-r", "-z", "--name-only", commit, "--", path)
        names = [name for name in listed.decode("utf-8").split("\0") if name]
        if not names:
            raise FileNotFoundError(f"{path} does not exist at {commit}")
        found.extend(names)
    return list(dict.fromkeys(found))


def materialise(commit: str, paths: Sequence[str], into: Path | None = None) -> Path:
    """Write the files `paths` name at `commit` under `into`, each at its repository path.

    A path may name a file or a folder. Without `into`, a new temporary folder is made;
    the caller removes it. Returns the folder written into.
    """
    root = Path(tempfile.mkdtemp(prefix=f"vedya-{commit[:7]}-")) if into is None else into
    for path in files(commit, *paths):
        target = root.joinpath(*PurePosixPath(path).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_git("show", f"{commit}:{path}"))
    return root


def _git(*args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(REPOSITORY), *args], capture_output=True, check=False)
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout
