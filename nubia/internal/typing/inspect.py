#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import collections.abc
import sys
from typing import Iterable, Mapping, TypeVar

from nubia.internal.helpers import issubclass_

PEP_560: bool = sys.version_info[:3] >= (3, 7, 0)

if PEP_560:
    from typing import Tuple, Union, _GenericAlias
else:
    from typing import TupleMeta, _Union


def is_none_type(tp) -> bool:
    """Checks whether a type is a `None' type."""
    return tp is type(None)  # noqa E721


def is_union_type(tp) -> bool:
    """Checks whether a type is a union type."""
    if PEP_560:
        return (
            tp is Union
            or isinstance(tp, _GenericAlias)
            and tp.__origin__ is Union
        )
    return type(tp) is _Union


def is_optional_type(tp) -> bool:
    """Checks whether a type is an optional type."""
    return (
        is_union_type(tp)
        and len(tp.__args__) == 2
        and any(map(is_none_type, tp.__args__))
    )


def is_mapping_type(tp) -> bool:
    """Checks whether a type is a mapping type."""
    if PEP_560:
        return (
            tp is Mapping
            or isinstance(tp, _GenericAlias)
            and issubclass_(tp.__origin__, collections.abc.Mapping)
        )
    return issubclass_(tp, collections.abc.Mapping)


def is_tuple_type(tp) -> bool:
    """Checks whether a type is a tuple type."""
    if PEP_560:
        return (
            tp is Tuple
            or isinstance(tp, _GenericAlias)
            and tp.__origin__ is tuple
        )
    return type(tp) is TupleMeta


def is_iterable_type(tp) -> bool:
    """Checks whether a type is an iterable type."""
    if PEP_560:
        return (
            tp is Iterable
            or isinstance(tp, _GenericAlias)
            and issubclass_(tp.__origin__, collections.abc.Iterable)
        )
    return issubclass_(tp, list)


def is_typevar(tp) -> bool:
    """Checks whether a type is a `TypeVar'."""
    return type(tp) is TypeVar


def get_first_type_argument(tp):
    """Returns first type argument, e.g. `int' for `List[int]'."""
    assert hasattr(tp, "__args__") and len(tp.__args__) > 0
    return tp.__args__[0]
