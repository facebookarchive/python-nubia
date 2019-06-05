#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#
import typing as t
import types
import pkgutil


def _walk_module(module: types.ModuleType):
    for attr_name in dir(module):
        # filter out private members
        if not attr_name.startswith("_"):
            member = getattr(module, attr_name)
            if hasattr(member, "__command"):
                yield member


def _walk_package(name, path) -> t.List[types.FunctionType]:
    packages = pkgutil.walk_packages(path, prefix=f"{name}.")
    for importer, modname, ispkg in packages:
        loaded = importer.find_module(modname).load_module(modname)
        if not ispkg:
            yield from _walk_module(loaded)


def load_commands(base_package) -> None:
    """
    Loads all commands defined in a loaded python package object. This function
    recursively look for classes and function annotated with @command and return
    a list of these objects.
    """
    if base_package is not None:
        path = None
        if hasattr(base_package, "__path__"):
            path = getattr(base_package, "__path__")
        else:
            path = getattr(base_package, "__file__")
        assert path is not None
        yield from _walk_package(base_package.__name__, path)
