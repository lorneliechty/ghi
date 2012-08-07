ghi: Git Has Issues
====================
Git Has Issues (ghi), is an open source implementation of an Issues-compatible issue tracking system for the git version control system. Ghi relies on Issues for the definition of how an issue is defined and provides the necessary set of helpful tools that make issue tracking possible.

## Sufficiently confusing? What is ghi really meant to be?
Ghi is meant to be a bug tracker.
Beyond bugs though it can track features, support tickets, and any other kind of to-do style list of issues... an "issue tracker".
Rather than try to define what an Issue is though it focuses on how to track them within git.

Ghi leaves Issue definition up to another project: "Issues".
The Issues project focuses only on what information should be stored in an Issue and, perhaps more importantly, what information should be left to an SCM like git.
The idea of tracking Issues within git is where the project gets its name: Git Has Issues.

## Why write a new bug tracker? What are the benefits?
Currently, the primary goal of ghi is to make bug tracking orders-of-magnitude faster for the individual developer.
Seondary goals include better team collaboration, improvements to complex bug tracking workflows, and generally faster innovation through standardized Issue definition.

Most individual developers are slowed down by existing bug trackers for a few reasons:
* There are too many project-management related options that they don't need or care about
* The web interface is not quickly accessible
* The GUI is clunky / difficult to use
* Bugs have turned into pages of comments that take forever to read and become useless for quick consumption
* Everything is too slow

Ghi tries to solve some of these problems by:
* Moving all project management related information to the SCM (e.g., bugs on branches is amazing)
* For now, there is no web interface ;) On the plus side, connectivity is never a problem
* Ghi focusses on keeping look and feel that is very similar to working with the git command line
* Ghi completely removes comments in favor of wiki-style Issue descriptions
* Ghi is very, very fast when compared to web-based bug trackers

## Sounds good. How do I use ghi?
The following sections provide example commands for setting up and using ghi in some basic workflows.
Hopefully these will also clearly show the speed and power of ghi as well.

### How to install ghi:
Installing ghi on your machine is easy. Just clone the repository and put it on your path!
The project dependencies are kept intentionally minimal (just python 2.7 and git 1.7)

	git clone git://github.com/lorneliechty/ghi.git /path/to/ghi
	export PATH=$PATH:/path/to/ghi

### How to start using ghi in your git repository:
Adding a bug tracker to your project should be as easy as starting your repository.
With ghi, it is!

	git init
	ghi init	# will auto-commit the initialized .ghi directory in the root of the git repository

### How to add an Issue / bug in ghi:
Adding a bug should be a fast as possible. One line is better than 3 or 4 clicks in a browser.

	git issue add "Bug I need to fix"
	git commit	# ghi will auto-suggest a commit message based on issues you've added>

\- alternatively \-

	git commit add	# opens up an interactive editor based on your configured editor preference in git

### How to fix an Issue / bug in ghi:
You know what would be great?... Marking a bug fixed in the same commit as the code change that fixes the Issue.
With ghi this is possible.

	<fix bug in source code>
	git issue edit -s Fixed [issue id]
	git commit	# ghi will auto-suggest a commit message based on issues you've edited

### How to close an Issue / bug in ghi:
Hate sifting through endless lists of closed bugs?
In ghi, you remove an Issue when its closed and let the SCM handle archiving a file that should never change.

	<verify bug fixed code in testing>
	git issue rm [issue id]
	git commit	# ghi will auto-suggest a commit message based on issues you've closed (removed)

### How to list existing Issues in ghi:
Two words is all it takes.

	git issue

#### How to set default list options in ghi:
Want to provide some default styling to your Issue list?
Use standard the git config file system.

	git config --bool issue.ls.group true
	git config issue.ls.sort status

### How to organize issues in ghi:
Ghi eschews a never-ending list of fields stored for each issue in favor of highly flexible groups.
This allows branches, forks, or individual developers to orgranize the Issues as they see fit without having to change the Issue definition (re-organizing issues is not the same as changing issues!)

	git issue group [issue id] [groupname]	# Example groups: Critical, Very High, High, Medium, Low... prioritize via ghi groups!


---
This project is licensed under Apache License, Version 2.0. You may obtain a copy of the license at http://www.apache.org/licenses/LICENSE-2.0

