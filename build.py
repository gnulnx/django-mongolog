#!/usr/bin/env python
import os
import subprocess

COPY_PATH = os.path.expanduser(
    os.path.abspath(
        os.environ.get("MONGOLOG_COPY_PATH", "./")
    )
)
if not COPY_PATH:
    raise ValueError("You muse set MONGOLOG_COPY_PATH")

Commands = (
    "rm -rf dist",
    "python setup.py sdist",
)

for cmd in Commands:
    print("running:", " ".join(cmd.split()))
    subprocess.check_output(cmd.split())

# Now copy the file over
cmd = "cp ./dist/%s  %s" % (os.listdir("dist")[0], COPY_PATH)
subprocess.check_output(cmd.split())
