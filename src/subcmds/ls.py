#! /usr/bin/env python

from group_helper import getIssueIdsInGroups
from Issue import IssueDisplayBuilder
import config
import dircache
import identifiers

NAME = "ls"
HELP = "List issues"

class Args:
	"""Wrapper class that defines the command line args"""
	ID="id"
	ID_HELP="Issue ID"
	ID_NARGS="?"
	
	OPT_GROUPED="--group"
	OPT_GROUPED_HELP="List issues by group"
	OPT_GROUPED_ACTION="store_true"
	
	OPT_SORT="--sort"
	OPT_SORT_HELP="Sort issues"

def execute(args):
	if args.id:
		issueId = identifiers.getFullIssueIdFromLeadingSubstr(args.id)
		print IssueDisplayBuilder(issueId).getFullIssueDisplay()

	else:
		issueIDs = dircache.listdir(config.ISSUES_DIR)

		if args.group:
			_displayGrouped(issueIDs)		
		else:
			_displayUnGrouped(issueIDs)
			
def _displayUnGrouped(issueIDs):
	for issueID in issueIDs:	
		print IssueDisplayBuilder(issueID).getOneLineStr()

def _displayGrouped(issueIDs):
	groups = getIssueIdsInGroups()

	ungrouped = []
	for issueID in issueIDs:
		isUngrouped = True
		for g in groups:
			if groups[g].count(issueID):
				isUngrouped = False
				break
		if isUngrouped:
			ungrouped.extend([issueID])

	for g in groups:
		print g
		for issueID in groups[g]:
			print IssueDisplayBuilder(issueID).getOneLineStr()
		print ""
	
	print "ungrouped"
	for issueID in ungrouped: 
		print IssueDisplayBuilder(issueID).getOneLineStr()

if (__name__ == "__main__"):
	execute()