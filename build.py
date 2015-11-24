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
	"python setup.py sdist",
	"cp dist/django-mongolog-0.1.3.tar.gz  %s" % COPY_PATH,
)


for cmd in Commands:
	print "running %", cmd
	subprocess.check_output(cmd.split())


