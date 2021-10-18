#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import collections.abc
from typing import Iterable, List, Mapping

# This is re-exported, add more if you need more from typing_inspect elsewhere.
from typing_inspect import is_optional_type  # noqa
from typing_inspect import NEW_TYPING, is_tuple_type, is_typevar, is_union_type

from nubia.internal.helpers import issubclass_

if NEW_TYPING:
    from typing import _GenericAlias


def _is_generic_alias_of(this, that) -> bool:
    return isinstance(this, _GenericAlias) and issubclass_(this.__origin__, that)


def is_none_type(tp) -> bool:
    """Checks whether a type is a `None' type."""
    return tp is type(None)  # noqa E721


def is_mapping_type(tp) -> bool:
    """Checks whether a type is a mapping type."""
    if NEW_TYPING:
        return tp is Mapping or _is_generic_alias_of(tp, collections.abc.Mapping)
    return issubclass_(tp, collections.abc.Mapping)


def is_iterable_type(tp) -> bool:
    """Checks whether a type is an iterable type."""
    if NEW_TYPING:
        return tp is Iterable or _is_generic_alias_of(tp, collections.abc.Iterable)
    return issubclass_(tp, list)


def get_first_type_argument(tp):
    """Returns first type argument, e.g. `int' for `List[int]'."""
    assert hasattr(tp, "__args__") and len(tp.__args__) > 0
    return tp.__args__[0]


def is_list_type(tp) -> bool:
    """Checks whether a type is a typing.List."""
    if NEW_TYPING:
        return tp is List or _is_generic_alias_of(tp, list)
    return issubclass_(tp, list)
