#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

from functools import wraps
from typing import Any, Dict, Optional

from termcolor import cprint

from nubia.internal.typing import inspect_object


def deprecated(
    message: Optional[str] = None, superseded_by: Optional[str] = None
):
    def decorator(command):
        @wraps(command)
        def wrapper(*args: Any, **kwargs: Dict[str, Any]):
            warning: str = (
                "[WARNING] The `{command}` command is deprecated "
                "and will be eventually removed".format(
                    command=inspect_object(command).command.name
                )
            )
            cprint(warning, "yellow")
            if message is not None:
                cprint(message, "yellow")
            elif superseded_by is not None:
                cprint(
                    "Use `{}` command instead".format(superseded_by), "yellow"
                )
            else:
                assert False, "Unreachable"
            return command(*args, **kwargs)

        wrapper.__doc__ = "[DEPRECATED]" + command.__doc__
        return wrapper

    if not ((message is None) ^ (superseded_by is None)):
        raise ValueError("Either `message` or `superseded_by` should be used")

    return decorator
