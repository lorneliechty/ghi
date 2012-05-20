#! /usr/bin/env python

class Issue:
	"""Class that represents an Issue"""
	title = r""
	description = r""

	status = 0

class IssueFile:
	"""Wraps all file I/O for Issues"""
	FIELD_DELIM = '\n'
	FILE_TAG = "ISSUE-1"

	@staticmethod
	def writeIssueToDisk(filepath, issue):
		my = IssueFile
		with open(filepath, 'wb') as f:
			f.write(my.FILE_TAG + my.FIELD_DELIM)
			f.write(str(issue.status) + my.FIELD_DELIM)
			f.write(issue.title + my.FIELD_DELIM)
			f.write(issue.description + my.FIELD_DELIM)
		f.closed

	@staticmethod
	def writeEditableIssueToDisk(filepath, issue):
		my = IssueFile
		with open(filepath, 'wb') as f:
			f.write(issue.title + my.FIELD_DELIM)
			f.write(issue.description + my.FIELD_DELIM)
		f.closed

	@staticmethod
	def readIssueFromDisk(filepath):
		my = IssueFile
		issue = Issue()
		with open(filepath, 'rb') as f:
			# Verify file type
			buf = f.readline().strip()
			if buf != my.FILE_TAG:
				print "FAIL!", buf
				return None
			
			# Status
			issue.status = f.readline().strip()
			# Title
			issue.title = f.readline().strip()
			
			# All remaining lines in the file are the issue description
			lines = f.readlines()
			for l in lines:
				issue.description += l
			# Remove any trailing new line
			issue.description = issue.description.rstrip()

		f.closed
		return issue
	
	@staticmethod
	def readEditableIssueFromDisk(filepath):
		issue = Issue()
		with open(filepath, 'rb') as f:
			lines = f.readlines()
			n = 0
			for l in lines:
				if (l.find('#',0,1) == -1):
					if (n==0):
						issue.title = l.rstrip()
#					elif (n==1):
#						issue.status = l
					else:
						issue.description += l			
					n += 1
																
			# Remove any trailing new line
			issue.description = issue.description.rstrip()

		f.closed
		return issue
		

def test():
	startIssue = Issue()
	startIssue.title = "test issue title"
	startIssue.description = "test issue description\ntest desc line 2"
	print startIssue.status, startIssue.title, startIssue.description
	IssueFile.writeIssueToDisk("/Users/lorne/dev/personal/ghi/src/test-issue", startIssue)
	endIssue = IssueFile.readIssueFromDisk("/Users/lorne/dev/personal/ghi/src/test-issue")
	print endIssue.status, endIssue.title, endIssue.description
	#print startIssue.status, startIssue.title, startIssue.description

if __name__ == "__main__":
	import sys
	test()
