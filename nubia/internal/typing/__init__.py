#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

"""
Module for giving type support for nubia

Check argparse.py for functions to work along with argparse in the cli mode
Check builder.py for functions to work along with nubia in interactive mode

This module contains 3 important functions:
- command
- argument
- inspect_object

`command` and `argument` are function/method decorators. It works as an
annotation and is meant to be used only on top of the function/method
declaration. They are used together to indicate that a particular function
or method should be exported for usage in nubia

For example, the following `foo` function can be exported as the `execute`
command:
    @command('execute', help='This command executes something')
    @argument('arg1', type=str, description='arg1 must be a string',
              aliases=['a'])
    @argument('arg2', type=typing.List[int],
              description='arg2 must be a list of integers'
              aliases=['b'])
    def foo(arg1, arg2):
        ...

And then it can be called in the cli as
    % my_prog -t <tier> execute -a something -b 1,2,3

or in nubia interactive mode as
    execute a=something b=[1,2,3]

`foo` will be called already with the correct types as well

Use `inspect_object` to analyze and retrieve the added metadata of an
annotated function/method

Check tests.py present in this module for more usage examples

Notes:
The @argument decorator is compatible with python 3 typing annotations. The
following example achieves the exact same result as the example above:

    @command('execute', help='This command executes something')
    @argument('arg1', description='arg1 must be a string', aliases=['a'])
    @argument('arg2', description='arg2 must be a list of integers'
              aliases=['b'])
    def foo(arg1: str, arg2: typing.List[int]):
        ...
"""


from collections import namedtuple, OrderedDict
from collections.abc import Container
from functools import partial
from inspect import ismethod, isclass

from termcolor import cprint

from nubia.internal.helpers import (
    get_arg_spec,
    function_to_str,
    transform_name,
    transform_class_name,
)


Argument = namedtuple(
    "Argument",
    "arg description type "
    "default_value_set default_value "
    "name extra_names positional choices",
)

Command = namedtuple("Command", "name help aliases exclusive_arguments")

FunctionInspection = namedtuple(
    "FunctionInspection", "arguments " "command subcommands"
)
_ArgDecoratorSpec = namedtuple(
    "_ArgDecoratorSpec", "arg name aliases description positional choices"
)


def _empty_arg_decorator_spec(arg):
    return _ArgDecoratorSpec(
        arg=arg,
        name=transform_name(arg),
        aliases=[],
        description=None,
        positional=False,
        choices=None,
    )


def append_doc(func, arg, type, description):
    func.__doc__ = "%s\r\n\r\n%s\t%s\t%s" % (
        func.__doc__,
        arg.ljust(30, " "),
        type,
        description.replace("\n", ""),
    )
    return func


def argument(
    arg,
    type=None,
    description=None,
    name=None,
    aliases=None,
    positional=False,
    choices=None,
):
    """
    Annotation decorator to specify metadata for an argument

    Check the module documentation for more info and tests.py in this module
    for usage examples
    """

    def decorator(function):
        # Following makes interactive really slow. (T20898480)
        # This should be revisited in T20899641
        #  if (description is not None and \
        #       arg is not None and type is not None):
        #      append_doc(function, arg, type, description)
        fn_specs = get_arg_spec(function)
        args = fn_specs.args or []
        if arg not in args and not fn_specs.varkw:
            raise NameError(
                "Argument {} does not exist in function {}".format(
                    arg, function_to_str(function)
                )
            )

        # init structures to store decorator data if not present
        _init_attr(function, "__annotations__", OrderedDict())
        _init_attr(function, "__arguments_decorator_specs", {})

        # Check if there is a conflict in type annotations
        current_type = function.__annotations__.get(arg)
        if current_type and type and current_type != type:
            raise TypeError(
                "Argument {} in {} is both specified as {} "
                "and {}".format(
                    arg, function_to_str(function), current_type, type
                )
            )

        if arg in function.__arguments_decorator_specs:
            raise ValueError(
                "@argument decorator was applied twice "
                "for the same argument {} on function {}".format(arg, function)
            )

        if positional and aliases:
            msg = "Aliases are not yet supported for positional arguments @ {}".format(
                arg
            )
            raise ValueError(msg)

        # reject positional=True if we are applied over a class
        if isclass(function) and positional:
            raise ValueError(
                "Cannot set positional arguments for super " "commands"
            )

        # We use __annotations__ to allow the usage of python 3 typing
        function.__annotations__.setdefault(arg, type)

        function.__arguments_decorator_specs[arg] = _ArgDecoratorSpec(
            arg=arg,
            description=description,
            name=name or transform_name(arg),
            aliases=aliases or [],
            positional=positional,
            choices=choices or [],
        )

        return function

    return decorator


def command(
    name_or_function=None, help=None, aliases=None, exclusive_arguments=None
):
    """
    Annotation decorator to specify that a function or method is a command
    that should be exported by nubia

    Check the module documentation for more info and tests.py in this module
    for usage examples
    """

    def decorator(function, name=None):
        is_supercommand = isclass(name_or_function)
        exclusive_arguments_ = _normalize_exclusive_arguments(
            exclusive_arguments
        )
        _validate_exclusive_arguments(function, exclusive_arguments_)

        _init_attr(function, "__command", {})
        if name:
            function.__command["name"] = name
        else:
            function.__command["name"] = (
                transform_name(function.__name__)
                if not is_supercommand
                else transform_class_name(function.__name__)
            )
        function.__command["help"] = help
        function.__command["aliases"] = aliases or []
        function.__command["exclusive_arguments"] = exclusive_arguments_
        return function

    # Allows the decorator to be used directly (`@command`) or as a
    # function call (`@command()`)
    if callable(name_or_function):
        function = name_or_function
        return decorator(function)
    else:
        name = name_or_function
        return partial(decorator, name=name)


