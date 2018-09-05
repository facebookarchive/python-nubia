#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import logging
import threading
from termcolor import colored


class ContextFilter(logging.Filter):
    def filter(self, record):
        # colorize the level
        level = record.levelname.lower().rjust(7)
        if record.levelno <= logging.DEBUG:
            level = colored(level, "blue")
        elif record.levelno >= logging.ERROR:
            level = colored(level, "red")
        elif record.levelno >= logging.WARNING:
            level = colored(level, "yellow")
        record.level = level

        # logger name
        if record.name == "__main__":
            logger_name = "main"
        else:
            logger_name = record.name.split(".")[-1]
        record.logger_name = logger_name

        # thread name (optional)
        record.thread = ""
        if record.levelno <= logging.DEBUG:
            thread = threading.current_thread().getName()
            if thread != "MainThread":
                record.thread = "thread {}: ".format(thread)

        return True


def get_formatter():
    return logging.Formatter(
        fmt="[%(asctime)-15s] [%(level)6s] [%(logger_name)s] "
        "%(thread)s%(message)s"
    )


def setup_logger(level, stream):
    log_handler = logging.StreamHandler(stream)
    log_handler.setFormatter(get_formatter())
    log_handler.addFilter(ContextFilter())
    logging.root.addHandler(log_handler)

    logging.root.setLevel(level)
