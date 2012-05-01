#! /usr/bin/env python

class Issue:
    """Class that represents an Issue"""
    title = r""
    description = r""

    status = 0

class IssueFile:
	"""Wraps all file I/O for Issues"""
	FIELD_DELIM = "\n"
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
		return

	@staticmethod
	def readIssueFromDisk(filepath):
		my = IssueFile
		issue = Issue()
		with open(filepath, 'rb') as f:
			buf = f.read(sys.getsizeof(my.FILE_TAG + my.FIELD_DELIM))
			if buf == my.FILE_TAG + my.FIELD_DELIM:
				print my.FILE_TAG
				
		f.closed
		return issue

def test():
	startIssue = Issue()
	startIssue.title = "test issue title"
	startIssue.description = "test issue description"
	IssueFile.writeIssueToDisk("/Users/lorne/dev/personal/ghi/src/test-issue",startIssue)
	endIssue = IssueFile.readIssueFromDisk("/Users/lorne/dev/personal/ghi/src/test-issue")

if __name__ == "__main__":
    import sys
    test()

