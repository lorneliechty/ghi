#! /usr/bin/env python

from identifiers import getFullIssueIdFromLeadingSubstr
import commit_helper

NAME = "rm"
HELP = "Remove an issue"

class Args:
	"""Wrapper class that defines the command line args"""
	ID="id"
	ID_HELP="Issue ID"

def execute(args):
	if (args.id):
		issueID = getFullIssueIdFromLeadingSubstr(args.id)
		commit_helper.cleanWcAndDeleteIssue(issueID)
		