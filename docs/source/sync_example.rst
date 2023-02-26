Intro Example
-------------

When defining a ``flexdi`` application we start by creating a ``FlexGraph`` instance.
We will use the graph to inform ``flexdi`` how to resolve dependencies in our callables.

This examples shows a number of ways that dependencies can be defined, and also introduces
the ``@graph.entrypoint`` wrapper, which can be used to easily create main methods for your
applications.

.. include:: ../../examples/sqla_sync.py
   :code: python
