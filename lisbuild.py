# Copyright 2026, LiserverYang. All rights reserved.
#
# lisbuild — the Lis project build tool (cargo-style).
#
# Usage:
#   python lisbuild.py new <name> [--dir <path>]     scaffold a project
#   python lisbuild.py build [dir] [--lisc <path>] [--clean]
#   python lisbuild.py run [dir] [--lisc <path>] [-- args...]
#   python lisbuild.py test [dir] [--lisc <path>]
#   python lisbuild.py clean [dir]
#
# `dir` defaults to the current directory. lisc.exe is found via --lisc,
# the LISC env var, or PATH (its stdlib must sit next to it: <dir>/lstdlib).

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import argparse
import shutil

from BuildSystem import LisProject
from BuildSystem.Logger import Logger
from BuildSystem.LogLevelEnum import LogLevelEnum


def main() -> int:
    parser = argparse.ArgumentParser(prog="lisbuild", description="Build Lis projects.")
    sub = parser.add_subparsers(dest="command", required=True)

    pNew = sub.add_parser("new", help="scaffold a new project")
    pNew.add_argument("name")
    pNew.add_argument("--dir", default=".", help="parent directory (default: cwd)")

    def addCommon(p):
        p.add_argument("dir", nargs="?", default=".", help="project directory (default: cwd)")
        p.add_argument("--lisc", default="", help="path to lisc.exe (default: LISC env / PATH)")

    pBuild = sub.add_parser("build", help="compile the project")
    addCommon(pBuild)
    pBuild.add_argument("--clean", action="store_true", help="remove artefacts first")

    pRun = sub.add_parser("run", help="build and run the project")
    addCommon(pRun)

    pTest = sub.add_parser("test", help="run test/*.lis cases")
    addCommon(pTest)

    pClean = sub.add_parser("clean", help="remove build artefacts")
    pClean.add_argument("dir", nargs="?", default=".", help="project directory (default: cwd)")

    args = parser.parse_args()

    if args.command == "new":
        return 0 if LisProject.newProject(args.name, args.dir) else 1

    projectDir = os.path.abspath(args.dir)

    if args.command == "clean":
        buildDir = os.path.join(projectDir, "build")
        shutil.rmtree(buildDir, ignore_errors=True)
        Logger.Log(LogLevelEnum.Info, f"Removed '{buildDir}'.")
        return 0

    lisc = LisProject.findLisc(getattr(args, "lisc", ""))
    if not lisc:
        return 1

    if args.command == "build":
        return 0 if LisProject.buildProject(projectDir, lisc, args.clean) else 1
    if args.command == "run":
        return LisProject.runProject(projectDir, lisc, [])
    if args.command == "test":
        fails = LisProject.testProject(projectDir, lisc)
        return 0 if fails == 0 else 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
