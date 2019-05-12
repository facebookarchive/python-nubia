#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import inspect
import re
import signal
import string
import subprocess

from collections import namedtuple


def add_command_arguments(parser, options):
    for option, extras in options.items():
        parser.add_argument("--{}".format(option), **extras)


def run_process(process_arg_list, on_interrupt=None, working_dir=None):
    """
    This runs a process using subprocess python module but handles SIGINT
    properly. In case we received SIGINT (Ctrl+C) we will send a SIGTERM to
    terminate the subprocess and call the supplied callback.

    @param process_arg_list Is the list you would send to subprocess.Popen()
    @param on_interrupt     Is a python callable that will be called in case we
                            received SIGINT

    This may raise OSError if the command doesn't exist.

    @return the return code of this process after completion
    """
    assert isinstance(process_arg_list, list)
    old_handler = signal.getsignal(signal.SIGINT)
    process = subprocess.Popen(process_arg_list, cwd=working_dir)

    def handler(signum, frame):
        process.send_signal(signal.SIGTERM)
        # call the interrupted callack
        if on_interrupt:
            on_interrupt()

    # register the signal handler
    signal.signal(signal.SIGINT, handler)
    rv = process.wait()
    # after the process terminates, restore the original SIGINT handler
    # whatever it was.
    signal.signal(signal.SIGINT, old_handler)
    return rv


FullArgSpec = namedtuple(
    "FullArgSpec",
    (
        "args",
        "varargs",
        "varkw",
        "defaults",
        "kwonlyargs",
        "kwonlydefaults",
        "annotations",
    ),
)


def get_arg_spec(function):
    """
    Basic backport of python's 3 inspect.gefullargspec to python 2
    """

    def set_default_value(dictionary, key, value):
        if not dictionary.get(key, None):
            dictionary[key] = value

    if hasattr(inspect, "getfullargspec"):
        argspec = inspect.getfullargspec(function)._asdict()
        argspec["annotations"].update(getattr(function, "__annotations__", {}))
    else:
        argspec = inspect.getargspec(function)._asdict()
        # python 3 renamed keywords for varkw
        argspec["varkw"] = argspec.pop("keywords")
        argspec["annotations"] = getattr(function, "__annotations__", None)

    for field in ["args", "defaults", "kwonlyargs"]:
        set_default_value(argspec, field, [])
    for field in ["kwonlydefaults", "annotations"]:
        set_default_value(argspec, field, {})

    return FullArgSpec(**argspec)


def get_kwargs_for_function(function, **kwargs):
    arg_spec = get_arg_spec(function)
    return (
        dict(kwargs)
        if arg_spec.varkw
        else {k: v for k, v in kwargs.items() if k in arg_spec.args}
    )


def function_to_str(function, with_module=True, with_args=True):
    """
    Returns a nice string representation of a function
    """
    string = getattr(function, "__name__", str(function))
    if with_module:
        string = "{}.{}".format(function.__module__, string)
    if with_args:
        argspec = get_arg_spec(function)
        args_string = ", ".join(argspec.args)
        if argspec.varargs:
            args_string = "{}, *{}".format(args_string, argspec.varargs)
        if argspec.varkw:
            args_string = "{}, **{}".format(args_string, argspec.varkw)
        string = "{}({})".format(string, args_string)
    return string


def transform_name(name, from_char="_", to_char="-"):
    """
    Transforms a symbol from code into something more user friendly
    For instance:
        _foo_bar => foo-bar
        __special__ => special
    """
    name = name.strip()
    # transforms one or more underscores into dashes. Also remove any
    # trailing or leading one
    # e.g, some__very___special -> some-very-special
    name = re.sub(r"{}+".format(re.escape(from_char)), to_char, name)
    name = re.sub(r"^{c}|{c}$".format(c=re.escape(to_char)), "", name)
    if not name:
        raise ValueError('Invalid name "{}"'.format(name))
    return name


def transform_class_name(name):
    """
    Tranforms a camel-case class name into dashed name. This also swaps
    underscores if exists
    """
    new_name = transform_name(name)
    res = []
    for c in new_name:
        if c in string.ascii_uppercase and len(res) > 0:
            res.append("-")
            res.append(c.lower())
        else:
            res.append(c.lower())
    return "".join(res)


# TypeError. In this case the object is clearly not a subclass, so we
# override this behavior for returning False
def issubclass_(obj, class_):
    try:
        return issubclass(obj, class_)
    except (AttributeError, TypeError):
        return False


def catchall(func, *args):
    """
    Run the given function with the given arguments,
    and make sure it never crashes.
    Note: This still allows some BaseExceptions,
    like SystemExit and KeyboardInterrupt
    """
    try:
        func(*args)
    except Exception as e:
        print("Error logging to scuba: {}".format(str(e)))
