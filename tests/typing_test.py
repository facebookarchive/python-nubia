#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import argparse
import inspect
import typing
import unittest
from io import StringIO

from nubia.internal.typing import command, argument
from nubia.internal.typing.argparse import add_command, find_command
from nubia.internal.typing.builder import build_value


class ParseError(Exception):
    pass


class ContainedParser(argparse.ArgumentParser):
    """
    Parser that gives options that avoid using sys.stdout, sys.stderr and
    raising SystemExit
    """

    def help(self):
        return self._print_to_buffer(self.print_help)

    def usage(self):
        return self._print_to_buffer(self.print_usage)

    def _print_to_buffer(self, print_function):
        s = StringIO()
        print_function(s)
        return s.getvalue()

    def error(self, message):
        raise ParseError(message)


class SimpleValuesBuilderTest(unittest.TestCase):
    def test_build_string(self):
        value = build_value("some string", str, False)
        self.assertEqual(value, "some string")

        value = build_value('"some string"', str, True)
        self.assertEqual(value, "some string")

    def test_build_int(self):
        value = build_value("1", int, False)
        self.assertEqual(value, 1)

        value = build_value("1", int, True)
        self.assertEqual(value, 1)

    def test_build_custom_type(self):
        def parser(string):
            return string.split("#")

        value = build_value("special#string", parser, False)
        self.assertEqual(value, ["special", "string"])

        value = build_value('"special#string"', parser, True)
        self.assertEqual(value, ["special", "string"])

    def test_build_tuple(self):
        value = build_value("foo bar,1,0.5", typing.Tuple[str, int, float], False)
        self.assertEqual(value, ("foo bar", 1, 0.5))

        value = build_value('("foo bar",1,0.5)', typing.Tuple[str, int, float], True)
        self.assertEqual(value, ("foo bar", 1, 0.5))

    def test_build_tuple_partially_typed(self):
        value = build_value(
            "foo bar,1,0.5", typing.Tuple[str, typing.Any, float], False
        )
        self.assertEqual(value, ("foo bar", "1", 0.5))

        value = build_value(
            '("foo bar",1,0.5)', typing.Tuple[str, typing.Any, float], True
        )
        self.assertEqual(value, (str("foo bar"), 1, 0.5))

    def test_build_tuple_untyped(self):
        value = build_value("foo bar,1,0.5", typing.Tuple, False)
        self.assertEqual(value, ("foo bar", "1", "0.5"))

        value = build_value('("foo bar",1,0.5)', typing.Tuple, True)
        self.assertEqual(value, (str("foo bar"), 1, 0.5))

    def test_build_tuple_single_element(self):
        value = build_value("foo bar", typing.Tuple[str], False)
        self.assertEqual(value, ("foo bar",))

        value = build_value('("foo bar",)', typing.Tuple[str], True)
        self.assertEqual(value, (str("foo bar"),))

    def test_build_typed_dict(self):
        value = build_value("a:1;b:2", typing.Mapping[str, int], False)
        self.assertEqual(value, {"a": 1, "b": 2})

        value = build_value(
            '{"a": "1", "b": 2, "c": 3.2}', typing.Mapping[str, int], True
        )
        self.assertEqual(value, {"a": 1, "b": 2, "c": 3})

    def test_build_typed_dict_mixed(self):
        value = build_value("a=1;b=2", typing.Mapping[str, int], False)
        self.assertEqual(value, {"a": 1, "b": 2})

        value = build_value("a:1;b=2", typing.Mapping[str, int], False)
        self.assertEqual(value, {"a": 1, "b": 2})

    def test_build_typed_dict_with_list(self):
        value = build_value("a=1,2,3;b=2", typing.Mapping[str, str], False)
        self.assertEqual(value, {"a": "1,2,3", "b": "2"})

        value = build_value("a=1,2,3;b=2", typing.Mapping[str, typing.List[int]], False)
        self.assertEqual(value, {"a": [1, 2, 3], "b": [2]})

    def test_build_partially_typed_dict(self):
        value = build_value("a:1;b:2", typing.Mapping[typing.Any, int], False)
        self.assertEqual(value, {"a": 1, "b": 2})

        value = build_value(
            '{"a": "1", "b": 2, 0: 3}', typing.Mapping[typing.Any, int], True
        )
        self.assertEqual(value, {"a": 1, "b": 2, 0: 3})

    def test_build_untyped_dict(self):
        value = build_value("a:1;b:2", typing.Mapping, False)
        self.assertEqual(value, {"a": "1", "b": "2"})

        value = build_value('{"a": 1, "b": 2.5}', typing.Mapping, True)
        self.assertEqual(value, {"a": 1, "b": 2.5})

    def test_build_typed_list(self):
        value = build_value("1,2,3", typing.List[int], False)
        self.assertEqual(value, [1, 2, 3])

        value = build_value("hello,world,test", typing.List[str], False)
        self.assertEqual(value, ["hello", "world", "test"])

        value = build_value("hello", typing.List[str], False)
        self.assertEqual(value, ["hello"])

        value = build_value('["1",2,3.2]', typing.List[int], True)
        self.assertEqual(value, [1, 2, 3])

    def test_build_untyped_list(self):
        value = build_value("1,2,3", typing.List, False)
        self.assertEqual(value, ["1", "2", "3"])

        value = build_value('["1",2,3.5]', typing.List, True)
        self.assertEqual(value, ["1", 2, 3.5])

    def test_build_any_typed_list(self):
        value = build_value("1,2,3", typing.List[typing.Any], False)
        self.assertEqual(value, ["1", "2", "3"])

        value = build_value('["1",2,3.5]', typing.List[typing.Any], True)
        self.assertEqual(value, ["1", 2, 3.5])

    def test_build_whitespaces(self):
        value = build_value(" a : 1 ; b : 2 ", typing.Mapping[str, int], False)
        self.assertEqual(value, {"a": 1, "b": 2})

        value = build_value('{ "a" : 1 , "b" : 2 }', typing.Mapping[str, int], True)
        self.assertEqual(value, {"a": 1, "b": 2})

        value = build_value(" 1 , 2 , 3 ", typing.List[int], False)
        self.assertEqual(value, [1, 2, 3])

        value = build_value("[ 1 , 2 , 3 ]", typing.List[int], True)
        self.assertEqual(value, [1, 2, 3])

        value = build_value(" 1 , 2 , 3 ", typing.Tuple[int, int, int], False)
        self.assertEqual(value, (1, 2, 3))

        value = build_value("( 1 , 2 , 3 )", typing.Tuple[int, int, int], True)
        self.assertEqual(value, (1, 2, 3))

    def test_build_with_casting(self):
        value = build_value("a:1;b:2;c:3", typing.Mapping[str, float])
        self.assertEqual(value, {"a": 1.0, "b": 2.0, "c": 3.0})

        value = build_value("a:1;b:2;c:3", typing.Mapping[str, str])
        self.assertEqual(value, {"a": "1", "b": "2", "c": "3"})

        self.assertRaises(
            ValueError, build_value, "a:1;b:2;c:3", typing.Mapping[int, int]
        )

    def test_build_nested_structures(self):
        inpt = """{
            "a": 1,
            "b": {
                "c": [2, 3, 4, [5, 6]]
            }
        }"""
        expected = {"a": 1, "b": {"c": [2, 3, 4, [5, 6]]}}
        expected_type = typing.Any
        self.assertEqual(build_value(inpt, expected_type, True), expected)

        inpt = """{
            "a": [ [1, 2], [3, 4] ],
            "b": [ [10, 20, 30], [40] ]
        }"""
        expected = {"a": [[1, 2], [3, 4]], "b": [[10, 20, 30], [40]]}
        # dict of str => list of list of ints
        expected_type = typing.Mapping[str, typing.List[typing.List[int]]]
        self.assertEqual(build_value(inpt, expected_type, True), expected)

    def test_build_tuple_error(self):
        # too many arguments
        self.assertRaises(
            ValueError,
            build_value,
            "foo bar,1,0.5,extra!",
            typing.Tuple[str, int, float],
            False,
        )

        self.assertRaises(
            ValueError,
            build_value,
            '("foo bar", 1, 0.5, "extra!")',
            typing.Tuple[str, int, float],
            True,
        )

        # too few arguments
        self.assertRaises(
            ValueError, build_value, "foo bar", typing.Tuple[str, int, float], False
        )

        self.assertRaises(
            ValueError, build_value, '("foo bar",)', typing.Tuple[str, int, float], True
        )


