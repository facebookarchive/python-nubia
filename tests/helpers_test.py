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
    find_approx,
    function_to_str,
    suggestions_msg,
)
from nubia.internal.typing.inspect import is_optional_type


class HelpersTest(unittest.TestCase):
    def test_function_to_str(self):
        def foo(arg1, arg2, *args, **kwargs):
            pass

        def test(expected, with_module, with_args):
            self.assertEqual(function_to_str(foo, with_module, with_args), expected)

        test("foo", False, False)
        test("tests.helpers_test.foo", True, False)
        test("foo(arg1, arg2, *args, **kwargs)", False, True)
        test("tests.helpers_test.foo(arg1, arg2, *args, **kwargs)", True, True)

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

    def test_find_approx(self):
        commands_map = ["maintenance", "malloc", "move", "list"]

        # check levenshtein approximation
        self.assertEqual(find_approx("maintenanec", commands_map), ["maintenance"])
        self.assertEqual(find_approx("ls", commands_map), ["list"])

        # check prefix matching with single result
        self.assertEqual(find_approx("mal", commands_map), ["malloc"])
        self.assertEqual(find_approx("maint", commands_map), ["maintenance"])

        # check prefix matching and levenshtein don't generate duplicate suggestions
        self.assertEqual(find_approx("lis", commands_map), ["list"])

        # check prefix matching with more than one result - should return none
        self.assertEqual(find_approx("ma", commands_map), ["maintenance", "malloc"])
        self.assertEqual(
            find_approx("m", commands_map), ["maintenance", "malloc", "move"]
        )

        # check no results
        self.assertEqual(find_approx("a", commands_map), [])

    def test_is_optional(self):
        self.assertFalse(is_optional_type(List[str]))
        self.assertFalse(is_optional_type(Dict[str, int]))
        self.assertFalse(is_optional_type(Union[str, int]))
        self.assertTrue(is_optional_type(Optional[str]))
        self.assertTrue(is_optional_type(Union[str, None]))

    def test_suggestions_msg(self):
        suggestions = []
        self.assertEqual(suggestions_msg(suggestions), "")

        suggestions = ["one", "two"]
        self.assertEqual(suggestions_msg(suggestions), ", Did you mean one or two?")

        suggestions = ["one", "two", "three"]
        self.assertEqual(
            suggestions_msg(suggestions), ", Did you mean one, two or three?"
        )
