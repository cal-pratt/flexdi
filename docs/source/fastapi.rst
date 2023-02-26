FastAPI Integration
===================

FastAPI has a great dependency system, but one of the key features it lacks is
the ability to create singleton scoped dependencies which are not bound to the
globals of a module. With ``flexdi`` you can create ``eager`` or singleton scoped
dependencies using the ``FastAPIGraph`` class.

``FastAPIGraph`` is an extension of the normal ``FlexGraph`` with the nessisary
logic to hook itself into FastAPI's startup and shutdown logic. Upon getting a
request, the ``FlexGraph`` will be chained to allow creating dependencies that
have the same lifetime rules as the request, but, it can inherit ``eager`` 
scoped dependencies which are created at server startup time.

To use a ``FlexGraph`` proided dependency within a FastAPI dependency or route,
you can define the default value of your argument as a ``FlexDepends`` instead of 
the normal ``fastapi.Depends`` instance. The argument to ``FlexDepends`` is the 
class which you want to be injected as the value.


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
