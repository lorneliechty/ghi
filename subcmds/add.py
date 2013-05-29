#! /usr/bin/env python
#
# Copyright (C) 2012-2013 Lorne Liechty
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

from groups.group import Group
from issues import identifiers
from issues.issue import IssueFile, IssueProto
from utils.subprocess_helper import getCmd
import commit_helper
import config
import subprocess

NAME="add"
HELP="Add a new issue"

class Args:
	"""Wrapper class that defines the command line args"""
	TITLE="title"
	TITLE_NARGS="?"
	TITLE_HELP="One line issue title"
	
	OPT_DESCRIPTION="--description"
	OPT_DESCRIPTION_SHORT="-d"
	OPT_DESCRIPTION_HELP="Description"
	
	OPT_GROUP="--group"
	OPT_GROUP_SHORT="-g"
	OPT_GROUP_HELP="Group name"
	
	OPT_AUTO_COMMIT="--commit"
	OPT_AUTO_COMMIT_HELP="Auto-commit"
	
	@staticmethod
	def addCmdToParser(parser):
		cmd_add = parser.add_parser(NAME,
								    help=HELP)
		
		cmd_add.add_argument(Args.OPT_AUTO_COMMIT,
							 action="store_true",
							 help=Args.OPT_AUTO_COMMIT_HELP)
		
		cmd_add.add_argument(Args.OPT_GROUP_SHORT,
                             Args.OPT_GROUP,
							 help=Args.OPT_GROUP_HELP)
		
		cmd_add.add_argument(Args.TITLE,
							 nargs=Args.TITLE_NARGS,
							 help=Args.TITLE_HELP)
		
		cmd_add.add_argument(Args.OPT_DESCRIPTION_SHORT,
							 Args.OPT_DESCRIPTION,
							 help=Args.OPT_DESCRIPTION_HELP)

		cmd_add.set_defaults(func=execute)

def execute(args):
	issue = None
	
	# First validate arguments
	if (args.title == None and args.description == None):
		# If no arguments, drop into interactive mode
		tmpFile = config.GHI_DIR + "/" + "ISSUE_EDIT";
		issue = IssueProto()
		IssueFile.writeEditableIssueToDisk(tmpFile, issue)
		tmpFileHash = getCmd("git hash-object " + tmpFile)
		
		subprocess.call([config.GIT_EDITOR, tmpFile])
		issue = IssueFile.readEditableIssueFromDisk(tmpFile)
		
		# Check to see if the tmpFile is unchanged
		if (tmpFileHash == getCmd("git hash-object " + tmpFile)):
			print "Not enough data to create issue. No issue created."
			return None
	
	elif (args.title == None):
		# Title is required... no good
		print "An issue title is required. Try 'add' with no arguments for interactive mode"
		return None
	
	else:
		# Create new issue
		issue = IssueProto();
		
		# Set title
		issue.setTitle(args.title)
		
		# Set description
		if (args.description):
			issue.setDescription(args.description)

	if (issue):
		# Generate an issue ID
		issueID = str(identifiers.genNewIssueID())
		
		# Make changes to index for commit
		issuepath = config.ISSUES_DIR + "/" + issueID
		IssueFile.writeIssueToDisk(issuepath, issue)
		commit_helper.addToIndex(issuepath)
		
		if args.group:
			Group(args.group).addIssue(issueID)
			commit_helper.addToIndex(config.GROUPS_DIR + '/"' + args.group + '"')
		
		# Display the new issue ID to the user
		print issueID
		
		if args.commit:
			commit_helper.commit()
