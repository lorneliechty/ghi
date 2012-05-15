#! /usr/bin/env python

import config
import os

NAME="init"
HELP="give git issues"

def execute(args):
	# Check to see if the .ghi directories have already been created
	# If it doesn't exist, create it.
	if os.path.isdir(config.GHI_DIR) == False:
		os.makedirs(config.GHI_DIR)
		os.makedirs(config.ISSUES_DIR)
	elif os.path.isdir(config.ISSUES_DIR) == False:
		os.makedirs(config.ISSUES_DIR)
	else:
		print "This git already has issues."
