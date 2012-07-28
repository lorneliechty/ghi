#! /usr/bin/env python

import subprocess

def getCmd(cmd):
	return subprocess.Popen(
		cmd,
		shell=True,
		stdin=subprocess.PIPE,
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		close_fds=True).stdout.read().strip()

