#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import argparse

from typing import List, Tuple, Any
from nubia.internal.constants import DEFAULT_COMMAND_TIMEOUT
from nubia.internal.ui import statusbar
from nubia.internal.context import Context
from nubia.internal.blackcmd import CommandBlacklist


class CompletionDataSource:
    """An interface that defines completion data sources"""

    def get_all(self):
        """
        Returns all the possible values for this data source
        """
        return []


class PluginInterface:
    """
    The PluginInterface class is a way to customize nubia for every customer
    use case. It allowes custom argument validation, control over command
    loading, custom context objects, and much more.
    """

    def create_context(self):
        """
        Must create an object that inherits from `Context` parent class.
        The plugin can return a custom context but it has to inherit from the
        correct parent class.
        """
        return Context()

    def validate_args(self, args):
        """
        This will be executed when starting nubia, the args passed is a
        dict-like object that contains the argparse result after parsing the
        command line arguments. The plugin can choose to update the context
        with the values, and/or decide to raise `ArgsValidationError` with
        the error message.
        """
        pass

    def get_commands(self):
        return []

    def get_listeners(self):
        """
        Return all "classes" that implement the Listener interface, note that
        you should not return the instances of these classes as they will be
        instantiated by nubia
        """
        return []

    def get_magics(self):
        """
        Return all the class objects that inherit from
        `IPython.core.magic.Magics` to be registered if running with ipython
        mode.
        """
        return []

    def get_opts_parser(self, add_help=True):
        """
        Builds the ArgumentParser that will be passed to nubia, use this to
        build your list of arguments that you want for your shell.
        """
        epilog = (
            "NOTES: LIST types are given as comma separated values, "
            "eg. a,b,c,d. DICT types are given as semicolon separated "
            "key:value pairs (or key=value), e.g., a:b;c:d and if a dict "
            "takes a list as value it look like a:1,2;b:1"
        )
        opts_parser = argparse.ArgumentParser(
            description="A Generic Shell Utility",
            epilog=epilog,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            add_help=add_help,
        )
        opts_parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            help="Increase verbosity, can be specified " "multiple times",
        )
        opts_parser.add_argument(
            "--stderr",
            "-s",
            action="store_true",
            help="By default the logging output goes to a "
            "temporary file. This disables this feature "
            "by sending the logging output to stderr",
        )
        opts_parser.add_argument(
            "--command-timeout",
            required=False,
            type=int,
            default=DEFAULT_COMMAND_TIMEOUT,
            help="Timeout for commands (default %ds)" % DEFAULT_COMMAND_TIMEOUT,
        )
        return opts_parser

    def get_completion_datasource_for_global_argument(self, name):
        return None

    def get_status_bar(self, context):
        return statusbar.StatusBar(context)

    def get_prompt_tokens(self, context: Context) -> List[Tuple[Any, str]]:
        return context.get_prompt_tokens()

    def setup_logging(self, root_logger, args):
        """
        Override this and configure your own logging setup. Return your root
        logger.
        """
        return None

    def create_usage_logger(self, context):
        """
        Override this and return you own usage logger.
        Must be a subtype of UsageLoggerInterface.
        """
        return None

    def getBlacklistPlugin(self):
        """
        Override this and return you own plugin for blacklist commands.
        Then implement a function is_blacklisted(<command_name>)
        Any return other then 0 will block command execution
        """
        return CommandBlacklist()
