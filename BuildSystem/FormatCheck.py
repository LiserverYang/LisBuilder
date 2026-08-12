# Copyright 2025, LiserverYang. All rights reserved.

import os
import shutil
import subprocess

from .BuildContext import BuildContext


def FindClangFormat() -> str:
    """
    Locate the clang-format binary.

    Search order:
      1. ``clang-format`` on PATH (a pinned version is recommended — the CI and
         local machines must agree, clang-format 18 vs 20 disagree on
         comment alignment and braced-list packing).
      2. ``<--llvm-position>/bin/clang-format`` (the LLVM the project builds
         against).
      3. Common Windows install location (``C:/Program Files/LLVM/bin``).

    Falls back to the bare name so the error message stays readable.
    """
    Candidates: list = [shutil.which("clang-format")]

    Args = getattr(BuildContext, "Arguments", None)
    LlvmPosition = getattr(Args, "llvm_position", "") if Args else ""
    if LlvmPosition:
        Candidates.append(
            os.path.join(
                LlvmPosition.rstrip("/\\"),
                "bin",
                "clang-format.exe" if os.name == "nt" else "clang-format",
            )
        )
    Candidates += [
        "C:/Program Files/LLVM/bin/clang-format",
        "C:/Program Files/LLVM/bin/clang-format.exe",
    ]

    for Candidate in Candidates:
        if Candidate and os.path.exists(Candidate):
            return Candidate
    return "clang-format"


def CheckFormat(FileName: str) -> int:
    """Return 0 iff *FileName* is already clang-format clean."""
    return subprocess.call([FindClangFormat(), "--Werror", "--dry-run", FileName])


def FormatFile(FileName: str) -> int:
    """Format *FileName* in place; return 0 on success."""
    return subprocess.call([FindClangFormat(), "-i", FileName])
