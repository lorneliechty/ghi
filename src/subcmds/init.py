	#! /usr/bin/env python

import config
import os
from subprocess_helper import getCmd
import commit_helper

NAME="init"
HELP="give git issues"

class Args:
	"""Wrapper class that defines the command line args"""
	OPT_GHI_PATH="--ghi_path"
	OPT_GHI_PATH_HELP="Path to ghi install"

def execute(args):
	bFileAdd = False
		
	# Check to see if the .ghi directories have already been created
	# If it doesn't exist, create it.
	if os.path.isdir(config.GHI_DIR) == False:
		os.makedirs(config.GHI_DIR)
		_writeGhiDirGitIgnoreFile(config.GHI_DIR + "/.gitignore")
		bFileAdd = True

	if os.path.isdir(config.ISSUES_DIR) == False:
		os.makedirs(config.ISSUES_DIR)
		# Touch a .gitignore file in the ISSUES_DIR so that we can
		# track the directory in git before any issues get added
		getCmd("touch " + config.ISSUES_DIR + "/.gitignore")
		bFileAdd = True
	
	if bFileAdd:
		commit_helper.cleanWcAndCommitGhiDir("Initializing ghi")

	# Alias "git issue" to ghi
	if (args.ghi_path):
		getCmd("git config alias.issue '!" + args.ghi_path + "'")
	else:
		getCmd("git config alias.issue '!ghi'")
		
	# Clever successful response message... in the future it would
	# be nice if running 'ghi-init' on a git that already has issues
	# would give you a summary of stats on the current issues of that
	# git
	print "Initialized ghi, but this git currently has no issues"

def _writeGhiDirGitIgnoreFile(filepath):
	with open(filepath, 'wb') as f:
		f.write("ISSUE_EDIT\n")
	f.close()