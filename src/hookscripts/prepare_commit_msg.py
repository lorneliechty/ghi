#! /usr/bin/env python

try:
	from identifiers import getPathFromId
	from issue import IssueFile
	from subprocess_helper import getCmd
	import config
except:
	print "Cannot find necessary modules / packages in $PYTHONPATH"
	print "Please inspect current path"
	quit()

def prependGhiCommitMsg(commitMsgFilepath):
	"""Examines the git index that is about to be committed and 
	adds auto-generated commit message lines into the git commit
	message to represent any ghi related changes."""
	
	relIssuesPath = config.ISSUES_DIR[len(config.GIT_ROOT) + 1:] # +1 to remove '/'
	relGroupsPath = config.GROUPS_DIR[len(config.GIT_ROOT) + 1:] # +1 to remove '/'

	# Find any .ghi files in the index
	ghiMods = getCmd('git diff --cached --name-status -- ' 
					+ config.GHI_DIR).split('\n')
	
	if len(ghiMods) == 1 and ghiMods[0] == '':
		# Nothing of interest in index... bail
		return None
	
	# Build a set of suggested commit message lines based on the
	# changes to .ghi files in the index
	commitMsg=['\n']
	for mod in ghiMods:
		m = mod.split()

		# if file was an issue
		if m[1].count(relIssuesPath):
			
			issueID = m[1][len(relIssuesPath)+1:]

			# if issue was added
			if m[0] == 'A':
				commitMsg.extend(["# " + buildGhiAddMsg(issueID) + "\n"])
			# if issue was modified
			elif m[0] == 'M':
				commitMsg.extend(["# " + buildGhiEditMsg(issueID) + "\n"])
			# if issue was deleted
			elif m[0] == 'D':
				commitMsg.extend(["# " + buildGhiRmMsg(issueID) + "\n"])
				
		elif m[1].count(relGroupsPath):
			
			groupname = m[1][len(relGroupsPath)+1:]
			
			# Run through the group file and see exactly what was done.
			diff = getCmd("git diff --cached -- " + m[1]).split('\n')
			for line in diff:
				# Issue added
				if line[0] == '+' and not line[0:3] == '+++':
					commitMsg.extend(["# " + 
							buildGhiGroupAddMsg(groupname, line[1:]) + "\n"])
				# Issue removed
				if line[0] == '-' and not line[0:3] == '---':
					commitMsg.extend(["# " + 
							buildGhiGroupRmMsg(groupname, line[1:]) + "\n"])
			
	# Add the existing commit message (usually a default git template)
	with open(commitMsgFilepath, 'rb') as f:
		commitMsg.extend(f.readlines())
	
	# Now write out the full message
	with open(commitMsgFilepath, 'wb') as f:
		for line in commitMsg:
			f.write(line)

def buildGhiAddMsg(issueID):
	return "ghi-add Issue #" + issueID[:7] + ": " + IssueFile.peakTitle(getPathFromId(issueID))

def buildGhiEditMsg(issueID):
	return "ghi-edit Issue #" + issueID[:7] + ": " + IssueFile.peakTitle(getPathFromId(issueID))

def buildGhiRmMsg(issueID):
	return "ghi-rm Issue #" + issueID[:7]

def buildGhiGroupAddMsg(groupname, issueID):
	return "ghi-group Issue #" + issueID[:7] + ' added to group "' + groupname + '"'

def buildGhiGroupRmMsg(groupname, issueID):
	return "ghi-group Issue #" + issueID[:7] + ' removed from group "' + groupname + '"'

if __name__ == "__main__":
	import sys
	prependGhiCommitMsg(sys.argv[1])
	