#! /usr/bin/env python

from identifiers import getFullIssueIdFromLeadingSubstr
from subprocess_helper import getCmd
import config

NAME = "rm"
HELP = "Remove an issue"

class Args:
	"""Wrapper class that defines the command line args"""
	ID="id"
	ID_HELP="Issue ID"

def execute(args):
	if (args.id):
		issueID = getFullIssueIdFromLeadingSubstr(args.id)
		getCmd("git rm " + config.ISSUES_DIR + "/" + issueID)		

if (__name__ == "__main__"):
	execute()