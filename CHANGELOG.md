# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2021-12-01

### Added
- `Nubia.run_async` added, the original `run` is a wrapper around it that creates an event loop.

### Changed
- The following functions were made async and might need to be updated in your context you want to upgrade. Internally Nubia checks if they're updated to be async, but if you're using them in your own code, then you'll need to update them.
    - `Context`
        - `on_connected`
        - `on_interactive`
        - `on_cli`
    - `Listener` and subclasses `Command` and `StatusBar`
        - `on_connected`
        - `react`
        - `Command`
            - `run_interactive`
            - `run_cli`
            - `add_arguments`
    - `CommandsRegistry`
        - `register_command`
        - `dispatch_message`
- Poetry was introduced with locked dependencies. This may introduce some conflicts in your dependencies.
