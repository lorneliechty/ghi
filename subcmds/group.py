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

from groups import group
from groups.group import Group
from issues import identifiers
from subprocess_helper import getCmd
import commit_helper
import config
import dircache

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
	
	OPT_AUTO_COMMIT="--commit"
	OPT_AUTO_COMMIT_HELP="Auto-commit"
	
	OPT_DELETE_SHORT="-d"
	OPT_DELETE_HELP="Delete an issue from a group or a group completely"
	
	OPT_FORCE_DELETE_SHORT="-D"
	OPT_FORCE_DELETE_HELP="Force the deletion of an issue or group. Useful if issue or group has never been committed"
	
	@staticmethod
	def addCmdToParser(parser):
		cmd_group = parser.add_parser(NAME, help=HELP)
		
		cmd_group.add_argument(Args.ID,
							help=Args.ID_HELP,
							nargs=Args.ID_NARGS)
		
		cmd_group.add_argument(Args.GROUPNAME,
							help=Args.GROUPNAME_HELP,
							nargs=Args.GROUPNAME_NARGS)
		
		cmd_group.add_argument(Args.OPT_AUTO_COMMIT,
							 action="store_true",
							 help=Args.OPT_AUTO_COMMIT_HELP)
		
		cmd_group.add_argument(Args.OPT_DELETE_SHORT,
							help=Args.OPT_DELETE_HELP)
		
		cmd_group.add_argument(Args.OPT_FORCE_DELETE_SHORT,
							help=Args.OPT_FORCE_DELETE_HELP)
		
		cmd_group.set_defaults(func=execute)

def execute(args):
	# Are we deleting something?
	if args.d or args.D:
		
		# see if we're deleting an existing issue from a group
		issueToDelete = args.d if args.d else args.D
		issueID = identifiers.getFullIssueIdFromLeadingSubstr(issueToDelete)
		if issueID:
			force = False if args.d else True
			
			# If no groupname is given, then we will remove from all groups
			# ... notice the hack here where args.id is holding the groupname
			# due to the currently lame and hacky argparsing
			if not args.id:
				# Remove the issue from any groups that contained it
				groupnames = group.getGroupsForIssueId(issueID)
				
				if len(groupnames) == 0:
					print "No groups to delete issue from!"
					return None
				
				# If we're not forcing the remove, then we need to double-check
				# to make sure that we can actually remove the issue from each
				# group without breaking things
				for name in groupnames:
					if not Group(name)._canRmIssue(issueID,force):
						# Can't perform this operation without a force!
						print "Cannot delete issue from group '" + name + "' without force option, '-D'"
						return None
				
				# All clear to remove the issue!... groups first if you please...
				for name in groupnames: 
					Group(name).rmIssue(issueID,force)
					# HACK HACK HACK
					# Should be executing a git command here to add the
					# subsequent group changes to the index, but I'm taking
					# a shortcut for the moment

				return None
			
			# HACK HACK HACK
			# The command line parsing here is totally messed up and so
			# rather than using the groupname we have to pretend here
			# that the id is the groupname... the command line just
			# needs to be rewritten :(
			Group(args.id).rmIssue(issueID, force)
			
			# HACK HACK HACK
			# Should be executing a git command here to add the
			# subsequent group changes to the index, but I'm taking
			# a shortcut for the moment
			return None
		
		# see if we're deleting a group entirely
		if group.exists(args.d):
			print "groupname = " + args.d
			getCmd('git rm "' + Group(args.d).getPath() + '"')
			return None
		elif group.exists(args.D):
			print "groupname = " + args.D
			getCmd('git rm -f "' + Group(args.D).getPath() + '"')
			return None
		
		# tried to delete, but we couldn't figure out what...
		groupname = args.d if args.d else args.D
		print "Could not delete '" + groupname  + "' without force option, '-D'"
		return None
	
	if args.groupname == None and args.id == None:
		print "\n".join(group.getListOfAllGroups())
		return None
	
	if args.groupname == None:
		# We don't support this syntax yet
		print "Command not currently supported"
		return None
	
	# get the full issue ID & Add the issue to the group
	issueID = identifiers.getFullIssueIdFromLeadingSubstr(args.id)
	Group(args.groupname).addIssue(issueID)
	commit_helper.addToIndex('"' + Group(args.groupname).getPath() + '"')
	
	if args.commit:
		commit_helper.commit()
