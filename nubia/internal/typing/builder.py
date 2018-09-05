#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import ast
import collections
import re
import sys
import typing

from functools import wraps
from six import string_types, reraise

from nubia.internal.helpers import issubclass_, is_union


def build_value(string, type=None, python_syntax=False):
    value = (
        _safe_eval(string)
        if python_syntax
        else _build_simple_value(string, type)
    )
    if type:
        value = apply_typing(value, type)
    return value


def apply_typing(value, type):
    return get_typing_function(type)(value)


def get_list_arg_type_as_str(type):
    """
    This takes a type (typing.List[int]) and returns a string representation of
    the type argument, or "any" if it's not defined
    """
    assert issubclass_(type, collections.Iterable)
    args = getattr(type, "__args__", None)
    return args[0].__name__ if args else "any"


def is_dict_value_iterable(type):
    assert issubclass_(type, collections.Mapping)
    args = getattr(type, "__args__", None)
    if args and len(args) == 2:
        return issubclass_(args[1], typing.List)
    return False


def get_dict_kv_arg_type_as_str(type):
    """
    This takes a type (typing.Mapping[str, int]) and returns a tuple (key_type,
    value_type) that contains string representations of the type arguments, or
    "any" if it's not defined
    """
    assert issubclass_(type, collections.Mapping)
    args = getattr(type, "__args__", None)
    key_type = "any"
    value_type = "any"
    if args and len(args) >= 2:
        key_type = getattr(args[0], "__name__", str(args[0]))
        value_type = getattr(args[1], "__name__", str(args[1]))
    return key_type, value_type


def get_typing_function(type):
    func = None

    # TypeVars are a problem as they can defined multiple possible types.
    # While a single type TypeVar is somewhat useless, no reason to deny it
    # though
    if type == typing.TypeVar:
        subtypes = type.__constraints__
        if len(subtypes) != 1:
            raise ValueError(
                "Cannot resolve typing function for TypeVar({}) "
                "as it declares none or multiple types".format(
                    ", ".format(str(x) for x in subtypes)
                )
            )
        func = get_typing_function(subtypes[0])
    elif type == typing.Any:
        func = _identity_function
    elif issubclass_(type, string_types):
        func = str
    elif issubclass_(type, collections.Mapping):
        func = _apply_dict_type
    elif issubclass_(type, tuple):
        func = _apply_tuple_type
    elif issubclass_(type, collections.Iterable):
        func = _apply_list_type
    elif is_union(type):
        func = _apply_optional_type
    elif callable(type):
        func = type
    else:
        raise ValueError(
            'Cannot find a function to apply type "{}"'.format(type)
        )

    args = getattr(type, "__args__", None)

    if args:
        # this can be a Generic type from the typing module, like
        # List[str], Mapping[int, str] and so on. In that case we need to
        # also deal with the generic typing
        args_types = [get_typing_function(arg) for arg in args]
        func = _partial_builder(args_types)(func)

    return func


def _safe_eval(string):
    try:
        return ast.literal_eval(string)
    except ValueError:
        _, e, tb = sys.exc_info()
        if str(e) == "malformed string":
            # raise a more meaningful, nicer error
            msg = '"{}" uses unsafe token/symbols'.format(string)
            reraise(ValueError, ValueError(msg), tb)
        else:
            raise


def _build_simple_value(string, type):
    if not type or issubclass_(type, string_types):
        return string
    elif issubclass_(type, collections.Mapping):
        entries = (
            re.split(r"\s*[:=]\s*", entry, maxsplit=1)
            for entry in string.split(";")
        )
        if is_dict_value_iterable(type):
            entries = ((k, re.split(r"\s*,\s*", v)) for k, v in entries)
        return {k.strip(): v for k, v in entries}
    elif issubclass_(type, tuple):
        return tuple(item for item in string.split(","))
    elif issubclass_(type, collections.Iterable):
        return [item for item in string.split(",")]
    else:
        return string


def _apply_dict_type(value, key_type=None, value_type=None):
    if not key_type and not value_type:
        return dict(value)

    key_type = key_type or _identity_function
    value_type = value_type or _identity_function
    return {key_type(key): value_type(value) for key, value in value.items()}


def _apply_tuple_type(value, *types):
    if not types:
        return tuple(value)

    if len(value) != len(types):
        raise ValueError(
            "Cannot build a tuple of {} elements with {} "
            'values: "{}"'.format(len(types), len(value), value)
        )

    return tuple(function(value) for function, value in zip(types, value))


def _apply_list_type(value, value_type=None):
    if not isinstance(value, list):
        value = [value]

    if not value_type:
        return list(value)

    return [value_type(item) for item in value]


def _apply_optional_type(value, left_type=None, _right_type=None):
    if value is None:
        return None
    elif left_type is None:
        return value
    else:
        return left_type(value)


def _partial_builder(args_builders):
    def decorator(function):
        @wraps(function)
        def wrapped(string):
            return function(string, *args_builders)

        return wrapped

    return decorator


def _identity_function(x):
    return x
