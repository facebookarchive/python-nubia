#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import logging
import os
import re
import json
import string
import shlex

logger = logging.getLogger(__name__)

option_regex = re.compile("(?P<key>\-\-?[\w\-]+\=)")


def run_complete(args):
    model_file = args.command_model_path
    logging.info("Command model: %s", model_file)
    comp_line = os.getenv("COMP_LINE")
    comp_point = int(os.getenv("COMP_POINT", "0"))
    comp_type = os.getenv("COMP_TYPE")
    comp_shell = os.getenv("COMP_SHELL", "bash")
    if not comp_line:
        logger.error("$COMP_LINE is unset, failing!")
        return 1
    if not comp_point:
        logger.error("$COMP_POINT is unset, failing!")
        return 1
    # Fix the disparity between zsh and bash for COMP_POINT
    if comp_shell == "zsh":
        comp_point -= 1
    # We want to trim the remaining of the line because we don't care about it
    comp_line = comp_line[:comp_point]
    # We want to tokenize the input using these rules:
    # - Separate by space unless there it's we are in " or '
    try:
        tokens = shlex.split(comp_line)
        if len(tokens) < 1:
            return 1
        # drop the first word (the executable name)
        tokens = tokens[1:]
    except ValueError:
        logger.warning(
            "We are in an open quotations, cannot suggestion completions"
        )
        return 0
    logger.debug("COMP_LINE: @%s@", comp_line)
    logger.debug("COMP_POINT: %s", comp_point)
    logger.debug("COMP_TYPE: %s", comp_type)
    logger.debug("COMP_SHELL: %s", comp_shell)
    # we want to know if the cursor is on a space or a word. If it's on a space,
    # then we expect a completion of (command, option, or value).
    current_token = None
    if comp_line[comp_point - 1] not in string.whitespace:
        current_token = tokens[-1]
        tokens = tokens[:-1]
    logger.debug("Input Tokens: %s", tokens)
    logger.debug("Current token: %s", current_token)
    # loading the model
    with open(model_file, "r") as f:
        model = json.load(f)

    completions = get_completions(model, tokens, current_token, comp_shell)
    for completion in completions:
        logger.debug("Completion: @%s@", completion)
        print(completion)


def _drop_from_options(options, token, skip_value=False):
    # does this token in the format "-[-]x=" ?
    tokens = token.split("=")
    if skip_value:
        tokens = tokens[:1]
    for i, option in enumerate(options):
        logger.debug("Tokens: %s", tokens)
        if tokens[0] == option.get("name") or tokens[0] in option.get(
            "extra_names"
        ):
            logger.debug("Dropping option %s", option)
            if option.get("expects_argument"):
                if len(tokens) > 1:
                    # we have the argument already
                    options.pop(i)
                    return None
                return options.pop(i)
            else:
                return None
        else:
            logger.debug("mismatch: %s and %s", option.get("name"), tokens[0])


def _get_values_for_option(option, prefix=""):
    logger.debug("Should auto-complete for option %s", option.get("name"))
    output = option.get("values", [])
    if output:
        output = [prefix + _space_suffix(k) for k in output]
    logger.debug("Values: %s", output)
    return output


def get_completions(model, tokens, current, shell):
    output = []
    options_we_expect = model["options"]
    current_command_list = model.get("commands", [])
    last_option_found = None
    for token in tokens:
        if token.startswith("-"):
            # it's an option, drop it from expected
            current_option = _drop_from_options(options_we_expect, token)
            if current_option and current_option.get("expects_argument"):
                last_option_found = current_option
        else:
            # this is:
            # - Argument to an option (ignore)
            # - Command
            # - Some random free argument
            if last_option_found:
                # does it expect a value?
                logger.debug(
                    "Skipping %s because it's an argument to %s",
                    token,
                    last_option_found.get("name"),
                )
                last_option_found = None
                continue
            last_option_found = None
            for command in current_command_list:
                if token == command.get("name"):
                    logger.debug("We matched command %s", command.get("name"))
                    options_we_expect.extend(command.get("options", []))
                    # for sub-commands
                    current_command_list = command.get("commands", [])
                    break
            else:
                logger.debug(
                    "We didn't find any matching command, ignoring the"
                    "token %s",
                    token,
                )
                # Now that we know where we are, let's complete the current token:
    if last_option_found:
        # we are expecting a value for this
        output = _get_values_for_option(last_option_found)
    else:
        # If the current token is '--something=' then we should try to
        # autocomplete a value for this
        if current:
            match = option_regex.match(current)
            if match:
                key = match.groupdict()["key"]
                logger.debug("We are in a value-completion inside %s", key)
                # it's true
                option = _drop_from_options(
                    options_we_expect, current, skip_value=True
                )
                if option:
                    # YES, we have it, let's get the values
                    prefix = ""
                    if shell == "zsh":
                        # in zsh, we need to prepend the completions with the
                        # key
                        prefix = key
                    return _get_values_for_option(option, prefix)

        output.extend(_completions_for_options(options_we_expect))
        output.extend(_completions_for_commands(current_command_list))
    return output


def _space_suffix(word):
    return word + " "


def _completions_for_options(options):
    output = []
    should_suffix = int(os.getenv("NUBIA_SUFFIX_ENABLED", "1"))

    def __suffix(key, expects_argument=True):
        if should_suffix and expects_argument:
            return key + "="
        else:
            return _space_suffix(key)

    for option in options:
        expects_argument = False
        if option.get("expects_argument"):
            expects_argument = True
        output.append(__suffix(option.get("name"), expects_argument))
    return output


def _completions_for_commands(commands):
    return [_space_suffix(x["name"]) for x in commands]
