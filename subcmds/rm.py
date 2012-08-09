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
		if issueID == None:
			print "Could not find issue: " + args.id
			return None
		
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
		