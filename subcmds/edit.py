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

from Issue import IssueFile
from subprocess_helper import getCmd
import commit_helper
import config
import identifiers
import subprocess

NAME="edit"
HELP="Edit an existing issue"

class Args:
	"""Wrapper class that defines the command line args"""
	ID="id"
	ID_HELP="Issue ID"
	
	OPT_TITLE="--title"
	OPT_TITLE_SHORT="-t"
	OPT_TITLE_HELP="One line issue title"
	
	OPT_DESCRIPTION="--description"
	OPT_DESCRIPTION_SHORT="-d"
	OPT_DESCRIPTION_HELP="Description"

	OPT_STATUS="--status"
	OPT_STATUS_SHORT="-s"
	OPT_STATUS_HELP="Status"

def execute(args):
	
	# First validate arguments
	issueID = identifiers.getFullIssueIdFromLeadingSubstr(args.id)
	if issueID == None:
		# ID is required... no good
		return None

	# Load the existing issue
	issue = IssueFile.readIssueFromDisk(
							config.ISSUES_DIR + "/" + issueID);
	
	# Are we going to use interactive editing?	
	if args.status == None and args.title == None and args.description == None:
		tmpFile = config.GHI_DIR + "/" + "ISSUE_EDIT";
		IssueFile.writeEditableIssueToDisk(tmpFile, issue)
		tmpFileHash = getCmd("git hash-object " + tmpFile)

		subprocess.call([config.GIT_EDITOR, tmpFile])
		issue = IssueFile.readEditableIssueFromDisk(tmpFile)
		
		# Check to see if the tmpFile is unchanged
		if (tmpFileHash == getCmd("git hash-object " + tmpFile)):
			print "No change in Issue data. Issue not updated"
			return None
	
	# Set the status
	if args.status:
		# There is a potential bug here in situations where there is 
		# more than one status with the same value name
		statusUpdate = None
		for k,v in config.STATUS_OPTS.iteritems():
			if args.status == v:
				statusUpdate = k
				break
		
		if statusUpdate != None:
			issue.setStatus(statusUpdate)
		else:
			print "Status does not exist!"
			return None
	
	# Set title
	if args.title:
		issue.setTitle(args.title)
	
	# Set description
	if args.description:
		issue.setDescription(args.description)
	
	# Make changes to index for commit
	issuepath = config.ISSUES_DIR + "/" + issueID
	IssueFile.writeIssueToDisk(issuepath, issue)
	commit_helper.addToIndex(issuepath)
