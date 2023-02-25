# Configuration file for the Sphinx documentation builder.

# -- Project information

project = "flexdi"
copyright = "2023, Cal Pratt"
author = "Cal Pratt"

version = "0.1.8"

# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

# -- Options for HTML output

html_theme = "sphinx_rtd_theme"

html_theme_options = {
    'collapse_navigation': False,
    'navigation_depth': -1,
    'prev_next_buttons_location': 'both',
}

# -- Options for EPUB output
epub_show_urls = "footnote"
