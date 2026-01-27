Quick Start Guide
==================

This guide will get you up and running with the HERP Python Client in minutes.

Installation
------------

Install via pip:

.. code-block:: bash

   pip install herp-python-client

Or install from source:

.. code-block:: bash

   git clone https://github.com/lalarsson87/herp-python-client.git
   cd herp-python-client
   pip install -e ".[dev]"

Configuration
-------------

Set your API key as an environment variable:

.. code-block:: bash

   export HERP_API_KEY=your_api_key_here

Or pass it directly when creating the client:

.. code-block:: python

   from src.core.herp.client import HerpClient

   client = HerpClient(api_key="your_api_key")

Basic Operations
----------------

Listing Candidacies
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # List all candidacies
   candidacies = client.candidacies.list()

   # List with filters
   active_candidacies = client.candidacies.list(
       status="active",
       limit=10
   )

   # Iterate through results
   for candidacy in active_candidacies:
       print(f"{candidacy['name']} - {candidacy['status']}")

Getting a Candidacy
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   candidacy = client.candidacies.get("cand_123")

   print(f"Name: {candidacy['name']}")
   print(f"Email: {candidacy.get('email', 'N/A')}")
   print(f"Status: {candidacy['status']}")

Using Builder Patterns
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.core.herp.builders import CandidacyBuilder

   # Build candidacy with fluent API
   candidacy_data = (
       CandidacyBuilder()
       .with_name("Jane Doe")
       .with_email("jane@example.com")
       .with_phone("+81-90-1234-5678")
       .for_requisition("req_001")
       .at_step("interview")
       .with_tags(["backend", "senior"])
       .build()
   )

   # Create candidacy
   new_candidacy = client.candidacies.create(candidacy_data)

Using Query DSL
~~~~~~~~~~~~~~~

.. code-block:: python

   from src.core.herp.query_dsl import CandidacyQuery

   # Build complex query
   query = (
       CandidacyQuery()
       .by_requisition("req_001")
       .active_only()
       .created_after("2026-01-01")
       .has_email()
   )

   # Execute query
   results = client.candidacies.search(query)

Working with Contacts
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.core.herp.builders import ContactBuilder
   from datetime import datetime, timedelta

   # Schedule interview
   interview_time = datetime.now() + timedelta(days=7)

   contact_data = (
       ContactBuilder()
       .of_type("technical_interview")
       .with_title("Senior Backend Engineer Interview")
       .scheduled_for(interview_time)
       .for_duration(60)
       .at_location("https://zoom.us/j/123456789")
       .with_interviewers(["user_001", "user_002"])
       .build()
   )

   contact = client.contacts.create("cand_123", contact_data)

Error Handling
--------------

.. code-block:: python

   from src.core.errors.exceptions import (
       HerpNotFoundError,
       HerpRateLimitError,
       HerpAuthenticationError
   )

   try:
       candidacy = client.candidacies.get("cand_123")
   except HerpNotFoundError:
       print("Candidacy not found")
   except HerpRateLimitError:
       print("Rate limit exceeded, will retry automatically")
   except HerpAuthenticationError:
       print("Invalid API key")

Caching
-------

Enable automatic caching:

.. code-block:: python

   client = HerpClient(
       api_key="your_api_key",
       enable_cache=True,
       cache_ttl=300  # 5 minutes
   )

   # First call hits API
   candidacy = client.candidacies.get("cand_123")

   # Second call uses cache
   candidacy = client.candidacies.get("cand_123")  # Fast!

   # Clear cache
   client.cache.clear()

Rate Limiting
-------------

Rate limiting is automatic:

.. code-block:: python

   # Client automatically respects rate limits
   client = HerpClient(
       api_key="your_api_key",
       requests_per_minute=100
   )

   # Make many requests - automatically throttled
   for i in range(200):
       candidacy = client.candidacies.get(f"cand_{i}")
       # Automatically adds delays to stay under limit

Structured Logging
------------------

Configure structured logging:

.. code-block:: python

   from src.core.utils.logging import configure_structlog

   # Development (colored console)
   configure_structlog(
       log_level="DEBUG",
       format="console",
       enable_colors=True
   )

   # Production (JSON logs)
   configure_structlog(
       log_level="INFO",
       format="json"
   )

Next Steps
----------

* Read the :doc:`guides/client` for detailed client configuration
* Learn about :doc:`guides/builders` for fluent request building
* Explore :doc:`guides/query_dsl` for complex searches
* Check :doc:`examples/basic_usage` for more examples
* See :doc:`api/client` for full API reference
