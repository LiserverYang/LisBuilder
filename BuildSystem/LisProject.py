# Copyright 2026, LiserverYang. All rights reserved.
#
# LisProject.py — build a LIS-LANGUAGE project (cargo-style workflow):
# one entry `.lis` file compiled by `lisc.exe`, linked with the system g++,
# run / tested / scaffolded by the lisbuild CLI.
#
# A Lis project is deliberately simple: the entry file is the ONLY compilation
# unit — every other file is a module loaded by the compiler through `impt`
# (lisc searches the entry file's directory, so local modules need no config).
# `lisproject.json` (all fields optional) can override defaults:
#
#   {
#     "name": "myproj",          // default: the project directory's name
#     "main": "main.lis",        // default: "main.lis"
#     "include_dirs": ["lib"],   // extra `-I` module search dirs (project-relative)
#     "opt": 0                   // lisc optimisation level 0-3, default 0
#   }
#
# Layout:
#   myproj/
#     lisproject.json
#     main.lis          # entry; `impt ...` loads local modules
#     lib/…             # local modules (found via the entry's own directory)
#     test/…            # `lisbuild test`: each file is a standalone program
#     build/            # artefacts (gitignored): <name>.o + <name>.exe

from .FileSystem import FileIO
from .Functions import GetCurrentSystem
from .Logger import Logger
from .LogLevelEnum import LogLevelEnum
from .SystemEnum import SystemEnum
from .TimeSolver import FormatDuration

import json
import os
import shutil
import subprocess
import sys
import time

_ExeSuffix = ".exe" if GetCurrentSystem() == SystemEnum.Windows else ""


def _exeName(name: str) -> str:
    return name + _ExeSuffix


def loadProject(projectDir: str) -> dict:
    """Read `<projectDir>/lisproject.json` (missing file → all defaults)."""
    projectDir = os.path.abspath(projectDir)
    manifest = os.path.join(projectDir, "lisproject.json")
    cfg = {"name": os.path.basename(projectDir), "main": "main.lis",
           "include_dirs": [], "opt": 0}
    if os.path.isfile(manifest):
        with open(manifest, encoding="utf-8") as f:
            user = json.load(f)
        for key in cfg:
            if key in user:
                cfg[key] = user[key]
    if not isinstance(cfg["include_dirs"], list):
        cfg["include_dirs"] = [cfg["include_dirs"]]
    return cfg


def findLisc(cliLisc: str = "") -> str:
    """Locate lisc.exe: --lisc flag > LISC env var > PATH. Verifies the
    compiler's stdlib lives next to it (lisc requires `<exe dir>/lstdlib`)."""
    candidates = []
    if cliLisc:
        candidates.append(cliLisc)
    if os.environ.get("LISC"):
        candidates.append(os.environ["LISC"])
    found = shutil.which("lisc") or shutil.which("lisc.exe")
    if found:
        candidates.append(found)
    for cand in candidates:
        if os.path.isfile(cand):
            lisc = os.path.abspath(cand)
            if not os.path.isdir(os.path.join(os.path.dirname(lisc), "lstdlib")):
                Logger.Log(
                    LogLevelEnum.Error,
                    f"lisc at '{lisc}' has no stdlib next to it (expected <dir>/lstdlib).",
                )
                return ""
            return lisc
    Logger.Log(
        LogLevelEnum.Error,
        "cannot find lisc.exe - pass --lisc <path>, set the LISC env var, or add it to PATH.",
    )
    return ""


def _collectLisFiles(projectDir: str) -> list:
    """All .lis files under the project (excluding build artefacts)."""
    out = []
    for root, dirs, files in os.walk(projectDir):
        dirs[:] = [d for d in dirs if d != "build"]
        for f in files:
            if f.endswith(".lis"):
                out.append(os.path.join(root, f))
    return out


def buildProject(projectDir: str, lisc: str, clean: bool = False) -> bool:
    """Compile the project's entry into build/<name>.exe. Incremental: skipped
    when the exe is newer than every .lis source. Returns True on success."""
    cfg = loadProject(projectDir)
    projectDir = os.path.abspath(projectDir)
    mainLis = os.path.join(projectDir, cfg["main"])
    buildDir = os.path.join(projectDir, "build")
    exe = os.path.join(buildDir, _exeName(cfg["name"]))
    obj = os.path.join(buildDir, cfg["name"] + ".o")

    if not os.path.isfile(mainLis):
        Logger.Log(LogLevelEnum.Error, f"entry file not found: {mainLis}")
        return False

    os.makedirs(buildDir, exist_ok=True)
    if clean:
        for stale in (exe, obj):
            if os.path.exists(stale):
                os.remove(stale)

    # Incremental: exe newer than every source → nothing to do.
    if os.path.isfile(exe):
        exeTime = FileIO(exe).LastChange()
        newest = max((FileIO(f).LastChange() for f in _collectLisFiles(projectDir)),
                     default=0)
        if exeTime > newest:
            Logger.Log(LogLevelEnum.Info, f"'{cfg['name']}' is up to date (skipped).")
            return True

    # Compile the entry (the only compilation unit — modules are loaded by
    # lisc through impt; lisc's search order already covers the entry dir).
    cmd = [lisc, os.path.basename(cfg["main"]), "-o", str(cfg["opt"])]
    if cfg["include_dirs"]:
        cmd.extend(["-I", ";".join(cfg["include_dirs"])])

    StartTime = time.time()
    Logger.Log(LogLevelEnum.Info, f"Compiling '{cfg['main']}'.")
    comp = subprocess.run(cmd, cwd=projectDir, capture_output=True, text=True)
    if comp.stdout:
        print(comp.stdout, end="")
    if comp.stderr:
        print(comp.stderr, end="", file=sys.stderr)
    if comp.returncode != 0:
        Logger.Log(LogLevelEnum.Error, f"Compile failed with code {comp.returncode}.")
        return False

    # lisc writes ./a.o into the cwd — move it into build/.
    aObj = os.path.join(projectDir, "a.o")
    if os.path.isfile(aObj):
        shutil.move(aObj, obj)
    elif not os.path.isfile(obj):
        Logger.Log(LogLevelEnum.Error, "lisc produced no object file (a.o missing).")
        return False

    # Link with the system g++ (the established Lis convention).
    Logger.Log(LogLevelEnum.Info, "Linking.")
    link = subprocess.run(
        ["g++", "-o", exe, obj], capture_output=True, text=True)
    if link.stdout:
        print(link.stdout, end="")
    if link.stderr:
        print(link.stderr, end="", file=sys.stderr)
    if link.returncode != 0:
        Logger.Log(LogLevelEnum.Error, f"Link failed with code {link.returncode}.")
        return False

    Logger.Log(LogLevelEnum.Info, f"Built '{exe}' in {FormatDuration(time.time() - StartTime)}.")
    return True


