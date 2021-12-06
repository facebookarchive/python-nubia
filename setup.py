#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import ast
import re
from os import path
from pathlib import Path

# To use a consistent encoding
import setuptools

here = Path(__file__).parent


with open("requirements.txt", "r") as fd:
    reqs = fd.readlines()
    reqs = [r for r in reqs if not r.strip().startswith("#")]


def get_long_description() -> str:
    with open(path.join(here, "README.md"), "r", encoding="utf-8") as fh:
        return fh.read()


def get_version() -> str:
    nubia_py = here / "nubia/__init__.py"
    _version_re = re.compile(r"__version__\s+=\s+(?P<version>.*)")
    with open(nubia_py, "r", encoding="utf8") as f:
        match = _version_re.search(f.read())
        version = match.group("version") if match is not None else '"unknown"'
    return str(ast.literal_eval(version))


setuptools.setup(
    name="python-nubia",
    version=get_version(),
    author="Ahmed Soliman",
    author_email="asoli@fb.com",
    description="A framework for building beautiful shells",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    keywords="cli shell interactive framework",
    url="https://github.com/facebookincubator/python-nubia",
    packages=setuptools.find_packages(exclude=["sample", "docs", "tests"]),
    python_requires=">=3.7",
    setup_requires=["nose>=1.0", "coverage"],
    tests_require=["nose>=1.0", "later>=20.10"],
    entry_points={"console_scripts": ["_nubia_complete = nubia_complete.main:main"]},
    install_requires=reqs,
    classifiers=(
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Environment :: Console",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ),
)
