Scopes
======

Scopes are used to help further manage the lifetime of dependencies in your
applications. 

.. note::

   Scopes are useful for systems like webservers or worker queues, where certain 
   objects have different lifetime rules. For simple command line applications, 
   these concepts can be ignored.

When setting bindings, there is an option to set the scope as either ``application`` 
or ``request`` scoped. By default, dependencies are set to ``request`` scoped. 

* | **Application Scope**: 
  | Dependencies are created once per application and reused for all requests.

* | **Request Scope**: 
  | Dependencies are created newly for each request that is made. 
  | Within a single request, objects will still be reused.

When resolving objects with the graph, both scopes will always exist.
Scopes are constructed for you if not manually created.
For example, the following:

.. literalinclude:: ../../examples/resolution.py
   :start-after: [scope_equivalency_simple: Start]
   :end-before: [scope_equivalency_simple: End]

Is equivalent to:

.. literalinclude:: ../../examples/resolution.py
   :start-after: [scope_equivalency_verbose: Start]
   :end-before: [scope_equivalency_verbose: End]


Example Setup
-------------

We'll start by making some basic classes that
we can bind to the graph in various ways:

.. literalinclude:: ../../examples/resolution.py
   :start-after: [Class Definitions: Start]
   :end-before: [Class Definitions: End]

With providers:

.. literalinclude:: ../../examples/resolution.py
   :start-after: [Provider Definitions: Start]
   :end-before: [Provider Definitions: End]

Using the graph directly
------------------------

We can use the ``FlexGraph`` directly without the entrypoint directive.
The graph supports invoking any callable which has dependencies registered
by the graph. When the graph is called directly, it does not persist any 
objects between invocations.

.. literalinclude:: ../../examples/resolution.py
   :start-after: [multiple_resolves: Start]
   :end-before: [multiple_resolves: End]

.. code-block:: text

   Example Start
   Starting Foo
   Ending Foo
   Starting Foo
   Ending Foo
   Foo1 is Foo2: False
   Example End

We can see that ``create_foo`` is called twice, and that foo is shut down
as soon as we get the result back. This is because each scope is newly created
and destroyed to processes each request. 

If we want to re-use results throughout multiple calls, we need to use scopes!

Request Scope
-------------

In our previous example, if we want ``create_foo`` to be called only once,
then we could do the following:

.. literalinclude:: ../../examples/resolution.py
   :start-after: [request_scoped_resolve: Start]
   :end-before: [request_scoped_resolve: End]

.. code-block:: text

   Before App Scope
   In App Scope
   Before Req Scope
   In Req Scope
   Starting Foo
   Foo1 is Foo2: True
   Ending Foo
   After Req Scope
   After App Scope

Because we re-used the request scope for multiple calls, we re-used the instance. 
You'll also notice that the shutdown of the resource happens only after we close the
request scope.

Application Scope
-----------------

We could also choose to make ``create_foo`` set as ``application`` scoped:

.. literalinclude:: ../../examples/resolution.py
   :start-after: [application_scoped_resolve: Start]
   :end-before: [application_scoped_resolve: End]

.. code-block:: text

   Before App Scope
   In App Scope
   Starting Foo
   Foo1 is Foo2: True
   Ending Foo
   After App Scope

Similar to last time, because the application scope was re-used, we re-used the instance. 
However, this time the shutdown of the resource happens only after we close the application 
scope.

Eager Dependencies
------------------

By default, dependencies are created lazily when requested for the first time.
If you want a value to be created as soon as the scope is opened, then you can
set the dependency as eager.

The following example illustrates how eager dependencies interact with the
different scopes:


.. literalinclude:: ../../examples/resolution.py
   :start-after: [eager_dependencies: Start]
   :end-before: [eager_dependencies: End]

.. code-block:: text

   Before App Scope
   Starting Foo
   In App Scope
   Before Req Scope
   Starting Bar
   In Req Scope
   Ending Bar
   After Req Scope
   Ending Foo
   After App Scope

Even though we didn't specifically call ``create_foo`` or ``create_bar``,
they were opened when entering the scope they were associated with.
We also notice that they are closed only after their associated scope has
also been closed.
