#! /usr/bin/env python

from Issue import IssueDisplayBuilder
from group_helper import getIssueIdsInGroups
from subprocess_helper import getCmd
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
		issueIDs = _getAllIssueIDs()
		if issueIDs == None:
			return

		if args.sort != None:
			issueIDs = _sortIssues(issueIDs, args.sort)

		if args.group:
			_displayGrouped(issueIDs)		
		else:
			_displayUnGrouped(issueIDs)
			
def _getAllIssueIDs():
	issueIDs = dircache.listdir(config.ISSUES_DIR)
	try:
		issueIDs.remove('.gitignore')
	except:	pass
	return issueIDs
			
def _sortIssues(issueIDs, sortBy):
	if sortBy != None and sortBy == 'status':
		issuesPathPrefix = config.ISSUES_DIR[len(config.GIT_ROOT) + 1:] # +1 to remove '/'

		# Organize the issues into status groups
		issuesWithStatus = []
		for sk in config.STATUS_OPTS:
			for i in getCmd('git grep -n ^' + str(sk) + '$ -- ' + config.ISSUES_DIR).splitlines():
				issuesWithStatus.extend([[sk, i.split(':')[0][len(issuesPathPrefix) + 1:]]]) # +1 to remove '/'

		# Sort by status
		issuesWithStatus.sort(key=lambda issue: issue[0])
		
		# return sorted IDs
		return map (lambda issueID: issueID[1], issuesWithStatus)
	
	return None
		
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