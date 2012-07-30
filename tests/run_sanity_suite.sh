#! /bin/bash

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

	$($GHI_CMD_ALIAS \
		add "Add with -d" \
		-d "Description of Issue")
	git commit -m "Test ghi-add with -d"

	$($GHI_CMD_ALIAS \
		add "Add with --description" \
		--description "Description of Issue")
	git commit -m "Test ghi-add with --description"

	$($GHI_CMD_ALIAS \
		add "Add with --group" \
		--group "Added with --group")
	git commit -m "Test ghi-add with --description"

	$($GHI_CMD_ALIAS \
		add "Add with -d and --group" \
		-d "Description of Issue" \
		--group "ghi-add with --group")
	git commit -m "Test ghi-add with -d and --group"

	$($GHI_CMD_ALIAS \
		add "Add with --description and --group" \
		--description "Description of Issue" \
		--group "ghi-add with --group")
	git commit -m "Test ghi-add with --description and --group"
}

function test_ls() {
	echo "-----------------------------"
	echo "-        Test ghi-ls        -"
	echo "-----------------------------"

	# Store current git config issue.ls defaults
	default_group=$(git config issue.ls.group)
	default_sort=$(git config issue.ls.sort)

	# clear issue.ls defaults
	git config --remove-section issue.ls 2> /dev/null

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
	git config issue.ls.group $default_group
	git config issue.ls.sort $default_sort
}

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

$GHI_CMD_ALIAS	# quick test of empty set ghi-ls

test_add

test_ls

# Reset paging back to its original settings
export GIT_PAGER=$GIT_PAGER_HOLDER

echo "Leaving test directory"
popd
