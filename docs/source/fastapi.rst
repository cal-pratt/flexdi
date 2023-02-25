FastAPI Integration (Experimental)
==================================

FastAPI has a great dependency system, but one of the key features it lacks is
the ability to create singleton scoped dependencies. With ``flexdi`` you can 
create singleton scoped dependencies using the ``FastAPIGraph`` class.

``FastAPIGraph`` is an extension of the normal ``FlexGraph`` with the nessisary
logic to hook itself into FastAPI's startup and shutdown logic. Upon getting a
request, the ``FlexGraph`` will be chained, to allow creating request scoped
dependencies like normal, however, it can inherit any ``eager`` scoped
dependencies which are created at server startup time.

To opt into using a ``FlexGraph`` proided dependency, you can define the default
value of your argument to ``FlexDepends`` instead of the normal ``Depends`` that
is provided by FastAPI. The argument to ``FlexDepends`` is the class which you
want to be injected as the value, which will follow the same binding rules as a
normal ``flexdi`` application.


.. include:: ../../examples/fastapi_graph.py
   :code: python

.. note::

    Sub-dependencies of ``flexdi`` injected arguments do not have access to the 
    request context or other FastAPI specific dependencies, such as bodies, query
    params, headers, etc. They only have access to dependencies registed in the 
    ``FlexGraph`` bindings.

.. warning::

    Flex dependencies will all be created on the main server thread, meaning
    dependencies with expensive startup costs will slow down your server.
