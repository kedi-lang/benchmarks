#!/usr/bin/env python3
"""Write portable SHA256 checksums for the publication payload."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    options = parser.parse_args()
    root = options.root.expanduser().resolve()
    output = root / "checksums.sha256"
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink() and path != output
    )
    output.write_text(
        "".join(f"{digest(path)}  {path.relative_to(root).as_posix()}\n" for path in files),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
