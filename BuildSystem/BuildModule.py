# Copyright 2025, LiserverYang. All rights reserved.

from .BuildContext import BuildContext
from .Logger import Logger
from .LogLevelEnum import LogLevelEnum
from .FileSystem import FileIO
from .BinaryTypeEnum import BinaryTypeEnum
from .Functions import GetCurrentSystem
from .SystemEnum import SystemEnum
from .TestModule import TestModule, GetTestExePath
from .FormatCheck import CheckFormat, FormatFile
from .ModuleBase import ModuleBase

from typing import List, Tuple

import glob
import subprocess
import concurrent.futures
import hashlib
import os
import re
import sys
import threading
import platform


# --------------------------------------------------------------------------- #
# Transient status line
# --------------------------------------------------------------------------- #
#
# A single "bottom line" that is overwritten every time a new source file
# starts compiling, the way ninja / cmake show progress. Writes go through
# a lock because the compile pool is multi-threaded.

_StatusLock = threading.Lock()
_StatusLastLen: int = 0


def _PrintStatus(Text: str) -> None:
    """Overwrite the transient status line with ``Text``."""
    global _StatusLastLen
    with _StatusLock:
        Padding = max(0, _StatusLastLen - len(Text))
        sys.stdout.write("\r" + Text + (" " * Padding))
        sys.stdout.flush()
        _StatusLastLen = len(Text)


def _ClearStatus() -> None:
    """Erase the transient status line so the next real print starts clean."""
    global _StatusLastLen
    with _StatusLock:
        if _StatusLastLen > 0:
            sys.stdout.write("\r" + (" " * _StatusLastLen) + "\r")
            sys.stdout.flush()
            _StatusLastLen = 0


# --------------------------------------------------------------------------- #
# Short hash (used to disambiguate same-named sources in one module)
# --------------------------------------------------------------------------- #


def _ShortHash(Text: str, Length: int = 8) -> str:
    return hashlib.md5(Text.encode("utf-8")).hexdigest()[:Length]


def _StableSourceKey(SourceFile: str) -> str:
    """
    cwd / drive-letter-case-stable identity for a source file.

    The hash is the only thing that distinguishes objects for same-named
    sources in one module, so its input must not change when the invocation
    cwd or the drive-letter spelling changes — otherwise every build recompiles
    everything under a new hash and orphans the old objects forever.

    Anchor to ``BuildContext.RootPath`` (the repo root) and lower-case the
    drive via ``os.path.normcase`` on Windows.
    """
    AbsSource: str = os.path.abspath(SourceFile)
    RootPath: str = getattr(BuildContext, "RootPath", "")
    if RootPath:
        try:
            Relative: str = os.path.relpath(AbsSource, RootPath)
            if not Relative.startswith(".."):
                AbsSource = os.path.normpath(os.path.join(RootPath, Relative))
        except ValueError:
            pass  # different drive: keep the absolute path
    return os.path.normcase(AbsSource)


# --------------------------------------------------------------------------- #
# Platform helpers
# --------------------------------------------------------------------------- #


def _ExecutableSuffix() -> str:
    return ".exe" if GetCurrentSystem() == SystemEnum.Windows else ""


def _DynamicLibSuffix() -> str:
    return ".dll" if GetCurrentSystem() == SystemEnum.Windows else ".so"


# --------------------------------------------------------------------------- #
# CUDA Helpers
# --------------------------------------------------------------------------- #
def _IsCudaFile(file: str) -> bool:
    """判断是否是 CUDA 源文件 .cu"""
    return file.lower().endswith(".cu")

def _CudaObjectFilePath(middle_dir: str, source: str) -> str:
    """CUDA 目标文件路径"""
    base = FileIO(source).FileName()
    hash_str = _ShortHash(_StableSourceKey(source))
    return f"{middle_dir}/{base}.{hash_str}.cubin.o"

def _FindCudaPath() -> str:
    """尝试查找 CUDA 安装路径"""
    if GetCurrentSystem() == SystemEnum.Windows:
        return os.environ.get("CUDA_PATH", "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA")
    else:
        return "/usr/local/cuda"


# --------------------------------------------------------------------------- #
# Source discovery
# --------------------------------------------------------------------------- #


