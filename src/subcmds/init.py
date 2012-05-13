#! /usr/bin/env python

import os
import subprocess

NAME="init"
HELP="give git issues"

def execute(args):
	# Get the git top-level directory
	GIT_ROOT = subprocess.Popen(
		'git rev-parse --show-toplevel',
		shell=True,
		stdin=subprocess.PIPE,
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		close_fds=True).stdout.read().strip()
	
	# Check to see if the .ghi directories have already been created
	# If it doesn't exist, create it.
	GHI_DIR = GIT_ROOT + '/.ghi'
	ISSUES_DIR = GHI_DIR + '/issues'
	if os.path.isdir(GHI_DIR) == False:
		os.makedirs(GHI_DIR)
		os.makedirs(ISSUES_DIR)
	elif os.path.isdir(ISSUES_DIR) == False:
		os.makedirs(ISSUES_DIR)
	else:
		print "This git already has issues."
