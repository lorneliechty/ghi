#! /bin/bash
#
# Copyright (C) 2012 Lorne Liechty
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

function printUsage() {
	echo "Usage:"
	echo "  run_sanity_suite <path/to/test/dir>"
}

function parseArgs() {
	if [ -z $1 ]; then
		printUsage
		exit 1;
	fi

	if ! [ -d $1 ]; then
		echo "Directory $1 does not exist!"
		echo "Would you like to create it now? [y/n]"
		read answer
		if [[ $answer = "y" ]]; then
			mkdir -p $1
		else
			exit 0
		fi
	fi

	if [[ $2 = "--clean"  ]]; then
		rm -rf $1
		mkdir -p $1
	fi
}

function run() {
	echo $@
	eval "$@"
}

function test_add() {
	echo "------------------------------"
	echo "-        Test ghi-add        -"
	echo "------------------------------"

	$GHI_CMD_ALIAS \
		add "Add with title only"
	git commit -m "Test ghi-add with title only"

	$GHI_CMD_ALIAS \
		add "Add with -d" \
		-d "Description of Issue"
	git commit -m "Test ghi-add with -d"

	$GHI_CMD_ALIAS \
		add "Add with --description" \
		--description "Description of Issue"
	git commit -m "Test ghi-add with --description"

	$GHI_CMD_ALIAS \
		add "Add with --group" \
		--group "Added with --group"
	git commit -m "Test ghi-add with --description"

	$GHI_CMD_ALIAS \
		add "Add with -d and --group" \
		-d "Description of Issue" \
		--group "ghi-add with --group"
	git commit -m "Test ghi-add with -d and --group"

	$GHI_CMD_ALIAS \
		add "Add with --description and --group" \
		--description "Description of Issue" \
		--group "ghi-add with --group"
	git commit -m "Test ghi-add with --description and --group"
}

function test_edit() {
	echo "-------------------------------"
	echo "-        Test ghi-edit        -"
	echo "-------------------------------"

	issue_to_edit=$($GHI_CMD_ALIAS add "Issue for testing ghi-edit")
	git commit -m "Add issue to test ghi-edit"

	$GHI_CMD_ALIAS edit $issue_to_edit -t "ghi-edit New Title Only"
	git commit -m "ghi-edit New Title Only"

	$GHI_CMD_ALIAS edit $issue_to_edit -d "ghi-edit New Description Only"
	git commit -m "ghi-edit New Description Only"

	$GHI_CMD_ALIAS edit $issue_to_edit -s "Fixed"
	git commit -m "ghi-edit New Status Only"

	$GHI_CMD_ALIAS edit $issue_to_edit -t "ghi-edit New Title" -d "ghi-edit New Description"
	git commit -m "ghi-edit New Title and New Description"

	$GHI_CMD_ALIAS edit $issue_to_edit -s "New" -d "ghi-edit New Description"
	git commit -m "ghi-edit New Status and New Description"

	$GHI_CMD_ALIAS edit $issue_to_edit -t "ghi-edit Newer Title" -s "New"
	git commit -m "ghi-edit New Status and New Title"

	$GHI_CMD_ALIAS edit $issue_to_edit -t "Newest Title" -s "In progress" -d "ghi-edit Newest Description"
	git commit -m "ghi-edit New Title, New Status, and New Description"

	# Test a non-existing status... shouldn't crash
	$GHI_CMD_ALIAS edit $issue_to_edit -s "asd;flaksjd"
}

function test_ls() {
	echo "-----------------------------"
	echo "-        Test ghi-ls        -"
	echo "-----------------------------"

	# If necessary, clear issue.ls defaults
	bDefaults=0
	if ! [ -z $(git config --get-regexp issue.ls) ]; then
		bDefaults=1

		# Store current git config issue.ls defaults
		default_group=$(git config issue.ls.group)
		default_sort=$(git config issue.ls.sort)
	
		git config --remove-section issue.ls 2> /dev/null
	fi

	# Begin tests
	printf "\n"
	printf "ls\n\n"
	$GHI_CMD_ALIAS

	printf "\n"
	printf "ls --group\n\n"
	$GHI_CMD_ALIAS --group

	printf "\n"
	printf "ls --sort status\n\n"
	$GHI_CMD_ALIAS --sort status

	printf "\n"
	printf "ls --group --sort status\n\n"
	$GHI_CMD_ALIAS --group --sort status

	printf "\n"
	printf "ls\n\n"
	$GHI_CMD_ALIAS

	printf "\n"
	printf "ls #issue.ls.group\n\n"
	git config --bool issue.ls.group true
	$GHI_CMD_ALIAS

	git config issue.ls.sort status

	printf "\n"
	printf "ls #issue.ls.group #issue.ls.status sort\n\n"
	$GHI_CMD_ALIAS

	git config --unset issue.ls.group

	printf "\n"
	printf "ls #issue.ls.sort status\n\n"
	$GHI_CMD_ALIAS

	git config --unset issue.ls.sort

	printf "\n"
	printf "ls\n\n"
	$GHI_CMD_ALIAS

	# Restore issue.ls defaults
	if [[ $bDefaults = 1 ]]; then
		git config --bool issue.ls.group $default_group
		git config issue.ls.sort $default_sort
	fi
}

