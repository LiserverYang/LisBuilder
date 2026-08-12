# Copyright 2025, LiserverYang. All rights reserved.

from .FileSystem import FileIO
from .Logger import Logger
from .LogLevelEnum import LogLevelEnum
from .BuildTarget import BuildTarget
from .Functions import GetInformations
from .GenericJson import GenericJson
from .BuildContext import BuildContext
from .TimeSolver import FormatDuration
from .BuildTypeEnum import BuildTypeEnum
from .Config.LLVMConfig import InitLLVMConfig
from .Functions import GetCurrentSystem
from .SystemEnum import SystemEnum
from typing import List

import os
import shutil
import sys
import time
import traceback
import argparse


def _CleanBuildArtifacts(TargetList: List[str]) -> None:
    """Remove all build artifacts for every target in *TargetList*.

    This replaces the old manual ritual::

        rm -rf Build/Binaries/libCompiler.a \\
               Build/Binaries/lisc.exe      \\
               Build/Intermediate/lisc/Main
    """
    Root: str = BuildContext.RootPath
    BuildRoot: str = os.path.join(Root, "Build") if Root else "./Build"
    InterDir: str = os.path.join(BuildRoot, "Intermediate")
    BinsDir: str = os.path.join(BuildRoot, "Binaries")

    # Each target owns an Intermediate/<TargetName>/ directory.
    for TargetPath in TargetList:
        TargetName: str = os.path.basename(TargetPath)
        # "lisc.target.py" -> "lisc"
        if TargetName.endswith(".target.py"):
            TargetName = TargetName[: -len(".target.py")]
        TargetInter: str = os.path.join(InterDir, TargetName)
        if os.path.isdir(TargetInter):
            shutil.rmtree(TargetInter, ignore_errors=True)

    # Shared test binary lives at Build/Intermediate/test(.exe).
    for Name in ("test", "test.exe"):
        P: str = os.path.join(InterDir, Name)
        if os.path.exists(P):
            os.remove(P)

    # Binaries: archives, executables and the copied stdlib. The BuildSystem/
    # package and READMEs live in the same tree and must NOT be touched.
    ExeSuffix: str = ".exe" if GetCurrentSystem() == SystemEnum.Windows else ""
    for Name in os.listdir(BinsDir):
        Full: str = os.path.join(BinsDir, Name)
        if (
            Name.endswith(".a")
            or Name.endswith(".lib")
            or (ExeSuffix and Name.endswith(ExeSuffix))
            or (Name == "lstdlib" and os.path.isdir(Full))
        ):
            if os.path.isdir(Full):
                shutil.rmtree(Full, ignore_errors=True)
            else:
                os.remove(Full)

    Logger.Log(LogLevelEnum.Info, "Removed all build artifacts (--clean).")


def BuildApp(SourceFolder: FileIO, TargetList: List[str]) -> None:
    """
    Build the application.
    
    :param SourceFolder: the folder's FILEIO where stored source file
    :type SourceFolder: FileIO
    :param TargetList: a list of target's configuration file path(*.target.py), build system will build the target in the order of the list.
    :type TargetList: List[str]
    
    For example, if can call it:

    ```BuildApp(FileIO("./Source/"), ["./Source/project.target.py", "./Source/Plugins/plugin_api.target.py"])
    """

    # Do some checks
    if not SourceFolder.Exists():
        Logger.Log(
            LogLevelEnum.Error,
            "Could not found Source folder, please check your source.",
            True,
            -1,
        )

    if not SourceFolder.IsFolder():
        Logger.Log(
            LogLevelEnum.Error,
            "The source is not a folder, please check your source.",
            True,
            -1,
        )

    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--build-type",
        help="The build type of application (Release, Debug or Development)",
        choices=["Release", "Debug", "Development"],
    )
    parser.add_argument(
        "--donot-build-files",
        help="If enabled, the build system will not execute the compile/link command, but something like format check will be executed",
        action="store_true",
    )
    parser.add_argument(
        "--donot-use-o-files",
        help="If enabled, the build system will not use cache (.o files) to build module",
        action="store_true",
    )
    parser.add_argument(
        "--enable-tests",
        help="If enabled, the build system will execute the unit test with google test (all test file should be at ModuolePath/Test/**)",
        action="store_true",
    )
    parser.add_argument(
        "--enable-format-check",
        help="If enabled, the build system will check the code format with clang-format",
        action="store_true",
    )
    parser.add_argument(
        "--llvm-position",
        help="The position of llvm.",
        default="",
    )
    parser.add_argument(
        "--donot-generic-cc-json",
        help="If eanbled, the build system will not generate compile_commands.json in the root folder.",
        action="store_true"
    )
    parser.add_argument("--threads", help="Set the thread number", type=int, default=1)
    parser.add_argument(
        "--clean",
        help="Remove all build artifacts for the target before building.",
        action="store_true",
    )
    BuildContext.Arguments = parser.parse_args()

    # Anchor every path to the repo root (the dir containing SourceFolder) so
    # the build works regardless of the invocation cwd.
    SourceFolder = FileIO(os.path.abspath(SourceFolder.FilePathStr))
    BuildContext.RootPath = os.path.dirname(SourceFolder.FilePathStr)
    TargetList = [
        t if os.path.isabs(t) else os.path.join(BuildContext.RootPath, t)
        for t in TargetList
    ]

    if BuildContext.Arguments.clean:
        _CleanBuildArtifacts(TargetList)

    if BuildContext.Arguments.llvm_position != "":
        InitLLVMConfig(BuildContext.Arguments.llvm_position)

    try:
        Logger.Log(LogLevelEnum.Info, f"Python version {sys.version}")

        # Get Build type
        match BuildContext.Arguments.build_type:
            case "Debug":
                BuildContext.BuildType = BuildTypeEnum.Debug
            case "Release":
                BuildContext.BuildType = BuildTypeEnum.Release
            case "Development":
                BuildContext.BuildType = BuildTypeEnum.Development

        Logger.Log(LogLevelEnum.Info, f"Build type is {BuildContext.BuildType.name}.")

        GetInformations()

        Logger.Log(LogLevelEnum.Info, f"System is {BuildContext.SystemType.name}.")

        Logger.Log(LogLevelEnum.Info, "Reading all targets.")

        # Start timing
        StartTime = time.time()

        Logger.Log(LogLevelEnum.Info, "Found target: " + ", ".join(TargetList))

        for target in TargetList:
            BuildTarget(FileIO(target))

        # For clangd, we generic some files
        GenericJson(BuildContext.CompileCommands)

        Logger.Log(
            LogLevelEnum.Info,
            f"Build done. Use time in toal: {FormatDuration(time.time() - StartTime)}",
        )
    except SystemExit:
        # Logger.Log(..., bExit=True) exits deliberately; do not swallow it.
        raise
    except KeyboardInterrupt:
        Logger.Log(LogLevelEnum.Error, "Build interrupted by user.", True, -1)
    except Exception as Exc:
        # Unexpected failure: keep the traceback for diagnosis, but exit through
        # the logger so the exit code stays consistent and the message is clear.
        print(traceback.format_exc(), file=sys.stderr)
        Logger.Log(
            LogLevelEnum.Error,
            f"Build failed: {Exc}",
            True,
            -1,
        )
