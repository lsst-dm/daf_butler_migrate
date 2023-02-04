"""Sphinx configuration file for an LSST stack package.
This configuration only affects single-package Sphinx documentation builds.
For more information, see:
https://developer.lsst.io/stack/building-single-package-docs.html
"""
# flake8: noqa

from documenteer.conf.pipelinespkg import *

project = "daf_butler_migrate"
html_theme_options["logotext"] = project
html_title = project
html_short_title = project
