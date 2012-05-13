#! /usr/bin/env python

import argparse
import subcmds

# Create top-level argument parser
parser = argparse.ArgumentParser()
cmds = parser.add_subparsers(title="subcommands",
                             help="valid subcommands")

# Create the 'init' command parser
cmd_init = cmds.add_parser(subcmds.init.NAME, 
                           help=subcmds.init.HELP)

cmd_init.set_defaults(func=subcmds.init.execute)

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
cmd_edit = cmds.add_parser("edit", help="edit an existing issue")
cmd_edit.add_argument("id", help="Issue ID")
cmd_edit.add_argument("-t", "--title", help="Title")
cmd_edit.add_argument("-d", "--description", help="Description") 

# Create the 'rm' command parser
cmd_rm = cmds.add_parser("rm", help="remove an issue")
cmd_rm.add_argument("id", help="Issue ID")

# Parse args and execute command
args = parser.parse_args()
args.func(args)