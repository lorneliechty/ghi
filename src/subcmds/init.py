	#! /usr/bin/env python

import config
import os
from subprocess_helper import getCmd

NAME="init"
HELP="give git issues"

class Args:
	"""Wrapper class that defines the command line args"""
	OPT_GHI_PATH="--ghi_path"
	OPT_GHI_PATH_HELP="Path to ghi install"

def execute(args):
	# Check to see if the .ghi directories have already been created
	# If it doesn't exist, create it.
	if os.path.isdir(config.GHI_DIR) == False:
		os.makedirs(config.GHI_DIR)
		os.makedirs(config.ISSUES_DIR)
		
		_writeGhiDirGitIgnoreFile(config.GHI_DIR + "/.gitignore")

	elif os.path.isdir(config.ISSUES_DIR) == False:
		os.makedirs(config.ISSUES_DIR)

	# Alias "git issue" to ghi
	if (args.ghi_path):
		getCmd("git config alias.issue '!" + args.ghi_path + "'")
	else:
		getCmd("git config alias.issue '!ghi'")

def _writeGhiDirGitIgnoreFile(filepath):
	with open(filepath, 'wb') as f:
		f.write("ISSUE_EDIT\n")
	f.close()