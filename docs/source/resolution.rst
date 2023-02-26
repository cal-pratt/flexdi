Resolving Objects
=================

For these examples, we'll start by making some basic classes that
we will bind to the graph in various ways.

.. literalinclude:: ../../examples/resolution.py
   :start-after: [Class Definitions: Start]
   :end-before: [Class Definitions: End]

To go along with these classes we will make a set of providers to
construct them.

.. literalinclude:: ../../examples/resolution.py
   :start-after: [Provider Definitions: Start]
   :end-before: [Provider Definitions: End]

Simple Resolution
-----------------

If we want to use the graph directly without the entrypoint directive,
then we can use the ``FlexGraph`` as an async context manager. When opened,
the graph supports invoking any callable which has dependencies registered
by the graph.


.. literalinclude:: ../../examples/resolution.py
   :start-after: [example1: Start]
   :end-before: [example1: End]

.. code-block:: text
   
   Starting Foo
   Ending Foo


Graph Reuse
-----------

The graph will attempt to only make one instance per binding requested.
For a single run of the graph, callables and classes will be re-used
when requested to avoid creating duplicate objects.

This is to facilitate creating dependencies on things like database 
connections or objects with expensive startup, that you would really
only want one of per application.


.. literalinclude:: ../../examples/resolution.py
   :start-after: [example2: Start]
   :end-before: [example2: End]

.. code-block:: text

   Starting Foo
   Foo1 is Foo2: True
   Ending Foo

We can see that ``create_foo`` is only called once, and that foo is
not closed until the ``async with`` statement completes, as it prints
after the line ``Foo1 is Foo2: True`` which was executed in the with block.

Eager Bindings
--------------

When setting bindings explicitly, there an option to making the binding
``eager``. A dependency set as eager will be constructed as soon as the
graph is opened. The default value for eager is set to ``False``.

*This concept will become more important when we start looking at graph chaining*.

.. literalinclude:: ../../examples/resolution.py
   :start-after: [example3: Start]
   :end-before: [example3: End]

.. code-block:: text

   Starting Foo
   Inside the with block
   Ending Foo

In this example, ``create_foo`` was set as eager, but ``create_bar`` was not.
This means that we will only prepopulate the graph instances with ``Foo``,
and wait until ``Bar`` is requested for the first time before constructing that.


Graph Chaining
--------------

Graph chaining is the way that ``flexdi`` supports creating scopes for object
resolution within applications. If a graph has been opened it is allowed to
be chained.

When a graph is chained, a new graph will be created which inherits a copy of all
of the graph state found in the parent graph. Any objects created by the parent
graph will persist in the child, but these resources will not be closed until the 
parent exits.

.. literalinclude:: ../../examples/resolution.py
   :start-after: [example4: Start]
   :end-before: [example4: End]

.. code-block:: text

   Starting Foo
   Parent Block
   Child Block
   Starting Bar
   Ending Bar
   Child Block
   Starting Bar
   Ending Bar
   Ending Foo

Using this pattern it is possible to create scopes for a long running application
that has different lifetime rules for certain dependencies. When a new request is
made to the application, a new graph may be constructed by chaining the main
application graph and using it to fulfil the request.
