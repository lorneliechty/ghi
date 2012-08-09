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

from subprocess_helper import getCmd
import commit_helper
import config
import dircache
import group_helper
import identifiers

NAME = "group"
HELP = "group related issues"

class Args:
	"""Wrapper class that defines the command line args"""
	ID="id"
	ID_HELP="Issue ID"
	ID_NARGS="?"
	
	GROUPNAME="groupname"
	GROUPNAME_HELP="Group Name"
	GROUPNAME_NARGS="?"
	
	OPT_DELETE_SHORT="-d"
	OPT_DELETE_HELP="Delete an issue from a group or a group completely"

def execute(args):
	# Are we deleting something?
	if args.d != None:
		# see if we're deleting an existing issue from a group
		issueID = identifiers.getFullIssueIdFromLeadingSubstr(args.d)
		if issueID != None:
			# HACK HACK HACK
			# The command line parsing here is totally messed up and so
			# rather than using the groupname we have to pretend here
			# that the id is the groupname... the command line just
			# needs to be rewritten :(
			group_helper.rmIssueInGroup(issueID, args.id)
			
			# HACK HACK HACK
			# Should be executing a git command here to add the
			# subsequent group changes to the index, but I'm taking
			# a shortcut for the moment
			return None
		
		# see if we're deleting a group entirely
		if group_helper.groupExists(args.d):
			getCmd('git rm "' + group_helper.getPathForGroup(args.d) + '"')
			return None
		
		# tried to delete, but we couldn't figure out what...
		print "Could not delete " + args.d
		return None
	
	if args.groupname == None and args.id == None:
		for group in dircache.listdir(config.GROUPS_DIR):
			if not group == ".gitignore":
				print group
		return None
	
	if args.groupname == None:
		# We don't support this syntax yet
		print "Command not currently supported"
		return None
	
	# get the full issue ID & Add the issue to the group
	issueID = identifiers.getFullIssueIdFromLeadingSubstr(args.id)
	group_helper.addIssueToGroup(issueID, args.groupname)
	commit_helper.addToIndex('"' + group_helper.getPathForGroup(args.groupname) + '"')
