"""Sphinx configuration."""
project = "Grapheme to Phoneme - Greek"
author = "Georgios K."
copyright = "2019, Georgios K."
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
