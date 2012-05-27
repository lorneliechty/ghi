#! /usr/bin/env python
import config

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
	def writeEditableIssueToDisk(filepath, issue):
		with open(filepath, 'wb') as f:
			# Title with helper comment
			f.write('# TITLE: One line immediately below this comment' + '\n')
			f.write(issue.title + '\n')
			
			# Status with helper comment
			f.write("\n")
			f.write('# STATUS: One line immediately below this comment' + '\n')
			f.write('# Legal values are:' + '\n')
			statusOpts = config.STATUS_OPTS
			for val,status in statusOpts.iteritems():
				f.write('#\t' + str(val) + ': ' + status + '\n')
			f.write(str(issue.status) + '\n')
			
			# Description with helper comment
			f.write("\n")
			f.write('# DESCRIPTION: All lines below this comment' + '\n')
			f.write(issue.description + '\n')
		f.closed

	@staticmethod
	def readEditableIssueFromDisk(filepath):
		issue = Issue()
		with open(filepath, 'rb') as f:
			lines = f.readlines()
			n = 0
			for l in lines:
				if (l.find('#',0,1) == -1 
					and (n > 2 or not len(l.rstrip()) == 0)):
					
					if (n==0):
						issue.title = l.rstrip()
					elif (n==1):
						issue.status = l.rstrip()
					else:
						issue.description += l			
					n += 1
																
			# Remove any trailing new line
			issue.description = issue.description.rstrip()

		f.closed
		return issue
	
	@staticmethod
	def peakTitle(filepath):
		my = IssueFile
		with open(filepath, 'rb') as f:
			# Verify file type
			buf = f.readline().strip()
			if buf != my.FILE_TAG:
				print "FAIL!", buf
				return None
			
			# Status
			f.readline().strip()
			
			# Title
			return f.readline().strip()
		

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
	test()
