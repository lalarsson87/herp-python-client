Installation
============

Requirements
------------

* Python 3.10 or higher
* pip package manager

From PyPI
---------

Install the latest stable release:

.. code-block:: bash

   pip install herp-python-client

This installs the core package with all required dependencies.

Development Installation
------------------------

For development, install with dev dependencies:

.. code-block:: bash

   pip install "herp-python-client[dev]"

Or install from source:

.. code-block:: bash

   git clone https://github.com/lalarsson87/herp-python-client.git
   cd herp-python-client
   pip install -e ".[dev]"

Dependencies
------------

Core Dependencies
~~~~~~~~~~~~~~~~~

* ``requests>=2.31.0`` - HTTP client
* ``python-dotenv>=1.0.0`` - Environment variable management
* ``structlog>=24.1.0`` - Structured logging
* ``pydantic>=2.5.0`` - Data validation

Development Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

* ``pytest>=7.4.0`` - Testing framework
* ``pytest-cov>=4.1.0`` - Code coverage
* ``pytest-vcr>=1.0.2`` - Integration test recording
* ``black>=24.1.1`` - Code formatting
* ``isort>=5.13.2`` - Import sorting
* ``flake8>=7.0.0`` - Linting
* ``mypy>=1.8.0`` - Static type checking
* ``bandit>=1.7.6`` - Security scanning
* ``pre-commit>=3.6.0`` - Pre-commit hooks

Verify Installation
-------------------

Verify the installation:

.. code-block:: python

   import src.core.herp.client
   print(src.core.herp.client.__version__)

Or run the tests:

.. code-block:: bash

   pytest tests/

Upgrading
---------

Upgrade to the latest version:

.. code-block:: bash

   pip install --upgrade herp-python-client

Uninstalling
------------

.. code-block:: bash

   pip uninstall herp-python-client