class ArgparseExtensionTest(unittest.TestCase):
    def test_no_decorator_simple(self):
        def foo():
            return "bar"

        def foo2(arg1, arg2):
            return (arg1, arg2)

        self._test(foo, "foo".split(), "bar")
        self._test(
            foo,
            "foo --invalid arg".split(),
            ParseError("unrecognized arguments: --invalid arg"),
        )

        self._test(foo2, "foo2 --arg1=abc --arg2=123".split(), ("abc", "123"))
        self._test(foo2, "foo2 --arg1 abc --arg2 123".split(), ("abc", "123"))

    def test_no_decorator_defaults(self):
        def foo(arg1="bar"):
            return arg1

        def foo2(arg1=True):
            return arg1

        def foo3(arg1=False):
            return arg1

        self._test(foo, "foo".split(), "bar")
        self._test(foo, "foo --arg1 lol".split(), "lol")

        # boolean args are exposed as flags that works as on/off switches
        # if the argument default is True, the flag works as an "off" switch
        self._test(foo2, "foo2".split(), True)
        self._test(foo2, "foo2 --arg1".split(), False)
        # if the argument default is False, the flag works as an "on" switch
        self._test(foo3, "foo3".split(), False)
        self._test(foo3, "foo3 --arg1".split(), True)

    def test_argument_decorated_simple(self):
        @argument("arg1")
        @argument("arg2")
        def foo(arg1, arg2):
            return "{} {}".format(arg1, arg2)

        self._test(foo, "foo --arg1 Hello --arg2 World".split(), "Hello World")

    def test_argument_decorated_different_name(self):
        @argument("arg1", name="banana")
        @argument("arg2", name="apple")
        def foo(arg1, arg2):
            return "{} {}".format(arg1, arg2)

        # arg2 is not decorated
        @argument("arg1", name="banana")
        def foo2(arg1, arg2):
            return "{} {}".format(arg1, arg2)

        # arg2 is decorated but pretty much useless in this form
        @argument("arg1", name="banana")
        @argument("arg2")
        def foo3(arg1, arg2):
            return "{} {}".format(arg1, arg2)

        self._test(foo, "foo --banana Hello --apple World".split(), "Hello World")
        self._test(foo2, "foo2 --banana Hello --arg2 World".split(), "Hello World")
        self._test(foo3, "foo3 --banana Hello --arg2 World".split(), "Hello World")

        self._test(foo, "foo --arg1 Hello --apple World".split(), ParseError)

    def test_argument_decorated_aliases(self):
        @argument("arg", aliases=["banana", "apple", "b", "a"])
        def foo(arg):
            return arg

        self._test(foo, "foo --arg bar".split(), "bar")
        self._test(foo, "foo --banana bar".split(), "bar")
        self._test(foo, "foo --apple bar".split(), "bar")
        self._test(foo, "foo -b bar".split(), "bar")
        self._test(foo, "foo -a bar".split(), "bar")

    def test_argument_decorated_kwargs(self):
        @argument("arg", type=int, description="arg help")
        @argument("extra_arg", type=int, description="extra")
        def foo(arg, **kwargs):
            return (arg, kwargs)

        self._test(foo, "foo --arg 6".split(), (6, {"extra_arg": None}))
        self._test(foo, "foo --extra-arg 15".split(), ParseError)
        self._test(foo, "foo --arg 14 --another-extra-arg 15".split(), ParseError)
        self._test(foo, "foo --arg 3 --extra-arg 15".split(), (3, {"extra_arg": 15}))

    def test_argument_decorated_naming_conventions(self):
        @argument("arg_1", aliases=["_argument__1"])
        @argument("arg_2", name="_argument___2")
        def __foo__bar__(arg_1, arg_2):
            return "{} {}".format(arg_1, arg_2)

        self._test(__foo__bar__, "foo-bar --arg-1 x --argument-2 y".split(), "x y")
        self._test(__foo__bar__, "foo-bar --argument-1 x --argument-2 y".split(), "x y")

    def test_argument_dict_list_type_lifting(self):
        @argument("arg_1", type=typing.Mapping[str, int])
        @argument("arg_2", type=typing.List[int])
        def __foo__bar__(arg_1, arg_2):
            return (arg_1, arg_2)

        self._test(__foo__bar__, "foo-bar --arg-1 x --arg-2 y".split(), ParseError)

        self._test(__foo__bar__, "foo-bar --arg-1 1 --arg-2 2".split(), ParseError)
        self._test(
            __foo__bar__,
            "foo-bar --arg-1 allData=1 --arg-2 2".split(),
            ({"allData": 1}, [2]),
        )
        self._test(
            __foo__bar__,
            "foo-bar --arg-1 all=1;nothing-data:2 --arg-2 2".split(),
            ({"all": 1, "nothing-data": 2}, [2]),
        )
        self._test(
            __foo__bar__,
            "foo-bar --arg-1 all=1;nothing-data=2 --arg-2 2".split(),
            ({"all": 1, "nothing-data": 2}, [2]),
        )
        self._test(
            __foo__bar__,
            "foo-bar --arg-1 all=1;nothing-data=2 --arg-2 2 3".split(),
            ({"all": 1, "nothing-data": 2}, [2, 3]),
        )
        self._test(
            __foo__bar__,
            "foo-bar --arg-1 all=1;nothing-data=2 --arg-2 2 3".split(),
            ({"all": 1, "nothing-data": 2}, [2, 3]),
        )

    def test_argument_list_in_dict_type_lifting(self):
        @argument("arg_1", type=typing.Mapping[str, typing.List[int]])
        def __foo__bar__(arg_1):
            return arg_1

        self._test(__foo__bar__, "foo-bar --arg-1 x".split(), ParseError)

        self._test(__foo__bar__, "foo-bar --arg-1 allData=1".split(), {"allData": [1]})
        self._test(
            __foo__bar__,
            "foo-bar --arg-1 all=1;nothing-data:2".split(),
            {"all": [1], "nothing-data": [2]},
        )
        self._test(
            __foo__bar__,
            "foo-bar --arg-1 all=1,2,3;nothing-data=2".split(),
            {"all": [1, 2, 3], "nothing-data": [2]},
        )
        self._test(
            __foo__bar__,
            "foo-bar --arg-1 all=1;nothing-data=2,2,3".split(),
            {"all": [1], "nothing-data": [2, 2, 3]},
        )

    def test_argument_decorated_unknown_arg(self):
        with self.assertRaises(NameError):

            @argument("arg1", description="arg1 description")
            @argument("bar", description="this arg doesnt exist!")
            def foo(arg1, arg2):
                pass

    def test_kwargs(self):
        try:

            @argument("arg1", description="this exists!")
            def foo(arg1, **kwargs):
                pass

        except Exception as e:
            self.fail("Should not have thrown: {}".format(e))

    def test_kwargs_with_arguments(self):
        try:

            @argument("arg1", description="this exists!")
            @argument("arg2", description="this is in kwargs!")
            def foo(arg1, **kwargs):
                pass

        except Exception as e:
            self.fail("Should not have thrown: {}".format(e))

    def test_command_decorator_presence(self):
        def foo():
            return "bar"

        self._test(foo, ["foo"], "bar")
        self._test(command(foo), ["foo"], "bar")
        self._test(command()(foo), ["foo"], "bar")

    def test_command_exclusive_args_simple(self):
        @command(exclusive_arguments=["arg1", "arg2"])
        def foo(arg1="", arg2="", arg3=""):
            return ",".join(str(arg) for arg in (arg1, arg2, arg3))

        self._test(foo, "foo --arg1=bar".split(), "bar,,")
        self._test(foo, "foo --arg2=bar".split(), ",bar,")
        self._test(foo, "foo --arg3=bar".split(), ",,bar")
        self._test(foo, "foo --arg1=bar --arg3=bar".split(), "bar,,bar")
        self._test(foo, "foo --arg2=bar --arg3=bar".split(), ",bar,bar")

        self._test(foo, "foo --arg1=bar --arg2=bar".split(), ParseError)
        self._test(foo, "foo --arg1=bar --arg2=bar --arg3=bar".split(), ParseError)

    def test_command_exclusive_args_array(self):
        @command(exclusive_arguments=[["arg1", "arg2"], ["arg3", "arg4"]])
        def foo(arg1="", arg2="", arg3="", arg4=""):
            return ",".join(str(arg) for arg in (arg1, arg2, arg3, arg4))

        self._test(foo, "foo --arg1=bar".split(), "bar,,,")
        self._test(foo, "foo --arg2=bar".split(), ",bar,,")
        self._test(foo, "foo --arg3=bar".split(), ",,bar,")
        self._test(foo, "foo --arg4=bar".split(), ",,,bar")
        self._test(foo, "foo --arg1=bar --arg3=bar".split(), "bar,,bar,")
        self._test(foo, "foo --arg1=bar --arg4=bar".split(), "bar,,,bar")
        self._test(foo, "foo --arg2=bar --arg3=bar".split(), ",bar,bar,")
        self._test(foo, "foo --arg2=bar --arg4=bar".split(), ",bar,,bar")

        self._test(foo, "foo --arg1=bar --arg2=bar".split(), ParseError)
        self._test(foo, "foo --arg3=bar --arg4=bar".split(), ParseError)
        self._test(
            foo, "foo --arg1=bar --arg2=bar --arg3=bar --arg4=bar".split(), ParseError
        )

    def test_command_repeated_exclusive_args(self):
        with self.assertRaises(ValueError):
            # arg1 is present in two exclusive groups
            @command(exclusive_arguments=[["arg1", "arg2"], ["arg1", "arg3"]])
            def foo(arg1="", arg2="", arg3=""):
                pass

    def test_command_unknown_exclusive_args(self):
        with self.assertRaises(NameError):
            # arg bar doesnt exist
            @command(exclusive_arguments=[["arg1", "bar"]])
            def foo(arg1="", arg2="", arg3=""):
                pass

    def test_duplicate_argument_decorator(self):
        with self.assertRaises(ValueError):
            # two refs to the same arg
            @command
            @argument("arg", name="arg1")
            @argument("arg", name="arg2")
            def foo(arg=1):
                pass

    def test_positional_arg(self):
        @argument("arg", positional=True)
        def foo(arg):
            return arg

        self._test(foo, "foo lalala", "lalala")

    def test_positional_arg_with_default(self):
        @argument("arg1", positional=True)
        @argument("arg2")
        def foo(arg1, arg2="default_arg1"):
            return "{},{}".format(arg1, arg2)

        self._test(foo, "foo lalala", "lalala,default_arg1")
        self._test(foo, "foo lalala --arg2 bububu", "lalala,bububu")
        self._test(foo, "foo --arg2 bububu lalala", "lalala,bububu")

    def test_only_single_value_allowed_for_positional(self):
        @argument("arg1", positional=True)
        def foo(arg1):
            pass

        self._test(foo, "foo lalala bububu", ParseError)

    def test_missing_positional(self):
        @argument("arg", positional=True)
        def foo(arg):
            pass

        self._test(foo, "foo", ParseError)

    def test_multiple_positionals(self):
        @argument("arg1", positional=True)
        @argument("arg2", positional=True)
        @argument("arg3")
        def foo(arg1, arg2, arg3="default"):
            return ",".join([arg1, arg2, arg3])

        self._test(foo, "foo arg1v arg2v", "arg1v,arg2v,default")
        self._test(foo, "foo arg1v arg2v --arg3 arg3v", "arg1v,arg2v,arg3v")
        self._test(foo, "foo arg1v --arg3 arg3v arg2v", "arg1v,arg2v,arg3v")
        self._test(foo, "foo --arg3 arg3v arg1v arg2v", "arg1v,arg2v,arg3v")

    def test_multiple_positionals_not_relates_to_decorator(self):
        # just all permutations of three decorators

        @argument("arg1", positional=True)
        @argument("arg2", positional=True)
        @argument("arg3", positional=True)
        def foo(arg1, arg2, arg3):
            return ",".join([arg1, arg2, arg3])

        self._test(foo, "foo arg1v arg2v arg3v", "arg1v,arg2v,arg3v")

        @argument("arg1", positional=True)
        @argument("arg3", positional=True)
        @argument("arg2", positional=True)
        def foo(arg1, arg2, arg3):
            return ",".join([arg1, arg2, arg3])

        self._test(foo, "foo arg1v arg2v arg3v", "arg1v,arg2v,arg3v")

        @argument("arg2", positional=True)
        @argument("arg1", positional=True)
        @argument("arg3", positional=True)
        def foo(arg1, arg2, arg3):
            return ",".join([arg1, arg2, arg3])

        self._test(foo, "foo arg1v arg2v arg3v", "arg1v,arg2v,arg3v")

        @argument("arg2", positional=True)
        @argument("arg3", positional=True)
        @argument("arg1", positional=True)
        def foo(arg1, arg2, arg3):
            return ",".join([arg1, arg2, arg3])

        self._test(foo, "foo arg1v arg2v arg3v", "arg1v,arg2v,arg3v")

        @argument("arg3", positional=True)
        @argument("arg1", positional=True)
        @argument("arg2", positional=True)
        def foo(arg1, arg2, arg3):
            return ",".join([arg1, arg2, arg3])

        self._test(foo, "foo arg1v arg2v arg3v", "arg1v,arg2v,arg3v")

        @argument("arg3", positional=True)
        @argument("arg2", positional=True)
        @argument("arg1", positional=True)
        def foo(arg1, arg2, arg3):
            return ",".join([arg1, arg2, arg3])

        self._test(foo, "foo arg1v arg2v arg3v", "arg1v,arg2v,arg3v")

    def test_positional_with_default(self):
        msg = (
            "We explicitly do not support positional "
            "with default because it is confusing"
        )
        with self.assertRaises(ValueError, msg=msg):

            @command
            @argument("arg", positional=True)
            def foo(arg="default"):
                return arg

            # validation happens on building parser time so let's build one
            parser = ContainedParser()
            add_command(parser, foo)

    def test_positional_with_aliases(self):
        msg = "Aliases for positional not yet supported"
        with self.assertRaises(ValueError, msg=msg):

            @command
            @argument("arg", positional=True, aliases=["a"])
            def foo(arg="default"):
                return arg

            # validation happens on building parser time so let's build one
            parser = ContainedParser()
            add_command(parser, foo)

    def _test(self, command_function, arguments, expected_result):
        if isinstance(arguments, str):
            arguments = arguments.split()

        parser = ContainedParser()
        add_command(parser, command_function)
        try:
            parsed = parser.parse_args(args=arguments)
        except Exception as e:
            if inspect.isclass(expected_result):
                self.assertIsInstance(e, expected_result)
            elif isinstance(expected_result, ParseError):
                self.assertEqual(str(e), str(expected_result))
            else:
                raise
        else:
            command_function = find_command(parser, parsed, True)
            self.assertEqual(command_function(), expected_result)
