#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

from IPython.terminal.prompts import Prompts, Token
from nubia import context


class CustomPrompt(Prompts):
    def in_prompt_tokens(self, cli=None):
        target = context.get_context().target
        target = target or "disconnected"
        return [
            (Token.Prompt, "["),
            (Token.PromptNum, str(self.shell.execution_count)),
            (Token.Prompt, "] "),
            (Token.Prompt, "("),
            (Token.Text, target),
            (Token.Prompt, "): "),
        ]

    def out_prompt_tokens(self):
        return [
            (Token.OutPrompt, "Out<"),
            (Token.OutPromptNum, str(self.shell.execution_count)),
            (Token.OutPrompt, ">: "),
        ]
