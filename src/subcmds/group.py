#! /usr/bin/env python

from issue import IssueFile
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
	OPT_DELETE_HELP="Delete a group"

def execute(args):

	if not args.d == None:
		getCmd("rm " + config.GROUPS_DIR + "/" + args.d)
		return None		
	
	if args.groupname == None and args.id == None:
		for group in dircache.listdir(config.GROUPS_DIR):
			if not group == ".gitignore":
				print group
		return None
	
	if args.groupname == None:
		# We don't support this syntax yet
		return None
	
	# Prep for commit
	commit_helper.prepForCommit()
	
	# get the full issue ID & Add the issue to the group
	issueID = identifiers.getFullIssueIdFromLeadingSubstr(args.id)
	group_helper.addIssueToGroup(issueID, args.groupname)
	commit_helper.addToIndex(group_helper.getPathForGroup(args.groupname))
	
	# Commit the changes
	commit_helper.commit('Issue #' + issueID[:7] 
						+ " added to group '" + args.groupname + "'")