def _CollectSourceFiles(RootFolder: FileIO) -> Tuple[List[str], List[str], List[str]]:
    """
    Recursively collect C and C++ source files under ``RootFolder``.

    :returns: ``(c_files, cpp_files)``
    """
    CFiles: List[str] = []
    CppFiles: List[str] = []
    CuFiles: List[str] = []

    def Walk(Folder: FileIO) -> None:
        for SubFileStr in Folder.GetSubFiles():
            SubFile: FileIO = FileIO(SubFileStr)
            if SubFile.IsFolder():
                Walk(SubFile)
                continue

            Ext = SubFile.EndsWith()
            if Ext == ".cpp" or Ext == ".cc":
                CppFiles.append(SubFile.FilePathStr)
            elif Ext == ".c":
                CFiles.append(SubFile.FilePathStr)
            elif Ext == ".cu":
                CuFiles.append(SubFile.FilePathStr)

    Walk(RootFolder)
    return CFiles, CppFiles, CuFiles


def _CollectFormatFiles(ModuleRoot: str) -> List[str]:
    """All C/C++/CUDA sources and headers under *ModuleRoot*.

    The format check/format step covers EVERY file of the module (not just the
    ones that happen to recompile this run) — with cached objects the old
    fresh-only set was empty, so `--enable-format-check` silently checked
    nothing on an up-to-date tree.
    """
    Extensions = (".c", ".cc", ".cpp", ".cu", ".h", ".hpp")
    Files: List[str] = []
    for DirPath, _DirNames, FileNames in os.walk(ModuleRoot):
        for Name in FileNames:
            if Name.endswith(Extensions):
                Files.append(os.path.join(DirPath, Name))
    return Files


# --------------------------------------------------------------------------- #
# Intermediate file paths
# --------------------------------------------------------------------------- #


def _ObjectFilePath(MiddleFilesDir: str, SourceFile: str) -> str:
    Base = FileIO(SourceFile).FileName()
    Hash = _ShortHash(_StableSourceKey(SourceFile))
    return f"{MiddleFilesDir}/{Base}.{Hash}.o"


def _DependencyFilePath(MiddleFilesDir: str, SourceFile: str) -> str:
    Base = FileIO(SourceFile).FileName()
    Hash = _ShortHash(_StableSourceKey(SourceFile))
    return f"{MiddleFilesDir}/{Base}.{Hash}.d"


# --------------------------------------------------------------------------- #
# Header-dependency tracking
# --------------------------------------------------------------------------- #


def _ParseDependencyFile(DepFilePath: str) -> List[str]:
    """
    Parse a ``.d`` dependency file produced by ``gcc/g++`` with
    ``-MMD -MP -MF``.

    The Make-style format looks like::

        target.o: src.cpp /path/to/header1.h \\
          /path/to/header2.h

        /path/to/header1.h:
        /path/to/header2.h:

    The trailing "phony" entries come from ``-MP`` and are harmless here
    because we only look at the RHS of the first colon.

    :returns: the list of header / source paths the object depends on
        (the right-hand side of the first rule). An empty list is
        returned if the file does not exist or cannot be read.
    """
    DepFile = FileIO(DepFilePath)
    if not DepFile.Exists():
        return []

    try:
        with open(DepFilePath, "r", encoding="UTF-8") as Handle:
            Content = Handle.read()
    except OSError:
        return []

    # Collapse line continuations so we can split on whitespace.
    Content = Content.replace("\\\r\n", " ").replace("\\\n", " ")

    # The rule delimiter is the first colon FOLLOWED BY WHITESPACE. A naive
    # `Content.find(":")` matches the drive letter in the absolute paths we now
    # emit after RootPath anchoring (e.g. "F:/..."), which corrupts the parse
    # and makes every object look stale. Drive colons are always followed by
    # '/' or '\', never whitespace, so the lookahead is unambiguous.
    RuleMatch = re.search(r":(?=\s)", Content)
    if not RuleMatch:
        return []
    ColonIndex = RuleMatch.start()

    # Everything up to the next newline is the first rule's dependency
    # list. Subsequent lines (from -MP) are phony targets we ignore.
    FirstRule = Content[ColonIndex + 1 :].split("\n", 1)[0]
    return [Token for Token in FirstRule.split() if Token]


def _ResolveDepPath(Dependency: str) -> str:
    """
    Resolve a path listed inside a ``.d`` file.

    ``gcc`` writes the compiled source as a *relative* path when it was given
    one on the command line (``Source/Compiler/Private/...``), while headers
    come back absolute. Resolving the relative form against the repo root
    makes the freshness check independent of the invocation cwd.
    """
    if os.path.isabs(Dependency):
        return Dependency
    RootPath: str = getattr(BuildContext, "RootPath", "")
    if RootPath:
        return os.path.abspath(os.path.join(RootPath, Dependency))
    return os.path.abspath(Dependency)


