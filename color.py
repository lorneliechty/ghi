#! /usr/bin/env python

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