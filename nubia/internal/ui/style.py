#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

from prompt_toolkit.styles import (
    merge_styles,
    style_from_pygments_cls,
    style_from_pygments_dict,
)
from prompt_toolkit.styles import Style
from pygments.styles.monokai import MonokaiStyle
from pygments.token import Token, Name


shell_style = merge_styles(
    [
        style_from_pygments_cls(MonokaiStyle),
        style_from_pygments_dict(
            {
                # Commands
                Name.Command: "#f2b44f",
                Name.SubCommand: "#f2c46f",
                Name.InvalidCommand: "bg:#ff0066 #000000",
                Name.Select: "#0000ff",
                Name.Query: "#d78700",
                Name.Key: "#ffffff",
                Name.Path: "#fff484",
                Name.Help: "#00aa00",
                Name.Exit: "#ff0066",
                # User input.
                Token: "#ff0066",
                # Prompt.
                Token.Username: "#884444",
                Token.At: "#00aa00",
                Token.Colon: "#00aa00",
                Token.Pound: "#00aa00",
                Token.Tier: "#ff0088",
                Token.Path: "#884444 underline",
                Token.RPrompt: "bg:#ff0066 #ffffff",
                # Toolbar Tokens
                Token.Toolbar: "#ffffff bg:#1c1c1c",
                Token.TestTier: "#ff0000 bg:#1c1c1c",
                Token.ProductionTier: "#ff0000 bg:#1c1c1c",
                Token.OfflineNodes: "#ff0000 bg:#1c1c1c",
                Token.NodesCount: "#ffffff bg:#1c1c1c",
                Token.Spacer: "#ffffff bg:#1c1c1c",
                # Alarms
                Token.MinorAlarm: "#0000ff bg:#1c1c1c",
                Token.MajorAlarm: "#d78700 bg:#1c1c1c",
                Token.CriticalAlarm: "#ff0000 bg:#1c1c1c",
                Token.AppendFailures: "#0000ff bg:#1c1c1c",
                # General
                Token.Good: "#ffffff bg:#10c010",
                Token.Bad: "#ffffff bg:#c01010",
                Token.Info: "#ffffff bg:#1010c0",
                Token.Warn: "#000000 bg:#c0c010",
            }
        ),
        Style.from_dict({"bottom-toolbar": "fg:#ffffff bg:#1c1c1c noinherit"}),
    ]
)
