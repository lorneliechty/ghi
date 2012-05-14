#! /usr/bin/env python

from issue import Issue
from issue import IssueFile
import uuid

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
    
    print issue.title, issue.description
    
    id = uuid.uuid4()
    file = IssueFile()