function test_group() {
	echo "--------------------------------"
	echo "-        Test ghi-group        -"
	echo "--------------------------------"

	$GHI_CMD_ALIAS group

	issue_to_group=$($GHI_CMD_ALIAS add "Issue to group")
	git commit -m "Add Issue for testing ghi-group"
	$GHI_CMD_ALIAS group $issue_to_group "ghi-group test group"
	git commit -m "Group Issue for testing ghi-group"

	issue_to_rm_from_group=$($GHI_CMD_ALIAS add "Issue to group" --group "ghi-group test group")
	git commit -m "Add Issue for testing ghi-group"
	$GHI_CMD_ALIAS group -d $issue_to_rm_from_group "ghi-group test group"
	git commit -m "Remove issue from existing group for testing ghi-group"

	$GHI_CMD_ALIAS group -d "ghi-group test group"
	git commit -m "Remove group for testing ghi-group"

	issue_to_rm_from_group=$($GHI_CMD_ALIAS add "Issue to group" --group "ghi-group test group")
	issue_to_rm_from_group_2=$($GHI_CMD_ALIAS add "Issue to group" --group "ghi-group test group")
	git commit -m "Add Issues for testing ghi-group"
	$GHI_CMD_ALIAS rm $issue_to_rm_from_group
	$GHI_CMD_ALIAS rm $issue_to_rm_from_group_2	# Should also remove the group
	git commit -m "Testing multi-issue remove to remove group"

	$GHI_CMD_ALIAS --group
}

function test_rm() {
	echo "-----------------------------"
	echo "-        Test ghi-rm        -"
	echo "-----------------------------"

	issue_to_rm=$($GHI_CMD_ALIAS add "Issue to rm")
	git commit -m "Add Issue for testing ghi-rm"
	
	$GHI_CMD_ALIAS rm $issue_to_rm
	git commit -m "Issue removed with ghi-rm"

	issue_to_rm=$($GHI_CMD_ALIAS add "Issue to rm" --group "ghi-rm test group")
	git commit -m "Add Issue with --group for testing ghi-rm"
	
	$GHI_CMD_ALIAS rm $issue_to_rm
	git commit -m "Issue added with --group removed with ghi-rm"
}

set -e	# Exit immediately if there is an error... don't keep going

parseArgs $@

# For right now, we're assuming that these tests are always being run from
# the root of a ghi repository. As is indicated below, there is no logic to
# find the ghi command under test from an arbitrary directory
GHI_DIR=$(pwd)
GHI_CMD=$GHI_DIR/ghi
echo "ghi command = $(pwd)"

echo "Changing to test directory"
pushd $1

# Make sure that we're working within a git repository...
git init

# Idealy, each command from this point on would be individually executed and
# tested individually and in aggregate. However, we're not quite there yet.
$GHI_CMD init --ghi_path $GHI_DIR

# Our git repository-specifc alias for 'git issue' should now be setup. It is
# the recommended method for using ghi, so setup a variable and use it for
# all tests from now on unless otherwise specified.
GHI_CMD_ALIAS='git issue'

# Disable output paging for now
GIT_PAGER_HOLDER=$GIT_PAGER
export GIT_PAGER=''

$GHI_CMD_ALIAS			# quick test of empty set ghi-ls
$GHI_CMD_ALIAS group	# quick test of empty set ghi-group

test_add
test_edit
test_group
test_rm
test_ls

# Reset paging back to its original settings
export GIT_PAGER=$GIT_PAGER_HOLDER

echo "Leaving test directory"
popd
