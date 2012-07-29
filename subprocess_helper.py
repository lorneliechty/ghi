#! /usr/bin/env python

import subprocess

def getCmd(cmd):
	ret = subprocess.Popen(
		cmd,
		shell=True,
		stdin=subprocess.PIPE,
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		close_fds=True).stdout.read().strip()
		
	# Check for null result
	if ret != '':
		return ret
	
	return None
