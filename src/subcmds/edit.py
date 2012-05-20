#! /usr/bin/env python

from issue import Issue
from issue import IssueFile
import config
import identifiers

NAME="edit"
HELP="Edit an existing issue"

class Args:
    """Wrapper class that defines the command line args"""
    ID="id"
    ID_HELP="Issue ID"
    
    OPT_TITLE="--title"
    OPT_TITLE_SHORT="-t"
    OPT_TITLE_HELP="One line issue title"
    
    OPT_DESCRIPTION="--description"
    OPT_DESCRIPTION_SHORT="-d"
    OPT_DESCRIPTION_HELP="Description"

def execute(args):
    
    # First validate arguments
    issueID = identifiers.getFullIssueIdFromLeadingSubstr(args.id)
    if (issueID == None):
        # ID is required... no good
        return None
    
    # Load the existing issue
    issue = IssueFile.readIssueFromDisk(
                            config.ISSUES_DIR + "/" + issueID);
    
    # Set title
    if (args.title):
        issue.title = args.title
    
    # Set description
    if (args.description):
        issue.description = args.description
    
    # Write the issue file to disk
    IssueFile.writeIssueToDisk(
                            config.ISSUES_DIR + "/" + issueID, 
                            issue)
    
    # Give the user some feedback on the success
    print "Issue Updated"