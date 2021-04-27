"""Sphinx configuration file for an LSST stack package.

This configuration only affects single-package Sphinx documentation builds.
"""

from documenteer.sphinxconfig.stackconf import build_package_configs
import lsst.daf.butler_smig


_g = globals()
_g.update(build_package_configs(
    project_name='daf_butler_smig',
    version=lsst.daf.butler_smig.version.__version__))
