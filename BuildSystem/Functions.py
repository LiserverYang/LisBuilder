# Copyright 2025, LiserverYang. All rights reserved.

from .FilePermissionsEnum import FilePermissionsEnum
from .SystemEnum import SystemEnum
from .FileSystem import FileIO
from .BuildContext import BuildContext
from .Config import LLVMConfig
from .Logger import Logger
from .LogLevelEnum import LogLevelEnum

import importlib
import importlib.util
import sys
import subprocess


def GetCurrentSystem() -> SystemEnum:
    """
    Get the kind of current operating system.
    """

    match sys.platform:
        case "win32":
            return SystemEnum.Windows
        case "linux":
            return SystemEnum.Linux
        case "darwin":
            return SystemEnum.MacOS

    return SystemEnum.Other


def HasPermissions(PermissionsNumber: int, Permissions: FilePermissionsEnum) -> bool:
    """
    Return if PermissionsNumber has permission, Permissions.
    """

    return (PermissionsNumber & Permissions.value) == Permissions.value


def AddPermissions(PermissionsNumber: int, Permissions: FilePermissionsEnum) -> int:
    """
    Add permission, Permissions to PermissionsNumber and return a new PermissionsNumber
    """

    return PermissionsNumber | Permissions.value


def GetAllUnits(Folder: FileIO, Suffix: str) -> list[str]:
    """
    Get all units in folder.
    """

    # The result of the function
    Result: list[str] = []

    def helper(path):
        """
        To help search
        """

        tFileIO: FileIO = FileIO(path)

        if not tFileIO.Exists():
            return

        if tFileIO.FileName().endswith("." + Suffix + ".py"):
            Result.append(tFileIO.FilePathStr)

        if tFileIO.IsFolder():
            sub_files = tFileIO.GetSubFiles()
            for sub_file in sub_files:
                helper(sub_file)

    helper(Folder.FilePathStr)

    # Return value
    return Result


def GetClassFromFileIO(FilePath: FileIO, ClassName: str):
    """
    Get class from file path.
    """

    Spec = importlib.util.spec_from_file_location(ClassName, FilePath.FilePathStr)
    Module = importlib.util.module_from_spec(Spec)
    sys.modules[ClassName] = Module
    Spec.loader.exec_module(Module)

    return getattr(Module, ClassName)


def GetInformations():
    """
    All informations like system type, compiler version.
    """

    BuildContext.SystemType = GetCurrentSystem()

    try:
        BuildContext.GccVersionStr = (
            subprocess.check_output(["gcc", "--version"])
            .decode("utf-8")
            .split("\n")[0]
            .split(" ")[-1]
        )
        SplitedGccVersion = BuildContext.GccVersionStr.split(".")
        BuildContext.GccVersion = [
            int(SplitedGccVersion[0]),
            int(SplitedGccVersion[1]),
            int(SplitedGccVersion[2]),
        ]
    except (FileNotFoundError, subprocess.CalledProcessError, IndexError, ValueError):
        Logger.Log(
            LogLevelEnum.Error,
            "gcc not found or not on PATH. Please install MinGW and add it to PATH.",
            True,
            -1,
        )

    try:
        BuildContext.GxxVersionStr = (
            subprocess.check_output(["g++", "--version"])
            .decode("utf-8")
            .split("\n")[0]
            .split(" ")[-1]
        )
        SplitedGxxVersion = BuildContext.GxxVersionStr.split(".")
        BuildContext.GxxVersion = [
            int(SplitedGxxVersion[0]),
            int(SplitedGxxVersion[1]),
            int(SplitedGxxVersion[2]),
        ]
    except (FileNotFoundError, subprocess.CalledProcessError, IndexError, ValueError):
        Logger.Log(
            LogLevelEnum.Error,
            "g++ not found or not on PATH. Please install MinGW and add it to PATH.",
            True,
            -1,
        )

    import os

    if os.name == "nt":
        try:
            BuildContext.GxxPosition = subprocess.check_output(
                ["where", "g++"], text=True, encoding="utf-8", errors="ignore"
            ).strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            BuildContext.GxxPosition = ""
    else:
        try:
            BuildContext.GxxPosition = subprocess.check_output(
                ["which", "g++"], text=True
            ).strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            BuildContext.GxxPosition = ""
