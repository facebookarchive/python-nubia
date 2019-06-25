#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import pyparsing as pp

from nubia.internal.exceptions import CommandParseError

allowed_symbols_in_string = r"-_/#@£$€%*+~|<>?."


def _no_transform(x):
    return x


def _bool_transform(x):
    return x in ["True", "true"]


def _str_transform(x):
    return x.strip("\"'")


_TRANSFORMS = {
    "bool": _bool_transform,
    "str": _str_transform,
    "int": int,
    "float": float,
    "dict": dict,
}


def _parse_type(datatype):
    transform = _TRANSFORMS.get(datatype, _no_transform)

    def _parse(s, loc, toks):
        return list(map(transform, toks))

    return _parse


identifier = pp.Word(pp.alphas + "_-", pp.alphanums + "_-")

int_value = pp.Regex(r"\-?\d+").setParseAction(_parse_type("int"))

float_value = pp.Regex(r"\-?\d+\.\d*([eE]\d+)?").setParseAction(
    _parse_type("float")
)

bool_value = (
    pp.Literal("True")
    ^ pp.Literal("true")
    ^ pp.Literal("False")
    ^ pp.Literal("false")
).setParseAction(_parse_type("bool"))

# may have spaces
quoted_string = pp.quotedString.setParseAction(_parse_type("str"))
# cannot have spaces
unquoted_string = pp.Word(
    pp.alphanums + allowed_symbols_in_string
).setParseAction(_parse_type("str"))

string_value = quoted_string | unquoted_string

single_value = bool_value | float_value | string_value | int_value

list_value = pp.Group(
    pp.Suppress("[")
    + pp.Optional(pp.delimitedList(single_value))
    + pp.Suppress("]")
).setParseAction(_parse_type("list"))

# because this is a recursive construct, a dict can contain dicts in values
dict_value = pp.Forward()

value = list_value ^ single_value ^ dict_value

dict_key_value = pp.dictOf(string_value + pp.Suppress(":"), value)

dict_value << pp.Group(
    pp.Suppress("{") + pp.delimitedList(dict_key_value) + pp.Suppress("}")
).setParseAction(_parse_type("dict"))

# Positionals must be end of line or has a space (or more) afterwards.
# This is to ensure that the parser treats text like "something=" as invalid
# instead of parsing this as positional "something" and leaving the "=" as
# invalid on its own.
positionals = pp.ZeroOrMore(
    value + (pp.StringEnd() ^ pp.Suppress(pp.OneOrMore(pp.White())))
).setResultsName("positionals")

key_value = pp.Dict(pp.ZeroOrMore(pp.Group(
    identifier + pp.Suppress("=") + value))).setResultsName("kv")

subcommand = identifier.setResultsName("__subcommand__")

# Subcommand is optional here as it maybe missing, in this case we still want to
# pass the parsing and we will handle the fact that the subcommand is missing
# while validating the arguments
command_with_subcommand = pp.Optional(subcommand) + key_value + positionals

# Positionals will be passed as the last argument
command = key_value + positionals


def parse(text: str, expect_subcommand: bool) -> pp.ParseResults:
    expected_pattern = command_with_subcommand if expect_subcommand else command
    try:
        result = expected_pattern.parseString(text, parseAll=True)
        return result
    except pp.ParseException as e:
        exception = CommandParseError(str(e))
        remaining = e.markInputline()
        partial_result = expected_pattern.parseString(text, parseAll=False)
        exception.remaining = remaining[(remaining.find(">!<") + 3) :]
        exception.partial_result = partial_result
        exception.col = e.col
        raise exception
