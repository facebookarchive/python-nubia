#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import ast
import re
import sys
import typing

from functools import wraps

from nubia.internal.helpers import issubclass_
from nubia.internal.typing.inspect import (
    PEP_560,
    is_iterable_type,
    is_mapping_type,
    is_optional_type,
    is_tuple_type,
    is_typevar,
)


def build_value(string, tp=None, python_syntax=False):
    value = (
        _safe_eval(string)
        if python_syntax
        else _build_simple_value(string, tp)
    )
    if tp:
        value = apply_typing(value, tp)
    return value


def apply_typing(value, tp):
    return get_typing_function(tp)(value)


def get_list_arg_type_as_str(tp):
    """
    This takes a type (typing.List[int]) and returns a string representation of
    the type argument, or "any" if it's not defined
    """
    assert is_iterable_type(tp)
    args = getattr(tp, "__args__", None)
    return args[0].__name__ if args else "any"


def is_dict_value_iterable(tp):
    assert is_mapping_type(tp), f"{tp} is not a mapping type"
    args = getattr(tp, "__args__", None)
    if args and len(args) == 2:
        return is_iterable_type(args[1])
    return False


def get_dict_kv_arg_type_as_str(tp):
    """
    This takes a type (typing.Mapping[str, int]) and returns a tuple (key_type,
    value_type) that contains string representations of the type arguments, or
    "any" if it's not defined
    """
    assert is_mapping_type(tp), f"{tp} is not a mapping type"
    args = getattr(tp, "__args__", None)
    key_type = "any"
    value_type = "any"
    if args and len(args) >= 2:
        key_type = getattr(args[0], "__name__", str(args[0]))
        value_type = getattr(args[1], "__name__", str(args[1]))
    return key_type, value_type


def get_typing_function(tp):
    func = None

    # TypeVars are a problem as they can defined multiple possible types.
    # While a single type TypeVar is somewhat useless, no reason to deny it
    # though
    if is_typevar(tp):
        if len(tp.__constraints__) == 0:
            # Unconstrained TypeVars may come from generics
            func = _identity_function
        elif len(tp.__constraints__) == 1:
            assert not PEP_560, "Python 3.7+ forbids single constraint for `TypeVar'"
            func = get_typing_function(tp.__constraints__[0])
        else:
            raise ValueError(
                "Cannot resolve typing function for TypeVar({constraints}) "
                "as it declares multiple types".format(
                    constraints=', '.join(
                        getattr(c, "_name", c.__name__) for c in tp.__constraints__
                    )
                )
            )
    elif tp == typing.Any:
        func = _identity_function
    elif issubclass_(tp, str):
        func = str
    elif is_mapping_type(tp):
        func = _apply_dict_type
    elif is_tuple_type(tp):
        func = _apply_tuple_type
    elif is_iterable_type(tp):
        func = _apply_list_type
    elif is_optional_type(tp):
        func = _apply_optional_type
    elif callable(tp):
        func = tp
    else:
        raise ValueError(
            'Cannot find a function to apply type "{}"'.format(tp)
        )

    args = getattr(tp, "__args__", None)

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
    except ValueError as e:
        _, e, tb = sys.exc_info()
        if str(e) == "malformed string":
            # Raise a more meaningful, nicer error
            raise ValueError(f"`{string}' uses unsafe token/symbols") from e
        else:
            raise


def _build_simple_value(string, tp):
    if not tp or issubclass_(tp, str):
        return string
    elif is_mapping_type(tp):
        entries = (
            re.split(r"\s*[:=]\s*", entry, maxsplit=1)
            for entry in string.split(";")
        )
        if is_dict_value_iterable(tp):
            entries = ((k, re.split(r"\s*,\s*", v)) for k, v in entries)
        return {k.strip(): v for k, v in entries}
    elif is_tuple_type(tp):
        return tuple(item for item in string.split(","))
    elif is_iterable_type(tp):
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