def inspect_object(obj, accept_bound_methods=False):
    """
    Used to inspect a function or method annotated with @command or
    @argument. Returns a well structured dict summarizing the metadata added
    through the decorators

    Check the module documentation for more info
    """

    command = getattr(obj, "__command", None)
    arguments_decorator_specs = getattr(obj, "__arguments_decorator_specs", {})

    argspec = get_arg_spec(obj)

    args = argspec.args
    # remove the first argument in case this is a method (normally the first
    # arg is 'self')
    if ismethod(obj):
        args = args[1:]

    result = {"arguments": OrderedDict(), "command": None, "subcommands": {}}

    if command:
        result["command"] = Command(
            name=command["name"] or obj.__name__,
            help=command["help"] or obj.__doc__,
            aliases=command["aliases"],
            exclusive_arguments=command["exclusive_arguments"],
        )

    # Is this a super command?
    is_supercommand = isclass(obj)

    for i, arg in enumerate(args):
        if (is_supercommand or accept_bound_methods) and arg == "self":
            continue
        arg_idx_with_default = len(args) - len(argspec.defaults)
        default_value_set = bool(argspec.defaults and i >= arg_idx_with_default)
        default_value = (
            argspec.defaults[i - arg_idx_with_default]
            if default_value_set
            else None
        )
        # We will reject classes (super-commands) that has required arguments to
        # reduce complexity
        if is_supercommand and not default_value_set:
            raise ValueError(
                "Cannot accept super commands that has required "
                "arguments with no default value "
                "like '{}' in super-command '{}'".format(
                    arg, result["command"].name
                )
            )
        arg_decor_spec = arguments_decorator_specs.get(
            arg, _empty_arg_decorator_spec(arg)
        )

        result["arguments"][arg_decor_spec.name] = Argument(
            arg=arg_decor_spec.arg,
            description=arg_decor_spec.description,
            type=argspec.annotations.get(arg),
            default_value_set=default_value_set,
            default_value=default_value,
            name=arg_decor_spec.name,
            extra_names=arg_decor_spec.aliases,
            positional=arg_decor_spec.positional,
            choices=arg_decor_spec.choices,
        )
    if argspec.varkw:
        # We will inject all the arguments that are not defined explicitly in
        # the function signature.
        for arg, arg_decor_spec in arguments_decorator_specs.items():
            added_arguments = [v.name for v in result["arguments"].values()]
            if arg_decor_spec.name not in added_arguments:
                # This is an extra argument
                result["arguments"][arg_decor_spec.name] = Argument(
                    arg=arg,
                    description=arg_decor_spec.description,
                    type=argspec.annotations.get(arg),
                    default_value_set=True,
                    default_value=None,
                    name=arg_decor_spec.name,
                    extra_names=arg_decor_spec.aliases,
                    positional=arg_decor_spec.positional,
                    choices=arg_decor_spec.choices,
                )

    # Super Command Support
    if is_supercommand:
        result["subcommands"] = []
        for attr in dir(obj):
            if attr.startswith("_"):  # ignore "private" methods
                continue
            candidate = getattr(obj, attr)
            if not callable(candidate):  # avoid e.g. properties
                continue
            metadata = inspect_object(candidate, accept_bound_methods=True)
            # ignore subcommands without docstring
            if not metadata.command.help:
                cprint((f"[WARNING] The sub-command {metadata.command.name} "
                        "will not be loaded. "
                        "Please provide a help message by either defining a "
                        "docstring or filling the help argument in the "
                        "@command annotation"), "red")
                continue
            if metadata.command:
                result["subcommands"].append((attr, metadata))

    return FunctionInspection(**result)


def _init_attr(obj, attribute, default_value):
    if not hasattr(obj, attribute):
        setattr(obj, attribute, default_value)


def _normalize_exclusive_arguments(exclusive_arguments):
    """
    Guarantees that exclusive arguments is normalized to a tuple of tuples
    or None in case exclusive_arguments is empty
    """

    def all_string_items(items):
        return all(isinstance(item, str) for item in items)

    def all_container_items(items):
        return all(
            isinstance(item, Container) and not isinstance(item, str)
            for item in items
        )

    if not exclusive_arguments:
        return None

    if all_string_items(exclusive_arguments):
        return (tuple(exclusive_arguments),)

    is_container_of_container_of_strings = all_container_items(
        exclusive_arguments
    ) and all(all_string_items(item) for item in exclusive_arguments)

    if not is_container_of_container_of_strings:
        raise ValueError(
            "exclusive_arguments is not an array of "
            "strings or an array of arrays of strings"
        )

    return tuple(tuple(group) for group in exclusive_arguments)


def _validate_exclusive_arguments(function, normalized_exclusive_arguments):
    if not normalized_exclusive_arguments:
        return

    exclusive_arguments = normalized_exclusive_arguments
    flat_ex_args = [arg for group in exclusive_arguments for arg in group]

    if not flat_ex_args:
        return

    inspection = inspect_object(function)
    possible_args = list(inspection.arguments.keys())

    unknown_args = set(flat_ex_args) - set(possible_args)
    if unknown_args:
        msg = (
            "The following arguments were specified as exclusive but they "
            "are not present in function {}: {}".format(
                function_to_str(function), ", ".join(unknown_args)
            )
        )
        raise NameError(msg)

    if len(set(flat_ex_args)) != len(flat_ex_args):
        counts = (
            (item, group.count(item))
            for group in exclusive_arguments
            for item in group
        )
        repeated_args = [item for item, count in counts if count > 1]
        msg = (
            "The following args are present in more than one exclusive "
            "group: {}".format(", ".join(repeated_args))
        )
        raise ValueError(msg)
