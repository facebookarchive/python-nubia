#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import sys
import logging
import argparse
from nubia_complete.completer import run_complete
from nubia_complete.shell import generate_shell_setup

logger = logging.getLogger(__name__)


def main():
    sys.exit(run(sys.argv))


def run(args):
    opts_parser = argparse.ArgumentParser(
        description="A shell completion utility for nubia programs"
    )

    subparsers = opts_parser.add_subparsers(help="sub-command help", dest="mode")
    opts_parser.add_argument(
        "--loglevel",
        type=str,
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="logging level",
    )

    generate_parser = subparsers.add_parser(
        "generate-shell-setup",
        help="Generates a bash/zsh setup script that you can source",
    )
    complete_parser = subparsers.add_parser("complete", help="Triggers completions")
    generate_parser.add_argument(
        "--target-binary-name",
        type=str,
        required=True,
        help="The name of the nubia program we want to generate a completer for",
    )
    generate_parser.add_argument(
        "--command-model-path",
        type=str,
        required=True,
        help="The location on which to find the command model",
    )
    complete_parser.add_argument(
        "--command-model-path",
        type=str,
        required=True,
        help="The location on which to find the command model",
    )
    args = opts_parser.parse_args()
    # Setting up logging
    log_level = logging.getLevelName(args.loglevel)
    logging.basicConfig(level=log_level)
    if args.mode == "generate-shell-setup":
        return generate_shell_setup(args.target_binary_name, args.command_model_path)
    elif args.mode == "complete":
        return run_complete(args)
    else:
        print("Not Implemented!")
        return 2


if __name__ == "__main__":
    main()
