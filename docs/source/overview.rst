``flexdi`` offers the ``FlexGraph``, used to manage dependencies and invoke callables.
The graph is a representation of what dependencies exist, and what providers can be
used to fulfil them.

When determining dependencies for a callable, ``flexdi`` will examine the type
annotations of the arguments to populate the graph with dependencies that can
satisfy the callable. A callable can be anything from a class, to functions, 
class methods, generators, etc.

``flexdi`` allows *binding* helper functions to the graph as a providers of types,
determined by their return annotations.
Bindings can themselves be injected with dependencies,
determined by their parameter annotations.
A Binding can be a simple function or a generator with custom teardown logic.