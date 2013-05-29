#! /usr/bin/env python
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

COLORS = {None      :-1,
          'normal'  :-1,
          'black'   :0,
          'red'     :1,
          'green'   :2,
          'yellow'  :3,
          'blue'    :4,
          'magenta' :5,
          'cyan'    :6,
          'white'   :7}

RESET = "\033[m"

def is_color(s): return s in COLORS

class Color:
    c = None
    
    def __init__(self,color):
        if (color == 'none'):
            self.c = None
        else:
            self.c = COLORS[color]
    
    def __str__(self):
        if (self.c == None):
            return RESET
        return "\033[3%dm" % self.c