#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

"""
############################################################################
# Python 3 only tests. This is not expected to work on python 2.
# Any test that should work on both python 2 and 3 should go to tests.py
############################################################################
"""

import typing
import unittest

from nubia.internal.typing import argument, inspect_object


class DecoratorTest(unittest.TestCase):
    def test_equality_decorated(self):
        @argument("arg1", description="arg1 desc")
        @argument("arg2", description="arg2 desc")
        def foo(arg1: typing.Any, arg2: str) -> typing.Tuple[str, str]:
            return (arg1, arg2)

        @argument("arg1", type=typing.Any, description="arg1 desc")
        @argument("arg2", type=str, description="arg2 desc")
        def bar(arg1, arg2):
            return (arg1, arg2)

        self.assertEqual(inspect_object(foo), inspect_object(bar))

    def test_inequality_no_decorator(self):
        def foo(arg1: str, arg2: str) -> typing.Tuple[str, str]:
            return (arg1, arg2)

        def bar(arg1, arg2):
            return (arg1, arg2)

        self.assertNotEqual(inspect_object(foo), inspect_object(bar))

    def test_inequality_decorated(self):
        def foo(arg1: str, arg2: str) -> typing.Tuple[str, str]:
            return (arg1, arg2)

        @argument("arg1", type=int)
        @argument("arg2", type=int)
        def bar(arg1, arg2):
            return (arg1, arg2)

        self.assertNotEqual(inspect_object(foo), inspect_object(bar))

    def test_type_conflict(self):

        # specifiying arg as str in both the decorator and in the type
        # annotation is redundant but should be fine
        @argument("arg", type=str)
        def foo(arg: str) -> str:
            return arg

        try:
            # arg is being specified as str by the decorator but as typing.Any
            # by the type annotation. A TypeError should be raised
            @argument("arg", type=str)
            def bar(arg: typing.Any) -> str:
                return arg

            self.fail(
                "foo declaration should fail with TypeError as it "
                "declares arg as both str and typing.Any"
            )
        except TypeError:
            pass
