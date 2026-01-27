HERP Python Client Documentation
==================================

Production-ready Python client for `HERP Hire API <https://herp.cloud>`_ with advanced features including caching, rate limiting, circuit breakers, and Notion integration.

.. image:: https://img.shields.io/pypi/v/herp-python-client.svg
   :target: https://pypi.org/project/herp-python-client/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/herp-python-client.svg
   :target: https://pypi.org/project/herp-python-client/
   :alt: Python versions

.. image:: https://img.shields.io/github/license/lalarsson87/herp-python-client.svg
   :target: https://github.com/lalarsson87/herp-python-client/blob/main/LICENSE
   :alt: License

Features
--------

* **Full HERP API Coverage**: Candidacies, contacts, evaluations, files, timeline, master data
* **Fluent Builder Patterns**: Readable, chainable interfaces for constructing requests
* **Query DSL**: Type-safe query builder for complex searches
* **Advanced Caching**: Thread-safe in-memory cache with TTL and LRU eviction
* **Rate Limiting**: Adaptive token bucket rate limiter with automatic backoff
* **Circuit Breakers**: Fault tolerance with automatic recovery
* **Retry Logic**: Smart exponential backoff for transient failures
* **Structured Logging**: Machine-parseable logs with structlog
* **Type Safety**: Complete TypedDict schemas for static type checking
* **Notion Integration**: Bi-directional sync with Notion databases

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install herp-python-client

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from src.core.herp.client import HerpClient

   # Initialize client
   client = HerpClient(api_key="your_api_key")

   # List candidacies
   candidacies = client.candidacies.list(limit=10)

   # Get specific candidacy
   candidacy = client.candidacies.get("cand_123")

   # Use builder pattern
   from src.core.herp.builders import CandidacyBuilder

   candidacy = client.candidacies.create(
       CandidacyBuilder()
       .with_name("Jane Doe")
       .with_email("jane@example.com")
       .for_requisition("req_001")
       .build()
   )

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   quickstart
   installation
   configuration

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   guides/client
   guides/builders
   guides/query_dsl
   guides/caching
   guides/error_handling
   guides/rate_limiting
   guides/structured_logging

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/client
   api/builders
   api/query_dsl
   api/schemas
   api/exceptions
   api/cache
   api/circuit_breaker

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/basic_usage
   examples/advanced_queries
   examples/batch_operations
   examples/notion_sync

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   testing
   changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
