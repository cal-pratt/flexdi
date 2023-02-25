Goals
-----

- | **Minimal Setup**
  | ``flexdi`` minimizes setup by leveraging type annotations to perform
    injection, allowing user code to remain generic and reusable.
    The avoids library lock-in which can be prevalent in other DI systems.

- | **Inject Any Callable**
  | In ``flexdi``, you can provide any typed callable as an input to be invoked.
    This avoids having to make class definitions purely for injection to work.

- | **Resource Management**
  | Dependencies in ``flexdi`` can be defined as context managers and will have
    their startup and shutdown logic invoked in a reliable order.

- | **Asyncio Support**
  | ``flexdi`` supports calling both sync and async callables, and allows
    defining dependencies as sync or async context managers.
