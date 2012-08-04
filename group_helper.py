#! /usr/bin/env python
from subprocess_helper import getCmd
import config
import dircache
import os

def groupExists(groupname):
	return os.path.exists(getPathForGroup(groupname))

def getPathForGroup(groupname):
	groupPath = config.GROUPS_DIR + "/" + groupname
	return groupPath

def getIssueIdsInGroups():
	ret = {};
	for group in dircache.listdir(config.GROUPS_DIR):
		if not group == ".gitignore":
			filepath = config.GROUPS_DIR + "/" + group
			with open(filepath, 'rb') as f:
				lines = f.readlines()
				ret[group] = [line.rstrip() for line in lines]
	
	return ret

def getGroupsForIssueId(issueID):
	groupPaths = getCmd("git grep --name-only " 
				+ issueID + " -- " + config.GROUPS_DIR)

	groups = []
	pathPrefix = config.GROUPS_DIR[len(config.GIT_ROOT) + 1:] # +1 to remove '/'
	if groupPaths != None:
		for path in groupPaths.splitlines():
			groupname = path[len(pathPrefix) + 1:] # +1 to remove '/'
			groups.extend([groupname]) 
	
	return groups

def addIssueToGroup(issueID, groupname):
	path = getPathForGroup(groupname)
	try:
		with open(path, "rb") as f:
			lines = f.read()
			if lines.count(issueID):
				# Issue already in group
				return None
	except IOError:
		# Group doesn't exist yet... carry on.
		pass
	
	# Issue not already in group, so add it
	with open(path, "ab") as f:
		f.write(issueID + "\n")

def rmIssueInGroup(issueID, groupname):
	with open(getPathForGroup(groupname), "rb") as f:
		lines = f.readlines()
		groupIDs = [line.rstrip() for line in lines]
	
	# If we're removing the last issue in a file, then rm the file
	if len(groupIDs) == 1 and groupIDs[0] == issueID:
		# HACK HACK HACK
		# Should not be executing a git command here
		getCmd('git rm "' + getPathForGroup(groupname) + '"')
	else:
		with open(getPathForGroup(groupname), "wb") as f:
			for identifier in groupIDs:
				if not identifier == issueID:
					f.write(identifier + "\n")

		# HACK HACK HACK
		# Should not be executing a git command here
		getCmd('git add "' + getPathForGroup(groupname) + '"')