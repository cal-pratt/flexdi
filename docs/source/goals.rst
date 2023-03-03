Goals
-----

- | **Minimal Setup**
  | Minimize boilderplate by leveraging type annotations to resolve
    arguments. Allow user code to remain generic and reusable.

- | **Inject Any Callable**
  | Provide any typed callable as an input to be invoked.
    Support sync and async callables.

- | **Resource Management**
  | Define dependencies as context managers and have
    their startup and shutdown logic invoked in a reliable order.
    Support sync and async context managers.

- | **Scoped Dependencies**
  | Clearly define dependency lifetimes.
    Use ``"application"`` scoped dependencies to provide singleton like objects.
    Use ``"request"`` scoped dependencies to allow short-term isolated usage.
