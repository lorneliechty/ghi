#! /usr/bin/env python

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
	OPT_DELETE_ACTION="store_true"

def execute(args):
	print args
	# Are we deleting an issue from an existing group?
	if args.d and not args.id == None and not args.groupname == None:
		issueID = identifiers.getFullIssueIdFromLeadingSubstr(args.id)
		group_helper.rmIssueInGroup(issueID, args.groupname)
		# HACK HACK HACK
		# Should be executing a git command here to add the
		# subsequent group changes to the index, but I'm taking
		# a shortcut for the moment
		return None
	
	# Are we deleting a group completely?
	elif args.d and args.id == None and not args.groupname == None:
		cmd = 'git rm "' + config.GROUPS_DIR + '/' + args.groupname + '"'
		print cmd
		#getCmd('git rm "' + config.GROUPS_DIR + '/' + args.groupname + '"')
		return None
	
	if args.groupname == None and args.id == None:
		for group in dircache.listdir(config.GROUPS_DIR):
			if not group == ".gitignore":
				print group
		return None
	
	if args.groupname == None:
		# We don't support this syntax yet
		return None
	
	# get the full issue ID & Add the issue to the group
	issueID = identifiers.getFullIssueIdFromLeadingSubstr(args.id)
	group_helper.addIssueToGroup(issueID, args.groupname)
	commit_helper.addToIndex('"' + group_helper.getPathForGroup(args.groupname) + '"')
