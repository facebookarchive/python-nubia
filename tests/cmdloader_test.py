#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import unittest

from nubia.internal import cmdloader

from tests import sample_package
from tests import empty_package


class CommandLoaderTest(unittest.TestCase):
    def test_load_no_packages(self):
        self.assertEquals([], list(cmdloader.load_commands(None)))

    def test_load_empty_packages(self):
        self.assertEquals([], list(cmdloader.load_commands(empty_package)))

    def test_load_sample_packages(self):
        loaded = list(cmdloader.load_commands(sample_package))
        self.assertEquals(3, len(loaded))
        from tests.sample_package import commands
        from tests.sample_package.subpackage import more_commands

        self.assertTrue(commands.example_command1 in loaded)
        self.assertTrue(more_commands.example_command2 in loaded)
        self.assertTrue(more_commands.SuperCommand in loaded)