def _ObjectIsUpToDate(
    SourceFile: str,
    ObjectFile: FileIO,
    MiddleFilesDir: str,
) -> bool:
    """
    Decide whether ``ObjectFile`` can be reused without recompiling
    ``SourceFile``.

    An object is stale if:
      * it does not exist, or
      * the source file is newer than the object, or
      * any header listed in the matching ``.d`` file is newer than
        the object, or
      * any header listed in the matching ``.d`` file has disappeared
        (forces a safe rebuild).
    """
    if not ObjectFile.Exists():
        return False

    SourceTime = FileIO(SourceFile).LastChange()
    ObjectTime = ObjectFile.LastChange()

    if SourceTime >= ObjectTime:
        return False

    DepFilePath = _DependencyFilePath(MiddleFilesDir, SourceFile)
    for Dependency in _ParseDependencyFile(DepFilePath):
        DepFile = FileIO(_ResolveDepPath(Dependency))
        if not DepFile.Exists():
            return False
        if DepFile.LastChange() >= ObjectTime:
            return False

    return True


# --------------------------------------------------------------------------- #
# Output path helpers
# --------------------------------------------------------------------------- #


def _EntryPointOutputPath(BinaryFilesDir: str, TargetName: str) -> str:
    return f"{BinaryFilesDir}/{TargetName}{_ExecutableSuffix()}"


def _DynamicLibOutputPath(BinaryFilesDir: str, LibPrefix: str, ModuleName: str) -> str:
    return f"{BinaryFilesDir}/{LibPrefix}{ModuleName}{_DynamicLibSuffix()}"


def _StaticLibOutputPath(BinaryFilesDir: str, LibPrefix: str, ModuleName: str) -> str:
    return f"{BinaryFilesDir}/lib{LibPrefix}{ModuleName}.a"


# --------------------------------------------------------------------------- #
# Up-to-date checks (target vs its inputs)
# --------------------------------------------------------------------------- #
#
# The whole-module skip must only fire when the TARGET is actually newer than
# every input (objects + dependency artifacts). Without this, a deleted source
# or a deleted/stale target would be silently skipped and lisc.exe would keep
# linking old members — the bug CLAUDE.md used to paper over with a manual
# `rm -rf`.


def _TargetIsUpToDate(
    TargetPath: str,
    ObjectPaths: List[str],
    ExtraInputPaths: List[str],
) -> bool:
    """True iff ``TargetPath`` exists and is newer than every input."""
    if not os.path.exists(TargetPath):
        return False
    TargetTime: float = os.stat(TargetPath).st_mtime
    for Obj in ObjectPaths:
        if not os.path.exists(Obj):
            return False
        if os.stat(Obj).st_mtime >= TargetTime:
            return False
    for Extra in ExtraInputPaths:
        # Absent extras (e.g. libMagicEnum.a, which is never produced) are fine.
        if not os.path.exists(Extra):
            continue
        if os.stat(Extra).st_mtime >= TargetTime:
            return False
    return True


def _DependArtifacts(
    ModuleConfiguration: ModuleBase,
    TargetName: str,
    BinaryFilesDir: str,
    OnlyStaticLibs: bool = False,
) -> List[str]:
    """Artifact paths of every linkable dependency of *ModuleConfiguration*.

    This is the single source of truth reused by the up-to-date check, the
    archive member set and the link command (``-l`` names at the call site).

    :param OnlyStaticLibs: when True, only StaticLib dependencies are returned
        — the ones whose ``.a`` gets appended *into* this module's archive.
    """
    Paths: List[str] = []
    for Name in ModuleConfiguration.ModulesDependOn:
        DependConfig: ModuleBase = BuildContext.ModuleConfiguration[
            BuildContext.BuildOrder.index(Name)
        ]
        if not DependConfig.LinkThisModule:
            continue
        Prefix: str = f"{TargetName}-" if DependConfig.EnableBinaryLibPrefix else ""
        if DependConfig.BinaryType == BinaryTypeEnum.StaticLib:
            Paths.append(_StaticLibOutputPath(BinaryFilesDir, Prefix, Name))
        elif (
            DependConfig.BinaryType == BinaryTypeEnum.DynamicLib
            and not OnlyStaticLibs
        ):
            Paths.append(_DynamicLibOutputPath(BinaryFilesDir, Prefix, Name))
    return Paths