def runProject(projectDir: str, lisc: str, args: list) -> int:
    """build + execute. Returns the program's exit code (1 if the build failed)."""
    if not buildProject(projectDir, lisc):
        return 1
    cfg = loadProject(projectDir)
    exe = os.path.join(os.path.abspath(projectDir), "build", _exeName(cfg["name"]))
    return subprocess.run([exe] + args).returncode


def testProject(projectDir: str, lisc: str) -> int:
    """Run `test/*.lis`: each file is a standalone program that must exit 0.
    Returns the number of failing cases."""
    projectDir = os.path.abspath(projectDir)
    testDir = os.path.join(projectDir, "test")
    if not os.path.isdir(testDir):
        Logger.Log(LogLevelEnum.Warning, "no test/ directory — nothing to run.")
        return 0
    cases = sorted(f for f in FileIO(testDir).GetSubFiles() if f.endswith(".lis"))
    if not cases:
        Logger.Log(LogLevelEnum.Warning, "no .lis files in test/ — nothing to run.")
        return 0

    tmp = os.path.join(projectDir, "build", "test_tmp")
    os.makedirs(tmp, exist_ok=True)
    fails = 0
    for case in cases:
        name = os.path.splitext(os.path.basename(case))[0]
        obj = os.path.join(tmp, name + ".o")
        exe = os.path.join(tmp, _exeName(name))
        comp = subprocess.run(
            [lisc, os.path.abspath(case), "-o", "0", "-I", projectDir],
            cwd=tmp, capture_output=True, text=True)
        if comp.returncode != 0:
            if comp.stdout:
                print(comp.stdout, end="")
            if comp.stderr:
                print(comp.stderr, end="", file=sys.stderr)
            Logger.Log(LogLevelEnum.Error, f"test '{name}': compile failed.")
            fails += 1
            continue
        aObj = os.path.join(tmp, "a.o")
        if os.path.isfile(aObj):
            shutil.move(aObj, obj)
        link = subprocess.run(["g++", "-o", exe, obj], capture_output=True, text=True)
        if link.returncode != 0:
            Logger.Log(LogLevelEnum.Error, f"test '{name}': link failed.")
            fails += 1
            continue
        run = subprocess.run([exe], capture_output=True, text=True)
        if run.returncode == 0:
            Logger.Log(LogLevelEnum.Info, f"test '{name}': ok.")
        else:
            Logger.Log(LogLevelEnum.Error, f"test '{name}': exited {run.returncode}.")
            fails += 1

    Logger.Log(LogLevelEnum.Info,
               f"{len(cases) - fails}/{len(cases)} test cases passed.")
    shutil.rmtree(tmp, ignore_errors=True)
    return fails


_TemplateMain = """// {name} — generated by lisbuild new.

fn main() -> i32
{{
    print_str("hello from {name}\\n");
    ret 0;
}}
"""

_TemplateGitignore = """build/
"""


def newProject(name: str, parentDir: str) -> bool:
    """Scaffold `<parentDir>/<name>`: entry main.lis + lisproject.json + .gitignore."""
    root = os.path.join(os.path.abspath(parentDir), name)
    if os.path.exists(root):
        Logger.Log(LogLevelEnum.Error, f"'{root}' already exists.")
        return False
    os.makedirs(root)
    with open(os.path.join(root, "main.lis"), "w", encoding="utf-8") as f:
        f.write(_TemplateMain.format(name=name))
    with open(os.path.join(root, "lisproject.json"), "w", encoding="utf-8") as f:
        json.dump({"name": name, "main": "main.lis", "include_dirs": [], "opt": 0},
                  f, indent=4)
        f.write("\n")
    with open(os.path.join(root, ".gitignore"), "w", encoding="utf-8") as f:
        f.write(_TemplateGitignore)
    Logger.Log(LogLevelEnum.Info, f"Created project '{name}' at '{root}'.")
    Logger.Log(LogLevelEnum.Info, "Next: lisbuild build " + root)
    return True
