#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import asyncio
import socket
import typing
from termcolor import cprint
from nubia import command, argument, context


@command(aliases=["lookup"])
@argument("hosts", description="Hostnames to resolve", aliases=["i"])
@argument("bad_name", name="nice", description="testing")
def lookup_hosts(hosts: typing.List[str], bad_name: int):
    """
    This will lookup the hostnames and print the corresponding IP addresses
    """
    ctx = context.get_context()
    cprint("Input: {}".format(hosts), "yellow")
    cprint("Verbose? {}".format(ctx.verbose), "yellow")
    for host in hosts:
        cprint("{} is {}".format(host, socket.gethostbyname(host)))

    # optional, by default it's 0
    return 0


@command("good-name")
def bad_name():
    """
    This command has a bad function name, but we ask Nubia to register a nicer
    name instead
    """
    cprint("Good Name!", "green")


@command
@argument("number", type=int)
async def triple(number):
    "Calculates the triple of the input value"
    cprint("Input is {}".format(number))
    cprint("Type of input is {}".format(type(number)))
    cprint("{} * 3 = {}".format(number, number * 3))
    await asyncio.sleep(2)


@command("be-blocked")
def be_blocked():
    """
    This command is an example of command that blocked in configerator.
    """

    cprint("If you see me, something is wrong, Bzzz", "red")


@command
@argument("style", description="Pick a style", choices=["test", "toast", "toad"])
@argument("stuff", description="more colors", choices=["red", "green", "blue"])
@argument("code", description="Color code", choices=[12, 13, 14])
def pick(style: str, stuff: typing.List[str], code: int):
    """
    A style picking tool
    """
    cprint("Style is '{}' code is {}".format(style, code), "yellow")


# instead of replacing _ we rely on camelcase to - super-command


@command
class SuperCommand:
    "This is a super command"

    def __init__(self, shared: int = 0) -> None:
        self._shared = shared

    @property
    def shared(self) -> int:
        return self._shared

    """This is the super command help"""

    @command
    @argument("firstname", positional=True)
    def print_name(self, firstname: str):
        """
        print a name
        """
        cprint("My name is: {}".format(firstname))

    @command(aliases=["do"])
    def do_stuff(self, stuff: int):
        """
        doing stuff
        """
        cprint("stuff={}, shared={}".format(stuff, self.shared))
