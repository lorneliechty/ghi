#! /usr/bin/env python

from issue import Issue
from issue import IssueFile
import uuid
import config

NAME="add"
HELP="Add a new issue"

class Args:
    """Wrapper class that defines the command line args"""
    TITLE="title"
    TITLE_HELP="One line issue title"
    
    OPT_DESCRIPTION="--description"
    OPT_DESCRIPTION_SHORT="-d"
    OPT_DESCRIPTION_HELP="Description"

def execute(args):
    
    # First validate arguments
    if (args.title == None):
        # Title is required... no good
        return None
    
    # Create new issue
    issue = Issue();
    
    # Set title
    issue.title = args.title
    
    # Set description
    if (args.description):
        issue.description = args.description
    
    # Generate an issue ID and then write the issue file to disk
    issueID = uuid.uuid4()
    IssueFile.writeIssueToDisk(config.ISSUES_DIR + "/" + str(issueID), 
                               issue)
    
    # Display the new issue ID to the user
    print str(issueID)