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

from Issue import Issue
from identifiers import getFullIssueIdFromLeadingSubstr, getPathFromId
from subprocess_helper import getCmd
import commit_helper
import group_helper

NAME = "rm"
HELP = "Remove an issue"

class Args:
	"""Wrapper class that defines the command line args"""
	ID="id"
	ID_HELP="Issue ID"
	
	OPT_FORCE="--force"
	OPT_FORCE_SHORT="-f"
	OPT_FORCE_HELP="Force the removal of an issue. Useful if issue has never been committed"
	OPT_FORCE_ACTION="store_true"
	
	@staticmethod
	def addCmdToParser(parser):
		cmd_rm = parser.add_parser(NAME, 
								 help=HELP)
		
		cmd_rm.add_argument(Args.ID,
							help=Args.ID_HELP)
		
		cmd_rm.add_argument(Args.OPT_FORCE_SHORT,
							Args.OPT_FORCE,
							action=Args.OPT_FORCE_ACTION,
							help=Args.OPT_FORCE_HELP)
		
		cmd_rm.set_defaults(func=execute)

def execute(args):
	if (args.id):
		issueID = getFullIssueIdFromLeadingSubstr(args.id)
		if issueID == None:
			print "Could not find issue: " + args.id
			return None
		
		# See if we can remove this issue at all without a --force
		issuePath = getPathFromId(issueID)
		if not args.force:
			issueStatus = getCmd("git status --porcelain -- " + issuePath)
			if issueStatus and issueStatus[0] =='A':
				print "Cannot remove issue without --force"
				return None
		
		# Remove the issue from any groups that contained it
		groups = group_helper.getGroupsForIssueId(issueID)
		
		# If we're not forcing the remove, then we need to double-check
		# to make sure that we can actually remove the issue from each
		# group without breaking things
		for group in groups:
			if not group_helper.canRmIssueFromGroup(issueID,group,args.force):
				# Can't perform this operation without a force!
				print "Cannot remove issue from group '" + group + "' without --force"
				return None
				
		# All clear to remove the issue!... groups first if you please...
		for group in groups: 
			group_helper.rmIssueInGroup(issueID,group,args.force)
			# HACK HACK HACK
			# Should be executing a git command here to add the
			# subsequent group changes to the index, but I'm taking
			# a shortcut for the moment
		
		issueTitle = Issue(issueID).getTitle()
		
		# Remove the issue
		commit_helper.remove(issuePath, args.force)
		