# HERP Python Client Documentation

Sphinx-based documentation for the HERP Python Client.

## Building Documentation

### Install Dependencies

```bash
pip install ".[docs]"
```

### Build HTML Documentation

```bash
cd docs
make html
```

Documentation will be built to `docs/build/html/`.

### View Documentation

Open `docs/build/html/index.html` in your browser:

```bash
open build/html/index.html  # macOS
xdg-open build/html/index.html  # Linux
start build/html/index.html  # Windows
```

### Clean Build

```bash
make clean
make html
```

## Development Server

Install sphinx-autobuild for live reload:

```bash
pip install sphinx-autobuild
sphinx-autobuild source build/html
```

Then open http://localhost:8000 in your browser.

## Documentation Structure

```
docs/
├── Makefile                    # Build commands
├── README.md                   # This file
├── source/
│   ├── conf.py                 # Sphinx configuration
│   ├── index.rst               # Documentation home page
│   ├── quickstart.rst          # Quick start guide
│   ├── installation.rst        # Installation guide
│   ├── configuration.rst       # Configuration guide
│   ├── api/                    # API reference
│   │   ├── client.rst
│   │   ├── builders.rst
│   │   ├── query_dsl.rst
│   │   ├── schemas.rst
│   │   ├── exceptions.rst
│   │   └── cache.rst
│   ├── guides/                 # User guides
│   │   ├── client.rst
│   │   ├── builders.rst
│   │   ├── query_dsl.rst
│   │   ├── caching.rst
│   │   ├── error_handling.rst
│   │   ├── rate_limiting.rst
│   │   └── structured_logging.rst
│   ├── examples/               # Code examples
│   │   ├── basic_usage.rst
│   │   ├── advanced_queries.rst
│   │   ├── batch_operations.rst
│   │   └── notion_sync.rst
│   └── _static/                # Static files (CSS, images)
└── build/                      # Generated documentation (gitignored)
```

## Writing Documentation

### RST Basics

```rst
Section Title
=============

Subsection Title
----------------

Subsubsection Title
~~~~~~~~~~~~~~~~~~~

**Bold text** and *italic text*

``Code inline``

.. code-block:: python

   # Code block
   from src.core.herp.client import HerpClient

   client = HerpClient(api_key="your_api_key")

See: `Link text <https://example.com>`_
```

### Autodoc

Document Python code automatically:

```rst
.. automodule:: src.core.herp.client
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.herp.client.HerpClient
   :members:
   :special-members: __init__
```

### Cross-References

```rst
See :class:`~src.core.herp.client.HerpClient`
See :meth:`~src.core.herp.client.HerpClient.candidacies.list`
See :doc:`quickstart` for getting started
```

## Publishing

### ReadTheDocs

Documentation is automatically built and published to ReadTheDocs:

https://herp-python-client.readthedocs.io/

### GitHub Pages

Or publish to GitHub Pages:

```bash
make html
cp -r build/html/* ../gh-pages/
cd ../gh-pages
git add .
git commit -m "Update documentation"
git push origin gh-pages
```

## Troubleshooting

### "Module not found" errors

Ensure the src directory is in the Python path (configured in conf.py):

```python
sys.path.insert(0, os.path.abspath('../../src'))
```

### Missing dependencies

Install all doc dependencies:

```bash
pip install ".[docs]"
```

### Build warnings

Fix warnings to ensure clean builds:

```bash
make clean
make html
```

## Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
- [ReadTheDocs Tutorial](https://docs.readthedocs.io/en/stable/tutorial/)
