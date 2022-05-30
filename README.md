# python-nubia

This project has been archived, the README below is kept for archiving purposes. See [#88](https://github.com/facebookincubator/python-nubia/issues/88) for more information.

---

[![Support Ukraine](https://img.shields.io/badge/Support-Ukraine-FFD500?style=flat&labelColor=005BBB)](https://opensource.fb.com/support-ukraine)
![Nubia Build](https://github.com/facebookincubator/python-nubia/workflows/Nubia%20Build/badge.svg)
[![Coverage](https://codecov.io/gh/facebookincubator/python-nubia/branch/main/graph/badge.svg)](https://codecov.io/github/facebookincubator/python-nubia)
[![PyPI version](https://badge.fury.io/py/python-nubia.svg)](https://badge.fury.io/py/python-nubia)

Nubia is a lightweight framework for building command-line applications with Python. It was originally designed for the “logdevice interactive shell (aka. `ldshell`)” at Facebook. Since then it was factored out to be a reusable component and several internal Facebook projects now rely on it as a quick and easy way to get an intuitive shell/cli application without too much boilerplate.

Nubia is built on top of [python-prompt-toolkit](https://github.com/jonathanslenders/python-prompt-toolkit) which is a fantastic toolkit for building interactive command-line applications.

_Disclaimer: Nubia is beta for non-ldshell use-cases. Some of the design decisions might sound odd but they fit the ldshell usecase perfectly. We are continuously making changes to make it more consistent and generic outside of the ldshell use-case. Until a fully stable release is published, use it on your own risk._

See the [CONTRIBUTING](CONTRIBUTING.md) file for how to help out.

If you are curious on the origins of the name, checkout [Nubia on Wikipedia](https://en.wikipedia.org/wiki/Nubia) with its unique and colourful architecture.

## Key Features

* Interactive mode that offers fish-style auto-completion
* CLI mode that gets generated from your functions and classes.
* Optional bash/zsh completions via an external utility ‘nubia-complete’ (experimental)
* A customisable status-bar in interactive mode.
* An optional IPython-based interactive shell
* Arguments with underscores are automatically hyphenated
* Python3 type annotations are used for input type validation

### Interactive mode
The interactive mode in Nubia is what makes it unique. It is very easy to build a unique shell for your program with zero overhead. The interactive shell in its simplistic form offers automatic completions for commands, sub-commands, arguments, and values. It also offers a great deal of control for developers to take control over  auto-completions, even for commands that do not fall under the typical format. An example is the “select” command in ldshell which is expressed as a SQL-query. We expect that most use cases of Nubia will not need such control and the AutoCommand will be enough without further customisation.

If you start a nubia-based program without a command, it automatically starts an interactive shell. The interactive mode looks like this:

![Interactive Demo](docs/interactive.gif?raw=true "Interactive demo")

### Non-interactive mode
The CLI mode works exactly like any traditional unix-based command line utility.
![Non-interactive Demo](docs/non_interactive.png?raw=true "Non-interactive demo")

Have your `@command` decorated function return an `int` to send that value as the Unix return code for your non interactive CLI.

## Examples
It starts with a function like this:
```py
import socket
import typing

from termcolor import cprint
from nubia import argument, command, context

@command
@argument("hosts", description="Hostnames to resolve", aliases=["i"])
@argument("bad_name", name="nice", description="testing")
async def lookup(hosts: typing.List[str], bad_name: int) -> int:
    """
    This will lookup the hostnames and print the corresponding IP addresses
    """
    ctx = context.get_context()

    if not hosts:
        cprint("No hosts supplied via --hosts")
        return 1

    print(f"hosts: {hosts}")
    cprint(f"Verbose? {ctx.verbose}")

    for host in hosts:
        cprint(f"{host} is {socket.gethostbyname(host)}")

    return 0
```

## Requirements

Nubia-based applications require Python 3.7+ and works with both Mac OS X or Linux. While in theory it should work on Windows, it has never been tried.

## Installing Nubia

If you are installing nubia for your next project, you should be able to easily use pip for that:
```bash
pip install python-nubia
```

## Building Nubia from source

```bash
poetry build
```

## Running example in virtualenv:

_We recommend setting up a separate Python environment using a tool like virtualenv, pyenv-virtualenv, or `poetry shell`._


If you would like to run the example, install the dependencies and run the example module as a script.

```bash
poetry install
cd example
python -m nubia_example
```

To run the unit tests:

```bash
poetry run nosetests
```

## Getting Started

See the [getting started](GETTING_STARTED.md) guide to learn how to build a simple application with Nubia.

## License
python-nubia is BSD licensed, as found in the LICENSE file.
