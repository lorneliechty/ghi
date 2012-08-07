#! /usr/bin/env python
#
# Copyright (C) 2012 Lorne Liechty
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from Issue import IssueDisplayBuilder
from group_helper import getIssueIdsInGroups
from pager import PageOutputBeyondThisPoint
from subprocess_helper import getCmd
import config
import dircache
import identifiers
import sys

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
		if len(issueIDs) == 0:
			return

		# We may have a lot of issues in the list that would make the output
		# run pretty long, therefore page it.
		PageOutputBeyondThisPoint()

		# Any sorting required?
		if args.sort != None:
			issueIDs = _sortIssues(issueIDs, args.sort)
			
		# Check to see if a default issue sort has been configured for this repository
		else:
			sort = getCmd('git config issue.ls.status')
			if sort != None:
				issueIDs = _sortIssues(issueIDs, sort)

		# Group arg can be passed as parameter or via configured default
		if args.group or getCmd('git config issue.ls.group') == 'true':
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
			issues = getCmd('git grep -n ^' + str(sk) + '$ -- ' + config.ISSUES_DIR)
			if issues != None:
				for i in issues.splitlines():
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
			sys.stdout.write(IssueDisplayBuilder(issueID).getOneLineStr() + '\n')
		print ""
	
	print "ungrouped"
	for issueID in ungrouped: 
		print IssueDisplayBuilder(issueID).getOneLineStr()

if (__name__ == "__main__"):
	execute()