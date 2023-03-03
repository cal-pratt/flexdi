Overview
========

``flexdi`` offers the ``FlexGraph``, used to manage dependencies and invoke callables.

When determining dependencies for a callable, ``flexdi`` will examine the type
annotations of the arguments, and populate the graph with dependencies which can
satisfy the callable. A callable can be anything from a class (as seen with the
type annotations), to functions, class methods, generators, etc.

For complex types, ``flexdi`` allows binding helper functions that can map a
type definition to an instance. These bindings can themselves be injected
with dependencies. Bindings can also be defined as generators which allows
supplying custom teardown logic for dependencies.
