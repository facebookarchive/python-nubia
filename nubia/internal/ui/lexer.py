#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import re
from pygments.lexer import RegexLexer, bygroups
from pygments.token import (
    Punctuation,
    Text,
    Operator,
    Keyword,
    Name,
    String,
    Number,
)
from nubia import context
from nubia.internal import parser


_identifier = r"[a-zA-Z_][a-zA-Z0-9_\-]*"
_unquoted_string = "([a-zA-Z0-9{}]+)".format(
    re.escape(parser.allowed_symbols_in_string)
)

_command = r"(:?[a-zA-Z_][a-zA-Z0-9_\-]*)"


def command_callback(lexer, match):
    """
    When matching a command, the lexer would look up the command registry to
    decide on how to highlight the command. We will emit Name.Command if this is
    a valid command, otherwise we emit Text. We also take care of the
    sub-commands if this is a super command. Otherwise, we consider the second
    argument a positional argument in this case.
    """
    command = match.group(1)
    # We do need to know whether we are parsing two groups (command) or four
    # (command with subcommand)
    command_with_argument = len(match.groups()) > 2
    ctx = context.get_context()
    cmd = ctx.registry.find_command(command.strip())
    # We know this command
    command_token = Name.InvalidCommand
    subcommand_token = Name.InvalidCommand
    if cmd:
        command_token = Name.Command
        # Now, let's see if this is a super command or not.
        if command_with_argument:
            if cmd.super_command:
                # That's a sub-command, is this a valid sub-command?
                subcmd = match.group(3)
                if cmd.has_subcommand(subcmd):
                    subcommand_token = Name.SubCommand
            else:
                # Just a positional
                subcommand_token = Name.Symbol

    yield (match.start(1), command_token, command)
    # matches the spaces
    yield (match.start(2), Text, match.group(2))
    if command_with_argument:
        yield (match.start(3), subcommand_token, match.group(3))
        # matches the spaces
        yield (match.start(4), Text, match.group(4))


