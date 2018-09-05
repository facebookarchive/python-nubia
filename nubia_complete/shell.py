#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import sys
import string
import re

regex = re.compile("[{}]".format(re.escape(string.punctuation)))


def generate_shell_setup(command_name, command_model):
    clean_command_name = regex.sub("_", command_name)
    func_name = "_nubia_completer_{}".format(clean_command_name)

    template = """
if [[ -n ${{ZSH_VERSION-}} ]]; then
  # zsh setup
  _zsh_{func_name}() {{
    local nubia_completer=${{NUBIA_COMPLETER_BINARY:-"{completer}"}}
    local log_level=${{NUBIA_COMPLETER_LOG_LEVEL:-"INFO"}}
    local log_file=${{NUBIA_COMPLETER_LOG_FILE:-"/dev/null"}}
    local word completions
    local IFS=$'\\n'
    read -l;
    local cl="$REPLY";
    read -ln;
    local cp="$REPLY";
    reply=(`COMP_SHELL="zsh" \\
            COMP_LINE="$cl" \\
            COMP_POINT="$cp" \\
      $nubia_completer --loglevel ${{log_level}} complete \\
      --command-model-path="{model}" \\
      2>> "$log_file"`)

  }}

  compctl -Q -S '' -K _zsh_{func_name} "{command}"

else
  # bash setup
  _bash_{func_name}() {{
    local nubia_completer=${{NUBIA_COMPLETER_BINARY:-"{completer}"}}
    local log_level=${{NUBIA_COMPLETER_LOG_LEVEL:-"INFO"}}
    local log_file=${{NUBIA_COMPLETER_LOG_FILE:-"/dev/null"}}
    COMPREPLY=()
    local word="$2"
    local IFS=$'\\n'
    local completions="$(COMP_LINE="$COMP_LINE" \\
      COMP_WORDS="${{COMP_WORDS[1]}}" \\
      COMP_POINT="$COMP_POINT" \\
      COMP_TYPE="$COMP_TYPE" \\
      COMP_WORDBREAKS="$COMP_WORDBREAKS" \\
      $nubia_completer --loglevel "${{log_level}}" complete \\
      --command-model-path="{model}" \\
      2>> "$log_file")"
    COMPREPLY=( $(compgen -W "$completions" -- "$word") )
    return 0
  }}

  complete -o nospace -F _bash_{func_name} "{command}"
fi
    """
    print(
        template.format(
            func_name=func_name,
            command=command_name,
            completer=sys.argv[0],
            model=command_model,
        )
    )