def _ArchiveMemberNames(ArchivePath: str) -> set:
    """Member basenames via ``ar t``; empty set if missing/unreadable."""
    if not os.path.exists(ArchivePath):
        return set()
    Result = subprocess.run(
        ["ar", "t", ArchivePath], capture_output=True, text=True
    )
    if Result.returncode != 0:
        return set()
    return {Line.strip() for Line in Result.stdout.splitlines() if Line.strip()}


def _ArchiveMemberSetMatches(
    ArchivePath: str,
    OwnObjectPaths: List[str],
    DependArtifacts: List[str],
) -> bool:
    """Whether *ArchivePath*'s members match the expected set.

    ``ar rcs`` replaces same-name members but never removes members that are no
    longer passed in, so an archive silently keeps objects of deleted/renamed
    sources. We detect that by diffing ``ar t`` against the expected members.

    Required ⊆ Actual ⊆ Allowed:

    * Required — every own object basename must be a member.
    * Allowed — required ∪ {dep archive basenames} ∪ {dep archive members},
      which tolerates GNU ar BOTH nesting an ``.a`` operand (observed: the dep
      archive appears as one member) and inlining its members. Only members
      that are provably stale (old-hash orphans, deleted/renamed sources) are
      flagged.
    """
    Required: set = {os.path.basename(p) for p in OwnObjectPaths}
    Allowed: set = set(Required)
    for Dep in DependArtifacts:
        if not os.path.exists(Dep):
            continue
        Allowed.add(os.path.basename(Dep))
        Allowed |= _ArchiveMemberNames(Dep)
    Actual: set = _ArchiveMemberNames(ArchivePath)
    return Required.issubset(Actual) and Actual.issubset(Allowed)


def _ModuleTargetUpToDate(
    ModuleConfiguration: ModuleBase,
    TargetOutputPath: str,
    AllObjectPaths: List[str],
    DependArtifacts: List[str],
) -> bool:
    """mtime freshness + (for StaticLib) archive member-set integrity."""
    if not _TargetIsUpToDate(TargetOutputPath, AllObjectPaths, DependArtifacts):
        return False
    if ModuleConfiguration.BinaryType == BinaryTypeEnum.StaticLib:
        return _ArchiveMemberSetMatches(
            TargetOutputPath, AllObjectPaths, DependArtifacts
        )
    return True


def _CleanupOrphanObjects(
    MiddleFilesDir: str, CurrentObjectPaths: List[str]
) -> None:
    """Delete ``.o``/``.d`` files in *MiddleFilesDir* owned by no current source.

    Permanently removes old-hash orphans (from before the stable-key fix) and
    objects of deleted sources. Idempotent afterwards.
    """
    if not os.path.isdir(MiddleFilesDir):
        return
    Expected: set = set()
    for Obj in CurrentObjectPaths:
        Base: str = os.path.basename(Obj)
        Expected.add(Base)
        # "Foo.cpp.<hash>.o" -> "Foo.cpp.<hash>.d"
        # "Foo.cu.<hash>.cubin.o" -> "Foo.cu.<hash>.d" (nvcc dep path has no .cubin)
        if Base.endswith(".cubin.o"):
            Expected.add(Base[: -len(".cubin.o")] + ".d")
        else:
            Expected.add(Base[:-2] + ".d")
    for Name in os.listdir(MiddleFilesDir):
        if not (Name.endswith(".o") or Name.endswith(".d")):
            continue
        if Name in Expected:
            continue
        try:
            os.remove(os.path.join(MiddleFilesDir, Name))
        except OSError:
            pass


def _TestsNeedUpdate(TestPath: str, TestExePath: str) -> bool:
    """Whether the gtest binary must be rebuilt and re-run.

    True when the binary is missing or any ``Tests/*.cpp`` is newer than it.
    This lets a SKIPPED module still re-run tests after a test-only change or
    a previously failed test run — without it, the whole-module skip would
    silently swallow both.
    """
    if not os.path.exists(TestExePath):
        return True
    TestTime: float = os.stat(TestExePath).st_mtime
    for Src in glob.glob(os.path.join(TestPath, "*.cpp")):
        if FileIO(Src).LastChange() >= TestTime:
            return True
    return False


# --------------------------------------------------------------------------- #
# Main entry
# --------------------------------------------------------------------------- #


