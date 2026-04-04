"""Minimal setup.py shim for editable installs with older pip versions.

All project metadata is in pyproject.toml. This file exists only to support
`pip install -e .` on systems with pip < 23.1 that do not implement PEP 660.
"""

from setuptools import setup

setup()
