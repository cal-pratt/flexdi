Implicit Bindings
=================

To ensure that developers can reason about their code, all bindings in ``flexdi``
must be explicitly bound. This ensures that we do not create bindings for items
where it is unclear about how dependencies are constructed.

Errors on implicit bindings
---------------------------

Going back to our previous Async Example, lets say that we want to move
the logic of our main method into a helper class called ``QueryService``.


.. include:: ../../examples/implicit_vs_explicit/service.py
   :code: python

When rewriting the main module we might be tempted to write the following:

.. include:: ../../examples/implicit_vs_explicit/main_failing.py
   :code: python

This fails with:

.. warning::

   .. code-block::

      flexdi.errors.ImplicitBindingError:
         Requested a binding for <class 'service.QueryService'>
         that was not explicitly marked for binding.


Fixing the issue by adding explicit bindings
--------------------------------------------

As noted in the error, the graph refused to resolve the function because 
a dependency was not explicitly bound to the graph.
To overcome this, we can explicitly to bind it to the graph.

.. literalinclude:: ../../examples/implicit_vs_explicit/main_explicit.py
   :emphasize-lines: 11-12

This example works, but this may become tedious if there are many dependencies 
to bind. We can overcome this hurlde with ``@implicitbinding``.


``@implicitbinding``
--------------------

Classes marked with ``@implicitbinding`` avoid the need for explicit wiring 
in the main module of your application. This is perfect for classes that have
easily understandable dependencies.

The ``@implicitbinding`` decorator marks a class with a special attribute that
tells ``flexdi`` that it is okay to inject this class even if it was not 
explicitly bound in the graph.

The modification to our ``QueryService`` is simple:

.. literalinclude:: ../../examples/implicit_vs_explicit/service_implicit.py
   :emphasize-lines: 6

Now we can write the main module as we had initially expected:

.. include:: ../../examples/implicit_vs_explicit/main_implicit.py
   :code: python
