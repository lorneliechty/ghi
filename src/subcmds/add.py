#! /usr/bin/env python

from issue import Issue, IssueFile
import config
import identifiers
import subprocess
from subprocess_helper import getCmd

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

def execute(args):
	issue = None
	
	# First validate arguments
	if (args.title == None and args.description == None):
		# If no arguments, drop into interactive mode
		tmpFile = config.GHI_DIR + "/" + "ISSUE_EDIT";
		issue = Issue()
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
		return None
	
	else:
		# Create new issue
		issue = Issue();
		
		# Set title
		issue.title = args.title
		
		# Set description
		if (args.description):
			issue.description = args.description

	if (issue):
		# Adding an issue includes adding a new commit to the repository.
		# To make sure that our commit doesn't include anything other
		# than this issue, clean the working copy using git-stash
		getCmd("git stash --all")
		
		# Generate an issue ID and then write the issue file to disk
		issueID = str(identifiers.genNewIssueID())
		IssueFile.writeIssueToDisk(config.ISSUES_DIR + "/" + issueID, 
								   issue)
		
		# Add the issue to git
		getCmd("git add " + config.ISSUES_DIR + "/" + issueID)
		
		# Commit the issue add
		getCmd('git commit -m "ghi-add Issue #' + issueID[:7] + ': '
			+ issue.title + '"')
		
		# Now restore the working copy
		getCmd("git stash pop")
		
		# Display the new issue ID to the user
		print issueID