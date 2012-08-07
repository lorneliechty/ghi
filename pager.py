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

# This code is *heavily* borrowed from pager.py of the AOSP project 'repo'.
# This has been done out of the utmost respect for that project and its
# authors. Their solution to output paging within a python project is
# excellent and I would not suggest that I could do it better.
#
# It has been modified to be more ghi-specific since the AOSP version was
# fairly 'repo' specific.

from subprocess_helper import getCmd
import os
import select
import sys

def PageOutputBeyondThisPoint():
	"""Use a pager for any output displayed after this function has run.
	This is particularly useful for commands like ghi-ls"""

	if not os.isatty(0) or not os.isatty(1):
		return

	pager = _SelectPager()
	if pager == '' or pager == 'cat':
		return

	# This process turns into the pager; a child it forks will
	# do the real processing and output back to the pager. This
	# is necessary to keep the pager in control of the tty.
	#
	try:
		r, w = os.pipe()
		pid = os.fork()
		if not pid:
			os.dup2(w, 1)
			os.dup2(w, 2)
			os.close(r)
			os.close(w)
			return

		os.dup2(r, 0)
		os.close(r)
		os.close(w)

		_BecomePager(pager)
	except Exception:
		print >> sys.stderr, "fatal: cannot start pager '%s'" % pager
		exit()

def _SelectPager():
	try:
		return os.environ['GIT_PAGER']
	except KeyError:
		pass

	pager = getCmd('git config core.pager')
	if pager:
		return pager

	try:
		return os.environ['PAGER']
	except KeyError:
		pass

	return 'less'

def _BecomePager(pager):
	# Delaying execution of the pager until we have output
	# ready works around a long-standing bug in popularly
	# available versions of 'less', a better 'more'.
	#
	a, b, c = select.select([0], [], [0])

	os.environ['LESS'] = 'FRSX'

	try:
		os.execvp(pager, [pager])
	except OSError, e:
		os.execv('/bin/sh', ['sh', '-c', pager])
