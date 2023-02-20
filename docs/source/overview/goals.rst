Goals
-----

- | **Minimal Setup**
  | Some DI systems require that you conform to a particular style of class
    definition, a naming convention to arguments, placing wrappers around class
    or method definitions, or providing complex default arguments which are tied
    to the DI system.
    ``flexdi`` mainly uses type annotations to perform injection, which avoids
    a common problem of library lock-in where frameworks force you to design
    components using their highly specialized constructs.

- | **Inject Any Callable**
  | Basic Python DI tools only allow classes to be used for injection, which can
    be quite limiting. In ``flexdi``, you can provide any typed callable as an
    input to be invoked.
    This avoids having to make class definitions purely for injection to work.

- | **Lifetime Management**
  | When creating dependencies for your callable, you often have resources that
    need to be properly torn down when your work is done. Providers for types in
    ``flexdi`` can be initialized using context managers that will have their
    shutdown logic invoked when you're done your work.

- | **Asyncio Support**
  | ``flexdi`` allows calling both sync and async methods directly, and provides
    both a sync and async interface to its main invocation method. Similarly,
    dependency providers may be defined as async methods, or be provided as
    async context managers.
