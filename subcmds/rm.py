#! /usr/bin/env python

from group_helper import getGroupsForIssueId, rmIssueInGroup
from identifiers import getFullIssueIdFromLeadingSubstr, getPathFromId
from Issue import Issue
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
		issuePath = getPathFromId(issueID)
		issueTitle = Issue(issueID).getTitle()
		
		# Remove the issue
		commit_helper.remove(issuePath)
		
		# Remove the issue from any groups that contained it
		groups = getGroupsForIssueId(issueID)
		for group in groups: 
			rmIssueInGroup(issueID,group)
			# HACK HACK HACK
			# Should be executing a git command here to add the
			# subsequent group changes to the index, but I'm taking
			# a shortcut for the moment
		