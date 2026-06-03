"""
setup.py — custom install command that downloads the xtb binary.

pip install . triggers this after the Python package is installed.
We load binary.py directly by path so we don't depend on ase_gxtb
being importable at build time.
"""

import importlib.util
import sys
from pathlib import Path
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop


def _load_binary_module():
    spec = importlib.util.spec_from_file_location(
        "ase_gxtb.binary",
        Path(__file__).parent / "src" / "ase_gxtb" / "binary.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _install_binary():
    binary = _load_binary_module()
    binary.install_gxtb_binary()


class PostInstall(install):
    def run(self):
        super().run()
        _install_binary()


class PostDevelop(develop):
    def run(self):
        super().run()
        _install_binary()


setup(
    cmdclass={
        "install": PostInstall,
        "develop": PostDevelop,
    },
)