def BuildModule(ModuleName: str):
    """
    Build a module.

    ATTENTION: the module must have been discovered by the build system.

    :param ModuleName: the name of the module
    :type ModuleName: str
    """

    ModuleID: int = BuildContext.BuildOrder.index(ModuleName)
    ModuleConfiguration: ModuleBase = BuildContext.ModuleConfiguration[ModuleID]
    TargetName: str = BuildContext.TargetName

    if not ModuleConfiguration.BuildThisModule:
        return

    # --- Verify dependencies were built before this module --------------- #
    for Depend in ModuleConfiguration.ModulesDependOn:
        if not BuildContext.BuildedModule[BuildContext.BuildOrder.index(Depend)]:
            Logger.Log(
                LogLevelEnum.Error,
                f"Module '{ModuleName}' depend on module '{Depend}', "
                f"but it didn't build.",
                True,
                -1,
            )

    Logger.Log(
        LogLevelEnum.Info,
        f"[{ModuleID + 1}/{len(BuildContext.BuildOrder)}] "
        f"Building module '{ModuleName}'",
    )

    # --- Directory layout ------------------------------------------------- #
    # Anchor to the repo root so the build works from any cwd.
    RootPath: str = getattr(BuildContext, "RootPath", "")
    BuildRoot: str = os.path.join(RootPath, "Build") if RootPath else "./Build"
    MiddleFilesDir: str = f"{BuildRoot}/Intermediate/{TargetName}/{ModuleName}"
    BinaryFilesDir: str = f"{BuildRoot}/Binaries"

    os.makedirs(MiddleFilesDir, exist_ok=True)
    os.makedirs(BinaryFilesDir, exist_ok=True)

    # --- Discover sources ------------------------------------------------- #
    ModuleRoot: str = os.path.dirname(
        os.path.abspath(
            os.path.join(RootPath, BuildContext.ModulePath[ModuleID])
        )
    )
    WaitCompileCFilesList, WaitCompileCppFilesList, WaitCompileCuFilesList = _CollectSourceFiles(
        FileIO(f"{ModuleRoot}/Private/")
    )

    COFilesList: List[str] = []
    CxxOFilesList: List[str] = []
    CuOFilesList: List[str] = []

    # Every object this module expects for its current source list — used by
    # the whole-module skip and the archive member-set check, and to purge
    # orphaned .o/.d files from deleted/renamed sources.
    AllObjectPaths: List[str] = [
        _ObjectFilePath(MiddleFilesDir, f)
        for f in WaitCompileCFilesList + WaitCompileCppFilesList
    ] + [
        _CudaObjectFilePath(MiddleFilesDir, f)
        for f in WaitCompileCuFilesList
    ]
    if not BuildContext.Arguments.donot_build_files:
        _CleanupOrphanObjects(MiddleFilesDir, AllObjectPaths)

    # --- Prune sources whose objects are already up to date --------------- #
    # This is where header-dependency tracking kicks in: _ObjectIsUpToDate
    # consults the matching .d file produced by a previous compile.
    if not BuildContext.Arguments.donot_use_o_files:
        FreshCFiles: List[str] = []
        FreshCppFiles: List[str] = []
        FreshCuFiles: List[str] = []

        for File in WaitCompileCFilesList:
            ObjectPath = _ObjectFilePath(MiddleFilesDir, File)
            if _ObjectIsUpToDate(File, FileIO(ObjectPath), MiddleFilesDir):
                COFilesList.append(ObjectPath)
            else:
                FreshCFiles.append(File)

        for File in WaitCompileCppFilesList:
            ObjectPath = _ObjectFilePath(MiddleFilesDir, File)
            if _ObjectIsUpToDate(File, FileIO(ObjectPath), MiddleFilesDir):
                CxxOFilesList.append(ObjectPath)
            else:
                FreshCppFiles.append(File)

        for File in WaitCompileCuFilesList:
            ObjectPath = _CudaObjectFilePath(MiddleFilesDir, File)
            if _ObjectIsUpToDate(File, FileIO(ObjectPath), MiddleFilesDir):
                CuOFilesList.append(ObjectPath)
            else:
                FreshCuFiles.append(File)

        WaitCompileCFilesList = FreshCFiles
        WaitCompileCppFilesList = FreshCppFiles
        WaitCompileCuFilesList = FreshCuFiles

    # --- Decide the final output path for this module -------------------- #
    LibPrefix: str = (
        f"{TargetName}-" if ModuleConfiguration.EnableBinaryLibPrefix else ""
    )

    if ModuleConfiguration.BinaryType == BinaryTypeEnum.EntryPoint:
        TargetOutputPath = _EntryPointOutputPath(BinaryFilesDir, TargetName)
    elif ModuleConfiguration.BinaryType == BinaryTypeEnum.DynamicLib:
        TargetOutputPath = _DynamicLibOutputPath(BinaryFilesDir, LibPrefix, ModuleName)
    else:
        TargetOutputPath = _StaticLibOutputPath(BinaryFilesDir, LibPrefix, ModuleName)

    TargetExists: bool = FileIO(TargetOutputPath).Exists()

    # --- Assemble compile flags ------------------------------------------ #
    # Computed BEFORE the skip check: the skip path may still need to rebuild
    # and re-run the gtest binary (see _TestsNeedUpdate below).
    CStanderd: str = ModuleConfiguration.CStanderd
    CxxStanderd: str = ModuleConfiguration.CxxStanderd
    ModuleAddedArguments: str = " ".join(ModuleConfiguration.ArgumentsAdded)
    TargetAddedArguments: str = " ".join(BuildContext.TargetConfiguration.ArgumentsAdded)
    HostArgumentsAdded: List = ModuleConfiguration.ArgumentsAdded + BuildContext.TargetConfiguration.ArgumentsAdded
    HostAddedArguments: str = " ".join(HostArgumentsAdded)
    HostAddedArgumentsSplited: str = ",".join(HostArgumentsAdded)

    IncludePaths: str = " -I".join(
        os.path.abspath(
            os.path.dirname(
                BuildContext.ModulePath[BuildContext.BuildOrder.index(Depend)]
            )
            + "/Public/"
        )
        for Depend in ModuleConfiguration.ModulesDependOn + [ModuleName]
    )

    # -l flags for every linkable dependency.
    DependsModules: List[str] = []
    for Name in ModuleConfiguration.ModulesDependOn:
        DependConfig: ModuleBase = BuildContext.ModuleConfiguration[
            BuildContext.BuildOrder.index(Name)
        ]
        if not DependConfig.LinkThisModule:
            continue
        if DependConfig.EnableBinaryLibPrefix:
            DependsModules.append(f"{TargetName}-{Name}")
        else:
            DependsModules.append(Name)

    LinkDependsStr: str = " ".join(f"-l{Name}" for Name in DependsModules)

    # Add CUDA link flags if this module or any dependency uses CUDA
    AnyModuleUsesCuda = ModuleConfiguration.UseCUDA or any(
        BuildContext.ModuleConfiguration[BuildContext.BuildOrder.index(Name)].UseCUDA
        for Name in ModuleConfiguration.ModulesDependOn
    )
    if AnyModuleUsesCuda:
        LinkDependsStr += " -L/usr/local/cuda/lib64/ -lcudart"

    # --- Format check / auto-format -------------------------------------- #
    # Runs BEFORE the skip check: an up-to-date module used to bypass it, so
    # `--enable-format-check` silently checked nothing locally (CI only worked
    # because a fresh checkout has no cached objects).
    if ModuleConfiguration.EnableFormatCheck:
        FormatFiles: List[str] = _CollectFormatFiles(ModuleRoot)
        if BuildContext.Arguments.format:
            # Format-only mode: reformat every file in place, then stop.
            for File in FormatFiles:
                if FormatFile(File) != 0:
                    Logger.Log(
                        LogLevelEnum.Error,
                        f"clang-format failed on {File}",
                        True,
                        -1,
                    )
            BuildContext.BuildedModule[ModuleID] = True
            return
        if BuildContext.Arguments.enable_format_check:
            for File in FormatFiles:
                if CheckFormat(File) != 0:
                    Logger.Log(
                        LogLevelEnum.Error,
                        f"Format check failed in file {File}, "
                        f"see log for detailed informations",
                        True,
                        1,
                    )

    # --- Can we skip this whole module? ---------------------------------- #
    AllDependsSkiped: bool = all(
        BuildContext.SkipedModule[BuildContext.BuildOrder.index(Depend)]
        for Depend in ModuleConfiguration.ModulesDependOn
    )
    NothingToCompile = (
        not WaitCompileCFilesList
        and not WaitCompileCppFilesList
        and not WaitCompileCuFilesList
    )

    DependArtifacts: List[str] = _DependArtifacts(
        ModuleConfiguration, TargetName, BinaryFilesDir
    )

    # The skip must NOT fire unless the target is actually newer than every
    # input AND (for StaticLib) the archive member set is still complete.
    # Without the member-set check, a deleted source would keep its stale
    # member in libCompiler.a forever and lisc.exe would keep linking it.
    ModuleUpToDate: bool = (
        NothingToCompile
        and AllDependsSkiped
        and TargetExists
        and _ModuleTargetUpToDate(
            ModuleConfiguration, TargetOutputPath, AllObjectPaths, DependArtifacts
        )
    )

    if ModuleConfiguration.AutoSkiped or ModuleUpToDate:
        BuildContext.BuildedModule[ModuleID] = True
        BuildContext.SkipedModule[ModuleID] = True
        # A skipped module may still need its tests: the gtest binary is
        # rebuilt fresh whenever it runs, so re-run when the binary is missing
        # or any Tests/*.cpp is newer — otherwise a test-only change or a
        # previously failed test run would silently never re-run.
        if (
            not ModuleConfiguration.AutoSkiped
            and BuildContext.Arguments.enable_tests
            and ModuleConfiguration.EnableTests
            and _TestsNeedUpdate(
                os.path.join(ModuleRoot, "Tests"),
                GetTestExePath(),
            )
        ):
            TestModule(
                ModuleName,
                ModuleRoot,
                CxxOFilesList,
                f"{ModuleAddedArguments} {TargetAddedArguments} "
                f"-I{IncludePaths} -L{BinaryFilesDir}/ {LinkDependsStr} "
                f"-l{LibPrefix}{ModuleName}",
                CxxStanderd,
            )
        return

    # --- Per-source compile commands ------------------------------------- #
    def TransformCommand(BuildCommand: str, SourceName: str) -> dict:
        """
        Transform a build command into the clangd
        ``compile_commands.json`` schema.
        """
        return {
            "file": FileIO(SourceName).FileName(),
            "directory": os.path.abspath(os.path.dirname(SourceName)),
            "arguments": ["clang++"] + BuildCommand.split(" ")[1:-1],
        }

    CompileCommands: List[Tuple[str, str]] = []  # (source_file, command)

    for CFile in WaitCompileCFilesList:
        ObjectPath = _ObjectFilePath(MiddleFilesDir, CFile)
        DepPath = _DependencyFilePath(MiddleFilesDir, CFile)
        COFilesList.append(ObjectPath)

        BuildCommand: str = (
            f"gcc {CFile} -o {ObjectPath} -std={CStanderd} "
            f"-MMD -MP -MF {DepPath} "
            f"{ModuleAddedArguments} {TargetAddedArguments} "
            f"-I{IncludePaths} -c"
        )
        BuildContext.CompileCommands.append(TransformCommand(BuildCommand, CFile))
        CompileCommands.append((CFile, BuildCommand))

    cuda_path = _FindCudaPath()
    cuda_include = f"{cuda_path}/include"

    for CppFile in WaitCompileCppFilesList:
        ObjectPath = _ObjectFilePath(MiddleFilesDir, CppFile)
        DepPath = _DependencyFilePath(MiddleFilesDir, CppFile)
        CxxOFilesList.append(ObjectPath)

        # NOTE: the CUDA include is appended conditionally, but `-c` and
        # `-I{IncludePaths}` are ALWAYS present. An earlier version wrapped the
        # whole trailing clause in a ternary (`... if UseCuda else " "`), which
        # dropped `-c` and the include paths for non-CUDA targets and silently
        # produced empty objects (g++ compiled-but-didn't-link without -c).
        BuildCommand: str = (
            f"g++ {CppFile} -o {ObjectPath} -std={CxxStanderd} "
            f"-MMD -MP -MF {DepPath} "
            f"{ModuleAddedArguments} {TargetAddedArguments} "
            f"-I{IncludePaths} -c"
        )
        if BuildContext.TargetConfiguration.UseCuda:
            BuildCommand += f" -I'{cuda_include}'"
        BuildContext.CompileCommands.append(TransformCommand(BuildCommand, CppFile))
        CompileCommands.append((CppFile, BuildCommand))

    if ModuleConfiguration.UseCUDA:
        cuda_arch = ModuleConfiguration.CudaArch

        for CuFile in WaitCompileCuFilesList:
            ObjPath = _CudaObjectFilePath(MiddleFilesDir, CuFile)
            DepPath = _DependencyFilePath(MiddleFilesDir, CuFile)
            CuOFilesList.append(ObjPath)

            build_cmd = (
                f"{cuda_path}/bin/nvcc {CuFile} -o {ObjPath} -c -std={CxxStanderd} --compiler-bindir /usr/bin/gcc-12 "
                f"-arch=sm_{cuda_arch} --expt-relaxed-constexpr "
                f"-Xcompiler='-MMD,-MP,-MF,{DepPath}' "
                f"-I{IncludePaths} -I'{cuda_include}' "
                f"-Xcompiler='{HostAddedArgumentsSplited},-Wno-attributes' "
            )

            CompileCommands.append((CuFile, build_cmd))

    # --- Run compile commands in parallel -------------------------------- #
    if not BuildContext.Arguments.donot_build_files and CompileCommands:

        def RunCompileCommand(Job: Tuple[str, str]):
            SourceFile, Cmd = Job
            _PrintStatus(f"Compiling {SourceFile}")

            Result = subprocess.run(
                Cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="UTF-8",
            )
            if Result.returncode != 0:
                return (False, Cmd, Result.stderr)
            return (True, Cmd, "")

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=BuildContext.Arguments.threads
        ) as Executor:
            Futures = {
                Executor.submit(RunCompileCommand, Job): Job for Job in CompileCommands
            }

            for Future in concurrent.futures.as_completed(Futures):
                Success, Cmd, Error = Future.result()
                if Success:
                    continue

                # Cancel everything still pending and fail loudly.
                for Pending in Futures:
                    Pending.cancel()
                _ClearStatus()
                print(Error.replace("\n\n", "\n"))
                Logger.Log(
                    LogLevelEnum.Error,
                    f"Compile failed when running command {Cmd}, "
                    f"see error in the log.",
                    True,
                    -1,
                )

        _ClearStatus()

    if BuildContext.Arguments.donot_build_files:
        BuildContext.BuildedModule[ModuleID] = True
        return

    # --- Link step -------------------------------------------------------- #
    ObjectsStr: str = " ".join(COFilesList + CxxOFilesList + CuOFilesList)
    BuildResult: int = 0

    if ModuleConfiguration.BinaryType == BinaryTypeEnum.EntryPoint:
        LinkCommand = (
            f"g++ {ObjectsStr} "
            f"-o {_EntryPointOutputPath(BinaryFilesDir, TargetName)} "
            f"-L{BinaryFilesDir}/ {LinkDependsStr} "
            f"{ModuleAddedArguments} {TargetAddedArguments}"
        )
        BuildResult = os.system(LinkCommand)

    elif ModuleConfiguration.BinaryType == BinaryTypeEnum.DynamicLib:
        LinkCommand = (
            f"g++ {ObjectsStr} "
            f"-o {_DynamicLibOutputPath(BinaryFilesDir, LibPrefix, ModuleName)} "
            f"-L{BinaryFilesDir}/ {LinkDependsStr} -fPIC -shared "
            f"{ModuleAddedArguments} {TargetAddedArguments}"
        )
        BuildResult = os.system(LinkCommand)

    else:  # StaticLib
        StaticLibPath = _StaticLibOutputPath(BinaryFilesDir, LibPrefix, ModuleName)
        OwnObjectPaths: List[str] = COFilesList + CxxOFilesList + CuOFilesList
        StaticDependArtifacts: List[str] = _DependArtifacts(
            ModuleConfiguration, TargetName, BinaryFilesDir, OnlyStaticLibs=True
        )

        if _ModuleTargetUpToDate(
            ModuleConfiguration,
            StaticLibPath,
            OwnObjectPaths,
            DependArtifacts,
        ):
            # Archive is already fresh (mtime) and its member set is complete:
            # nothing to do — the fast no-op path.
            BuildResult = 0
        else:
            # The member set changed (source deleted/renamed) → GNU ar rewrites
            # the whole archive on any mutation anyway, so recreate it from
            # scratch to drop stale members instead of leaving them behind.
            if os.path.exists(StaticLibPath) and not _ArchiveMemberSetMatches(
                StaticLibPath, OwnObjectPaths, DependArtifacts
            ):
                os.remove(StaticLibPath)

            LinkCommand = f"ar rcs {StaticLibPath} {ObjectsStr}"
            for Dep in StaticDependArtifacts:
                if os.path.exists(Dep):
                    LinkCommand += f" {Dep}"
            BuildResult = os.system(LinkCommand)

    if BuildResult == 0:
        BuildContext.BuildedModule[ModuleID] = True
    else:
        Logger.Log(
            LogLevelEnum.Error,
            f"There's something error when build module '{ModuleName}' in "
            f"target '{TargetName}', and the compiler return value "
            f"'{BuildResult}' not 0.",
            True,
            -1,
        )

    # --- Tests ----------------------------------------------------------- #
    if BuildContext.Arguments.enable_tests and ModuleConfiguration.EnableTests:
        TestModule(
            ModuleName,
            os.path.dirname(BuildContext.ModulePath[ModuleID]),
            CxxOFilesList,
            f"{ModuleAddedArguments} {TargetAddedArguments} "
            f"-I{IncludePaths} -L{BinaryFilesDir}/ {LinkDependsStr} "
            f"-l{LibPrefix}{ModuleName}",
            ModuleConfiguration.CxxStanderd,
        )
