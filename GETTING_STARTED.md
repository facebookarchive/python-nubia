# Getting Started

## Basic concepts
The building blocks of a simple Nubia-based application are three pieces:

* [Nubia plugin](###Plugin)
* Application [context](###Context)
* [Commands](###Commands) and their [arguments](###Arguments)


### Plugin
A Nubia plugin is an object that implements `nubia.PluginInterface`.
It gives you the ability to configure the behaviour of different aspects of your program.
Take a look into `example/nubia_plugin.py` to see an example of a very simple Nubia plugin.
The table below gives a short overiew of `nubia.PluginInterface`' most important methods.

| Method | Responsibility |
| --- | --- |
| `get_commands` | Provides the list of commands exposed via Nubia |
| `get_opts_parser` | Provides the top-level argument parser that handles common arguments |
| `create_context` | Provides a context object |
| `get_status_bar` | Provides a status bar |
| `get_prompt_tokens` | Provides prompt tokens for interactive prompt |

### Context
A _context_ is an object that extends `nubia.Context` class.
It’s a singleton object that holds state and configuration for your program and can be easily accessed from your code.

```python
from nubia import context

ctx = context.get_context()
```

The context should be the only place you store your shared state and configuration into.
For more details about context and how to use it, please read context documentation. <TODO context>

### Commands
Any Python function can be exposed as a Nubia command by applying `@command` decorator on top of it.

``` python
from nubia import command

@command
def foo_bar() -> int:  # becomes a `foo-bar` command
    return 42
```

By default, Nubia automatically generates a command name from the corresponding function name.
Nubia translates both `snake_case` or `CamelCase` names into `kebab-case` names (see the examples below).
However, it's possible to override this behaviour by explicitly supplying the command name.
<TODO aliases>

``` python
from nubia import command

@command("moo")
def foo_bar() -> int:  # becomes a `moo` command
    return 42
```


#### Subcommands
When building complex CLI interfaces (e.g. similar to `git`), one may need to group the commands according to their purpose.

Nubia supports this by allowing Python classes to act as super commands.
Applying the `@command` decorator to the class itself indicates that:

* It denotes a super command
* Its public instance methods are automatically treated as subcommands

``` python
from nubia import command

@command
class Daemon:
    """
    This is a set of commands that run daemons
    """
    @command
    def start(self) -> None:  # becomes a `daemon start` subcommand
        "Help message of start"
        # Starting the daemon
        ...

    @command
    def stop(self) -> None:  # becomes a `daemon stop` subcommand
        "Help message of stop"
        # Stopping the daemon
        ...
```

Furthermore, the `__init__` arguments are options that will be available for
both sub-commands, each sub-command can have its own additional options by
defining these are arguments to their respective functions.

### Arguments
Function (or method) arguments are converted into command options automatically.
You can use the `@argument` decorator to add more metadata to the generated
command option if you like. But before we get to that, let's talk about some
rules first:
- Function arguments that have default values are _optional_. If the command is
executed without supplying a value, you will receive this default value as
defined in the function signature.
- Function arguments that do not have default values are required.
- All arguments are _options_ by default, this means that you need to pass
`--argument-name` when running the command (in CLI mode). If you would like to
have the argument supplied as a positional value, you need to set
`positional=True` in the `@argument` decorator as indicated in this example
- `description` parameter of `@argument` decorator is mandatory.

```python
import typing

@command
@argument("hostnames", description="Hostname for the server you want to start",
    positional=True)
def start_server(hostnames: typing.List[str]):
    """
    Starts a server or more
    """
    pass
```

Since `hostnames` is defined as a `typing.List`, we expect the user to pass
multiple values. A single value will automatically be lifted into a list of
a single value `(x -> [x])`. Lists in CLI mode are space-separated values

```
my-program start-server server.com server2.com
```

In interactive, you can do any of the following:

```
my-program start-server server1.com
my-program start-server [server1.com, server2.com]
my-program start-server ["server1.com", "server2.com"]
my-program start-server hostnames=["server1.com", "server2.com"]
```
