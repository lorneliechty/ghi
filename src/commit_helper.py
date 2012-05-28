#! /usr/bin/env python

from issue import IssueFile
from subprocess_helper import getCmd
import config
import inspect

def _getCallerModuleName():
	''''Get the name of the calling subcommand
	For more info on the basic idea see: http://stackoverflow.com/questions/1095543/get-name-of-calling-functions-module-in-python
	
	From the above, we're additionally grabbing the lowest level
	module name in the event that the command module was imported
	as part of a package (which is the case with our subcmds)'''
	
	# Note, we use a [2] to get the caller's caller here because
	# we assume that _getCallerModuleName is being called only
	# from a method within this module
	return inspect.getmodule((inspect.stack()[2])[0]
					).__name__.split('.')[-1]

def _stashWc():
	# Adding an issue includes adding a new commit to the repository.
	# To make sure that our commit doesn't include anything other
	# than this issue, clean the working copy using git-stash
	getCmd("git stash --all")

def _restoreWc():
	# Now restore the working copy
	getCmd("git stash pop")

def cleanWcAndCommitGhiDir(msg):
	'''Cleans the git working copy and creates a git commit for the
	whole .ghi directory'''
	
	_stashWc()
	
	getCmd("git add " + config.GHI_DIR)
	
	cmdName = _getCallerModuleName()
	getCmd('git commit -m "ghi-' + cmdName + ' ' + msg + '"')
	
	_restoreWc()

def cleanWcAndCommitIssue(issueID, issue):
	'''Cleans the git working copy and creates a git commit for an 
	individual issue'''
	issuePath = config.ISSUES_DIR + "/" + issueID

	_stashWc()
	
	# Write the issue file to disk
	IssueFile.writeIssueToDisk(issuePath, issue)
	
	# Add the issue to the git index
	getCmd("git add " + issuePath)
	
	# Commit the issue
	cmdName = _getCallerModuleName()
	getCmd('git commit -m "ghi-' + cmdName 
		+ ' Issue #' + issueID[:7] + ': ' + issue.title + '"')
	
	_restoreWc()
	
def cleanWcAndDeleteIssue(issueID):
	'''Cleans the git working copy and creates a git commit for an 
	individual issue'''
	issuePath = config.ISSUES_DIR + "/" + issueID
	issueTitle = IssueFile.peakTitle(issuePath)
	
	_stashWc()
	
	# Delete the issue
	getCmd("git rm " + issuePath)		
	
	# Commit the change
	cmdName = _getCallerModuleName()
	getCmd('git commit -m "ghi-' + cmdName 
		+ ' Issue #' + issueID[:7] + ': ' + issueTitle + '"')
	
	_restoreWc()
	