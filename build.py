#!/usr/bin/env python
import os
import subprocess
import collections

COPY_PATH=os.path.os.path.expanduser(
	os.path.abspath(
		os.environ.get("MONGOLOG_COPY_PATH", None)
	)
)
if not COPY_PATH:
	raise ValueError("You muse set MONGOLOG_COPY_PATH")

Commands = (
    "rm -rf dist",
	"python setup.py sdist",
	"cp ./dist/%s  %s" % (os.listdir("dist")[0], COPY_PATH),
)


for cmd in Commands:
	print "running:", " ".join(cmd.split())
	subprocess.check_output(cmd.split())


