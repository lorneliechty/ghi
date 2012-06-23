#! /usr/bin/env python

from color import Color
from group_helper import getIssueIdsInGroups
from issue import IssueFile
import config
import dircache

NAME = "ls"
HELP = "List issues"

class Args:
	"""Wrapper class that defines the command line args"""
	ID="id"
	ID_HELP="Issue ID"
	ID_NARGS="?"
	ID_DEFAULT="*"
	
	OPT_GROUPED="--group"
	OPT_GROUPED_HELP="List issues by group"
	OPT_GROUPED_ACTION="store_true"

def execute(args):
	if args.group:
		groups = getIssueIdsInGroups()
	
	issueIDs = dircache.listdir(config.ISSUES_DIR)

	ungrouped = []
	if args.group:
		for id in issueIDs:
			isUngrouped = True
			for g in groups:
				if groups[g].count(id):
					isUngrouped = False
					break
			if isUngrouped:
				ungrouped.extend([id])
	
	if args.group:
		for i,g in enumerate(groups):
			print g
			for id in groups[g]:
				displayIssue(id)
			print ""
		
		print "ungrouped"
		for id in ungrouped: displayIssue(id)
		
	else:
		for id in issueIDs:	displayIssue(id)

def displayIssue(id):
	print str(Color('yellow')) + id[:7] + str(Color('none')) + \
			"\t" + IssueFile.peakTitle(config.ISSUES_DIR + "/" + id)

if (__name__ == "__main__"):
	execute()