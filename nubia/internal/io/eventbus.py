#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import logging
import traceback

logger = logging.getLogger(__name__)


class Message:
    CONNECTED = 1


class Listener:
    def react(self, msg, *args, **kwargs):
        if msg == Message.CONNECTED:
            try:
                self.on_connected(*args, **kwargs)
            except NotImplementedError:
                raise
            except Exception as e:
                logger.info(
                    "Couldn't initialize {}: " "{}".format(type(self), e)
                )
                traceback.print_exc()

    def on_connected(*args, **kwargs):
        raise NotImplementedError(
            "Listeners must implement on_connected method"
        )
