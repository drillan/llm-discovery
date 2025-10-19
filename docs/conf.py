# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "llm-discovery"
copyright = "2025, driller"
author = "driller"

# Dynamic version retrieval
try:
    release = get_version("llm-discovery")
    version = ".".join(release.split(".")[:2])  # Major.Minor
except PackageNotFoundError:
    # Fallback for development/documentation build without package installation
    release = "0.1.0"
    version = "0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx_rtd_theme",
]

# MyST Parser extensions
myst_enable_extensions = [
    "colon_fence",      # ::: directives (Admonitions)
    "deflist",          # Definition lists
    "tasklist",         # Task lists
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Read the Docs theme options
html_theme_options = {
    "navigation_depth": 3,
    "collapse_navigation": False,
}
