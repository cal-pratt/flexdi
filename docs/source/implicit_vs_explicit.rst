Implicit Bindings
=================

To ensure that developers can reason about their code, all bindings in ``flexdi``
must be explicitly bound. This ensures that we do not create bindings for items
where it is unclear about which dependencies will actually be used.

Errors on implicit bindings
---------------------------

Going back to our previous asynchronous example, lets say that we want to move
the logic of our main method into a helper class called ``QueryService``.


.. include:: ../../examples/implicit_vs_explicit/service.py
   :code: python

When rewriting the main module we might be tempted to write the following:

.. include:: ../../examples/implicit_vs_explicit/main_failing.py
   :code: python

Fixing the issue by adding explicit bindings
--------------------------------------------

As noted in the comment above the main method, the graph refused to
resolve the main method because it was not explicitly bound to the graph.
To overcome this challenge we need to bind it to the graph.

.. include:: ../../examples/implicit_vs_explicit/main_explicit.py
   :code: python

Great, the example works! But this seems kind of tedious to do if one has
many dependencies that all need to be bound...


Reducing boilerplate with ``@implicitbinding``
----------------------------------------------

We can bind classes with ``@implicitbinding`` to avoid needing to wire up many 
in the main module of your application. This is perfect for classes that have
easily understandable dependencies.

The ``@implicitbinding`` decorator marks a class with a special attribute that
tells ``flexdi`` that the intent of this class is to be injected and that it is
okay to bind it to the graph, even if it was not explicitly referenced.

The modification to our ``QueryService`` is simple:

.. include:: ../../examples/implicit_vs_explicit/service_implicit.py
   :code: python

Now we can write the main module as we had initially expected:

.. include:: ../../examples/implicit_vs_explicit/main_implicit.py
   :code: python