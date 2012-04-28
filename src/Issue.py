#! /usr/bin/env python

class Issue:
    """Class that represents an Issue"""
    title = r""
    description = r""

    status = 0

def writeIssueToDisk(filepath, issue):
    print issue.title + "\n" + issue.description
    return

def readIssueFromDisk(filepath):
    return Issue()

if __name__ == "__main__":
    import sys
    issue = Issue()
    issue.title = "test issue title"
    issue.description = "test issue description"
    writeIssueToDisk("",issue)

