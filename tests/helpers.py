#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import unittest
from typing import Dict, List, Optional, Union

from nubia.internal.helpers import (
    catchall,
    function_to_str,
    get_left_type,
    is_optional,
    is_union,
)


class HelpersTest(unittest.TestCase):
    def test_function_to_str(self):
        def foo(arg1, arg2, *args, **kwargs):
            pass

        def test(expected, with_module, with_args):
            self.assertEquals(
                function_to_str(foo, with_module, with_args), expected
            )

        test("foo", False, False)
        test("tests.helpers.foo", True, False)
        test("foo(arg1, arg2, *args, **kwargs)", False, True)
        test("tests.helpers.foo(arg1, arg2, *args, **kwargs)", True, True)

    def test_catchall(self):
        def raise_generic_error():
            raise RuntimeError()

        def raise_keyboard_interrupt():
            raise KeyboardInterrupt()

        def raise_sysexit():
            raise SystemExit()

        # expected catch all errors except keyboard, sysexit
        catchall(raise_generic_error)
        self.assertRaises(KeyboardInterrupt, catchall, raise_keyboard_interrupt)
        self.assertRaises(SystemExit, catchall, raise_sysexit)

    def test_is_union(self):
        self.assertTrue(is_union(Union[str, int]))
        self.assertFalse(is_union(List[str]))
        self.assertFalse(is_union(Dict[str, int]))

    def test_is_optional(self):
        self.assertFalse(is_optional(List[str]))
        self.assertFalse(is_optional(Dict[str, int]))
        self.assertFalse(is_optional(Union[str, int]))
        self.assertTrue(is_optional(Optional[str]))
        self.assertTrue(is_optional(Union[str, None]))

    def test_get_left_type(self):
        self.assertIs(get_left_type(Union[str, None]), str)
        self.assertIs(get_left_type(Optional[str]), str)
        self.assertIsNot(get_left_type(Union[str, None]), None)
        self.assertIsNot(get_left_type(Optional[str]), None)
