#! /usr/bin/env python

import argparse
import subcmds
import sys

# Create top-level argument parser
parser = argparse.ArgumentParser()

cmds = parser.add_subparsers(title="subcommands",
                             help="valid subcommands")

# Create the 'init' command parser
cmd_init = cmds.add_parser(subcmds.init.NAME, 
                           help=subcmds.init.HELP)

cmd_init.set_defaults(func=subcmds.init.execute)

# Create the 'list' command parser
cmd_ls = cmds.add_parser(subcmds.ls.NAME,
                           help=subcmds.ls.HELP)

cmd_ls.add_argument(subcmds.ls.Args.ID,
                    help=subcmds.ls.Args.ID_HELP,
                    nargs=subcmds.ls.Args.ID_NARGS,
                    default=subcmds.ls.Args.ID_DEFAULT)

cmd_ls.set_defaults(func=subcmds.ls.execute)

# Create the 'add' command parser
cmd_add = cmds.add_parser(subcmds.add.NAME, 
                          help=subcmds.add.HELP)

cmd_add.add_argument(subcmds.add.Args.TITLE, 
                     help=subcmds.add.Args.TITLE_HELP)

cmd_add.add_argument(subcmds.add.Args.OPT_DESCRIPTION_SHORT,
                     subcmds.add.Args.OPT_DESCRIPTION,
                     help=subcmds.add.Args.OPT_DESCRIPTION_HELP)

cmd_add.set_defaults(func=subcmds.add.execute);

# Create the 'edit' command parser
cmd_edit = cmds.add_parser(subcmds.edit.NAME, 
                           help=subcmds.edit.HELP)

cmd_edit.add_argument(subcmds.edit.Args.ID,
                      help=subcmds.edit.Args.ID_HELP)

cmd_edit.add_argument(subcmds.edit.Args.OPT_TITLE_SHORT,
                      subcmds.edit.Args.OPT_TITLE,
                      help=subcmds.edit.Args.OPT_TITLE_HELP)

cmd_edit.add_argument(subcmds.edit.Args.OPT_DESCRIPTION_SHORT,
                      subcmds.edit.Args.OPT_DESCRIPTION,
                      help=subcmds.edit.Args.OPT_DESCRIPTION_HELP)

cmd_edit.set_defaults(func=subcmds.edit.execute);


# Create the 'rm' command parser
cmd_rm = cmds.add_parser("rm", help="remove an issue")
cmd_rm.add_argument("id", help="Issue ID")

# Quick sanity check to see if any subcommand was given at all
posarg = False
for i,arg in enumerate(sys.argv):
    if (i != 0 and str(arg)[0] != '-'):
        posarg = True

# Make the default subcommand 'ls'
if (posarg == False):
    args = parser.parse_args(sys.argv.extend([subcmds.ls.NAME]))
else:
    args = parser.parse_args()

# Execute the command
args.func(args)