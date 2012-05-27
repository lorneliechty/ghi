#! /usr/bin/env python

from issue import IssueFile
from subprocess_helper import getCmd
import config
import inspect

def cleanWcAndCommitIssue(issueID, issue):
	'''Cleans the git working copy and creates a git commit for an 
	individual issue'''
	
	# Adding an issue includes adding a new commit to the repository.
	# To make sure that our commit doesn't include anything other
	# than this issue, clean the working copy using git-stash
	getCmd("git stash --all")
	
	# Write the issue file to disk
	IssueFile.writeIssueToDisk(config.ISSUES_DIR + "/" + issueID, issue)
	
	# Add the issue to the git index
	getCmd("git add " + config.ISSUES_DIR + "/" + issueID)
	
	# Get the name of the calling subcommand
	# For more info on the basic idea see: http://stackoverflow.com/questions/1095543/get-name-of-calling-functions-module-in-python
	# From the above, we're additionally grabbing the lowest level
	# module name in the event that the command module was imported
	# as part of a package (which is the case with our subcmds)
	cmdName = inspect.getmodule((inspect.stack()[1])[0]
					).__name__.split('.')[-1]

	# Commit the issue
	getCmd('git commit -m "ghi-' + cmdName 
		+ ' Issue #' + issueID[:7] + ': ' + issue.title + '"')
	
	# Now restore the working copy
	getCmd("git stash pop")
