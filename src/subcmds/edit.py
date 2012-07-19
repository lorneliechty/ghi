#! /usr/bin/env python

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

def execute(args):
	
	# First validate arguments
	issueID = identifiers.getFullIssueIdFromLeadingSubstr(args.id)
	if (issueID == None):
		# ID is required... no good
		return None

	# Load the existing issue
	issue = IssueFile.readIssueFromDisk(
							config.ISSUES_DIR + "/" + issueID);
	
	# Are we going to use interactive editing?	
	if (args.title == None and args.description == None):
		tmpFile = config.GHI_DIR + "/" + "ISSUE_EDIT";
		IssueFile.writeEditableIssueToDisk(tmpFile, issue)
		tmpFileHash = getCmd("git hash-object " + tmpFile)

		subprocess.call([config.GIT_EDITOR, tmpFile])
		issue = IssueFile.readEditableIssueFromDisk(tmpFile)
		
		# Check to see if the tmpFile is unchanged
		if (tmpFileHash == getCmd("git hash-object " + tmpFile)):
			print "No change in Issue data. Issue not updated"
			return None
		
	# Set title
	if (args.title):
		issue.title = args.title
	
	# Set description
	if (args.description):
		issue.description = args.description
	
	# Make changes to index for commit
	issuepath = config.ISSUES_DIR + "/" + issueID
	IssueFile.writeIssueToDisk(issuepath, issue)
	commit_helper.addToIndex(issuepath)