class NubiaLexer(RegexLexer):
    name = "Nubia Interactive Lexer"
    filenames = ["*.nubia"]
    flags = re.IGNORECASE
    tokens = {
        str("root"): [
            # We want to change the state of the lexer if the first word is
            # select so that we can have the sql lexer
            (r"^SELECT\s", Name.Command, str("query")),
            (r"\s+", Text),
            (r"^(\?|help)\s*$", Name.Help),
            (r"^(q|quit|exit)\s*$", Name.Exit),
            # Command with Subcommands
            (r"(" + _identifier + ")(\s*=\s*)", bygroups(Name.Key, Operator)),
            # Commands
            (r"^" + _command + "(\s+)" + _command + "(\s+)", command_callback),
            (r"^" + _command + "(\s+|$)", command_callback),
            (r"(" + _identifier + ")(\s*)", Name.Symbol),
            (r"(True|False|true|false)", Keyword),
            (r"\-?[0-9]+", Number.Integer),
            (r"'(''|[^'])*'", String.Single),
            # not a real string literal in ANSI SQL
            (r'"(""|[^"])*"', String.Symbol),
            (r"[;:()\[\],\.]", Punctuation),
        ],
        str("query"): [
            (r"\s+", Text),
            (
                r"(ABORT|ABS|ABSOLUTE|ACCESS|ADA|ADD|ADMIN|AFTER|AGGREGATE|"
                r"ALIAS|ALL|ALLOCATE|ALTER|ANALYSE|ANALYZE|AND|ANY|ARE|AS|"
                r"ASC|ASENSITIVE|ASSERTION|ASSIGNMENT|ASYMMETRIC|AT|ATOMIC|"
                r"AUTHORIZATION|AVG|BACKWARD|BEFORE|BEGIN|BETWEEN|BITVAR|"
                r"BIT_LENGTH|BOTH|BREADTH|BY|C|CACHE|CALL|CALLED|CARDINALITY|"
                r"CASCADE|CASCADED|CASE|CAST|CATALOG|CATALOG_NAME|CHAIN|"
                r"CHARACTERISTICS|CHARACTER_LENGTH|CHARACTER_SET_CATALOG|"
                r"CHARACTER_SET_NAME|CHARACTER_SET_SCHEMA|CHAR_LENGTH|CHECK|"
                r"CHECKED|CHECKPOINT|CLASS|CLASS_ORIGIN|CLOB|CLOSE|CLUSTER|"
                r"COALSECE|COBOL|COLLATE|COLLATION|COLLATION_CATALOG|"
                r"COLLATION_NAME|COLLATION_SCHEMA|COLUMN|COLUMN_NAME|"
                r"COMMAND_FUNCTION|COMMAND_FUNCTION_CODE|COMMENT|COMMIT|"
                r"COMMITTED|COMPLETION|CONDITION_NUMBER|CONNECT|CONNECTION|"
                r"CONNECTION_NAME|CONSTRAINT|CONSTRAINTS|CONSTRAINT_CATALOG|"
                r"CONSTRAINT_NAME|CONSTRAINT_SCHEMA|CONSTRUCTOR|CONTAINS|"
                r"CONTINUE|CONVERSION|CONVERT|COPY|CORRESPONTING|COUNT|"
                r"CREATE|CREATEDB|CREATEUSER|CROSS|CUBE|CURRENT|CURRENT_DATE|"
                r"CURRENT_PATH|CURRENT_ROLE|CURRENT_TIME|CURRENT_TIMESTAMP|"
                r"CURRENT_USER|CURSOR|CURSOR_NAME|CYCLE|DATA|DATABASE|"
                r"DATETIME_INTERVAL_CODE|DATETIME_INTERVAL_PRECISION|DAY|"
                r"DEALLOCATE|DECLARE|DEFAULT|DEFAULTS|DEFERRABLE|DEFERRED|"
                r"DEFINED|DEFINER|DELETE|DELIMITER|DELIMITERS|DEREF|DESC|"
                r"DESCRIBE|DESCRIPTOR|DESTROY|DESTRUCTOR|DETERMINISTIC|"
                r"DIAGNOSTICS|DICTIONARY|DISCONNECT|DISPATCH|DISTINCT|DO|"
                r"DOMAIN|DROP|DYNAMIC|DYNAMIC_FUNCTION|DYNAMIC_FUNCTION_CODE|"
                r"EACH|ELSE|ENCODING|ENCRYPTED|END|END-EXEC|EQUALS|ESCAPE|EVERY|"
                r"EXCEPT|ESCEPTION|EXCLUDING|EXCLUSIVE|EXEC|EXECUTE|EXISTING|"
                r"EXISTS|EXPLAIN|EXTERNAL|EXTRACT|FALSE|FETCH|FINAL|FIRST|FOR|"
                r"FORCE|FOREIGN|FORTRAN|FORWARD|FOUND|FREE|FREEZE|FROM|FULL|"
                r"FUNCTION|G|GENERAL|GENERATED|GET|GLOBAL|GO|GOTO|GRANT|GRANTED|"
                r"GROUP|GROUPING|HANDLER|HAVING|HIERARCHY|HOLD|HOST|IDENTITY|"
                r"IGNORE|ILIKE|IMMEDIATE|IMMUTABLE|IMPLEMENTATION|IMPLICIT|IN|"
                r"INCLUDING|INCREMENT|INDEX|INDITCATOR|INFIX|INHERITS|INITIALIZE|"
                r"INITIALLY|INNER|INOUT|INPUT|INSENSITIVE|INSERT|INSTANTIABLE|"
                r"INSTEAD|INTERSECT|INTO|INVOKER|IS|ISNULL|ISOLATION|ITERATE|JOIN|"
                r"KEY|KEY_MEMBER|KEY_TYPE|LANCOMPILER|LANGUAGE|LARGE|LAST|"
                r"LATERAL|LEADING|LEFT|LENGTH|LESS|LEVEL|LIKE|LIMIT|LISTEN|LOAD|"
                r"LOCAL|LOCALTIME|LOCALTIMESTAMP|LOCATION|LOCATOR|LOCK|LOWER|"
                r"MAP|MATCH|MAX|MAXVALUE|MESSAGE_LENGTH|MESSAGE_OCTET_LENGTH|"
                r"MESSAGE_TEXT|METHOD|MIN|MINUTE|MINVALUE|MOD|MODE|MODIFIES|"
                r"MODIFY|MONTH|MORE|MOVE|MUMPS|NAMES|NATIONAL|NATURAL|NCHAR|"
                r"NCLOB|NEW|NEXT|NO|NOCREATEDB|NOCREATEUSER|NONE|NOT|NOTHING|"
                r"NOTIFY|NOTNULL|NULL|NULLABLE|NULLIF|OBJECT|OCTET_LENGTH|OF|OFF|"
                r"OFFSET|OIDS|OLD|ON|ONLY|OPEN|OPERATION|OPERATOR|OPTION|OPTIONS|"
                r"OR|ORDER|ORDINALITY|OUT|OUTER|OUTPUT|OVERLAPS|OVERLAY|OVERRIDING|"
                r"OWNER|PAD|PARAMETER|PARAMETERS|PARAMETER_MODE|PARAMATER_NAME|"
                r"PARAMATER_ORDINAL_POSITION|PARAMETER_SPECIFIC_CATALOG|"
                r"PARAMETER_SPECIFIC_NAME|PARAMATER_SPECIFIC_SCHEMA|PARTIAL|"
                r"PASCAL|PENDANT|PLACING|PLI|POSITION|POSTFIX|PRECISION|PREFIX|"
                r"PREORDER|PREPARE|PRESERVE|PRIMARY|PRIOR|PRIVILEGES|PROCEDURAL|"
                r"PROCEDURE|PUBLIC|READ|READS|RECHECK|RECURSIVE|REF|REFERENCES|"
                r"REFERENCING|REINDEX|RELATIVE|RENAME|REPEATABLE|REPLACE|RESET|"
                r"RESTART|RESTRICT|RESULT|RETURN|RETURNED_LENGTH|"
                r"RETURNED_OCTET_LENGTH|RETURNED_SQLSTATE|RETURNS|REVOKE|RIGHT|"
                r"ROLE|ROLLBACK|ROLLUP|ROUTINE|ROUTINE_CATALOG|ROUTINE_NAME|"
                r"ROUTINE_SCHEMA|ROW|ROWS|ROW_COUNT|RULE|SAVE_POINT|SCALE|SCHEMA|"
                r"SCHEMA_NAME|SCOPE|SCROLL|SEARCH|SECOND|SECURITY|SELECT|SELF|"
                r"SENSITIVE|SERIALIZABLE|SERVER_NAME|SESSION|SESSION_USER|SET|"
                r"SETOF|SETS|SHARE|SHOW|SIMILAR|SIMPLE|SIZE|SOME|SOURCE|SPACE|"
                r"SPECIFIC|SPECIFICTYPE|SPECIFIC_NAME|SQL|SQLCODE|SQLERROR|"
                r"SQLEXCEPTION|SQLSTATE|SQLWARNINIG|STABLE|START|STATE|STATEMENT|"
                r"STATIC|STATISTICS|STDIN|STDOUT|STORAGE|STRICT|STRUCTURE|STYPE|"
                r"SUBCLASS_ORIGIN|SUBLIST|SUBSTRING|SUM|SYMMETRIC|SYSID|SYSTEM|"
                r"SYSTEM_USER|TABLE|TABLE_NAME| TEMP|TEMPLATE|TEMPORARY|TERMINATE|"
                r"THAN|THEN|TIMESTAMP|TIMEZONE_HOUR|TIMEZONE_MINUTE|TO|TOAST|"
                r"TRAILING|TRANSATION|TRANSACTIONS_COMMITTED|"
                r"TRANSACTIONS_ROLLED_BACK|TRANSATION_ACTIVE|TRANSFORM|"
                r"TRANSFORMS|TRANSLATE|TRANSLATION|TREAT|TRIGGER|TRIGGER_CATALOG|"
                r"TRIGGER_NAME|TRIGGER_SCHEMA|TRIM|TRUE|TRUNCATE|TRUSTED|TYPE|"
                r"UNCOMMITTED|UNDER|UNENCRYPTED|UNION|UNIQUE|UNKNOWN|UNLISTEN|"
                r"UNNAMED|UNNEST|UNTIL|UPDATE|UPPER|USAGE|USER|"
                r"USER_DEFINED_TYPE_CATALOG|USER_DEFINED_TYPE_NAME|"
                r"USER_DEFINED_TYPE_SCHEMA|USING|VACUUM|VALID|VALIDATOR|VALUES|"
                r"VARIABLE|VERBOSE|VERSION|VIEW|VOLATILE|WHEN|WHENEVER|WHERE|"
                r"WITH|WITHOUT|WORK|WRITE|YEAR|ZONE)\b",
                Keyword,
            ),
            (
                r"(ARRAY|BIGINT|BINARY|BIT|BLOB|BOOLEAN|CHAR|CHARACTER|DATE|"
                r"DEC|DECIMAL|FLOAT|INT|INTEGER|INTERVAL|NUMBER|NUMERIC|REAL|"
                r"SERIAL|SMALLINT|VARCHAR|VARYING|INT8|SERIAL8|TEXT)\b",
                Name.Builtin,
            ),
            (r"[+*/<>=~!@#%^&|`?-]", Operator),
            (r"[0-9]+", Number.Integer),
            (r"'(''|[^'])*'", String.Single),
            # not a real string literal in ANSI SQL
            (r'"(""|[^"])*"', String.Symbol),
            (r"[a-zA-Z_][a-zA-Z0-9_]*", Name),
            (r"[;:()\[\],\.]", Punctuation),
        ],
    }
