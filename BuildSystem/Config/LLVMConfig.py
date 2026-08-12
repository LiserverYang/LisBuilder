# Copyright 2025, LiserverYang. All rights reserved.

import subprocess
import os
import sys

from ..Logger import Logger
from ..LogLevelEnum import LogLevelEnum

LLVMLibs: str = ""
LLVMCommand: str = ""
LLVMIncludeCommand: str = ""


def InitLLVMConfig(LLVMPosition: str) -> None:
    """Probe llvm-config under ``LLVMPosition`` and populate the global
    LLVMLibs / LLVMCommand / LLVMIncludeCommand strings used by the
    Compiler and Main modules.

    ``LLVMPosition`` is the root of a local LLVM installation (e.g.
    ``F:/LLVM/``).  The function expects the following layout::

        {LLVMPosition}/bin/llvm-config(.exe)
        {LLVMPosition}/include/
        {LLVMPosition}/lib/
    """
    global LLVMLibs, LLVMCommand, LLVMIncludeCommand

    # Normalise trailing slashes so os.path.join produces clean paths.
    LLVMPosition = LLVMPosition.rstrip("/\\")

    LlvmConfigExe = os.path.join(LLVMPosition, "bin", "llvm-config")
    if sys.platform == "win32":
        LlvmConfigExe += ".exe"

    if not os.path.exists(LlvmConfigExe):
        Logger.Log(
            LogLevelEnum.Error,
            f"llvm-config not found at '{LlvmConfigExe}'. "
            f"Check --llvm-position (got '{LLVMPosition}').",
            True,
            -1,
        )

    try:
        Raw = subprocess.run(
            [LlvmConfigExe, "--system-libs", "--libnames", "--link-static", "all"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as Exc:
        Logger.Log(
            LogLevelEnum.Error,
            f"llvm-config failed: {Exc}",
            True,
            -1,
        )

    # "libLLVMCore.lib libLLVMSupport.lib … libxml2s.lib" ->
    # "-lLLVMCore -lLLVMSupport …" (minus libxml2s which we don't ship).
    LLVMLibs = (
        " -l".join(
            lib.split(".")[0]
            for lib in Raw.replace(" libxml2s.lib", "").split()
        )
        + " -lwinpthread -lmingwex -lmsvcr120 -lz -lzstd"
    )

    LLVMIncludeCommand = f"-I{LLVMPosition}/include"
    LLVMCommand = f"{LLVMIncludeCommand} -L{LLVMPosition}/lib/ -l{LLVMLibs}"
