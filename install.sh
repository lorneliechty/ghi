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

main() {
	if [[ $UID != 0 ]]; then
	    echo "Please run this script with sudo:"
	    echo "sudo $0 $@"
	    exit 1
	fi
	
	cleanvars
	determineOS

	if [ $(isBashCompletionInstalled) = 1 ]; then
		installBashCompletion
	fi
}

cleanvars() {
	unset OS
}

determineOS() {
	export OSX="Darwin"

	# Detect OS
	if [ -n "$(uname -a | grep $OSX)" ]; then
		export OS=$OSX
	else
		export OS="Unknown"
	fi
}

getBashCompletionInstallDir() {
	case $OS in
	$OSX)
		echo "/opt/local/etc/bash_completion.d"
		;;
	esac
}

isBashCompletionInstalled() {
	if test -d $(getBashCompletionInstallDir); then
		echo 1; return 0;
	fi

	echo 0; return 1;
}

installBashCompletion() {
	sudo cp etc/bash_completion/ghi $(getBashCompletionInstallDir)/ghi
}

main $@
