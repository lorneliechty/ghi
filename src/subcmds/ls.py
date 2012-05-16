#! /usr/bin/env python

from color import Color
from issue import IssueFile
import config
import dircache

NAME = "ls"
HELP = "List issues"

class Args:
    """Wrapper class that defines the command line args"""
    ID="id"
    ID_HELP="Issue ID"
    ID_NARGS="?"
    ID_DEFAULT="*"

def execute(args):
    for issueID in dircache.listdir(config.ISSUES_DIR):
        issue = IssueFile.readIssueFromDisk(
                                config.ISSUES_DIR + "/" + issueID) 
        print str(Color('yellow')) + issueID[:7] + str(Color('none')) + \
                "\t" + issue.title

if (__name__ == "__main__"):
    execute()