Entrypoints
-----------

The ``entrypoint`` decorator on the graph is a helper tool to construct
an async function which will open the graph and invoke a callable, and a
no-argument synchronous method which will invoke the async function.

For example, the following entrypoint:

.. literalinclude:: ../../examples/entrypoints.py
   :start-after: [entrypoint1: Start]
   :end-before: [entrypoint1: End]

Is roughly equivalent to:

.. literalinclude:: ../../examples/entrypoints.py
   :start-after: [entrypoint2: Start]
   :end-before: [entrypoint2: End]
